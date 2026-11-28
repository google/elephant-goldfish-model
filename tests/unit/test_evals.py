# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Offline unit tests for reproducible eval fixtures, manifest, and scorer."""

import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import eval_runner  # noqa: E402


def test_offline_replay_passes_and_excludes_showcase() -> None:
  cases_data = yaml.safe_load(
      (ROOT / "evals/fixtures/cases.yaml").read_text(encoding="utf-8")
  )
  outputs_data = yaml.safe_load(
      (ROOT / "evals/fixtures/replay/review_outputs.yaml").read_text(
          encoding="utf-8"
      )
  )
  result = eval_runner.score_review_outputs(cases_data, outputs_data)

  assert result.passed is True
  assert result.total_cases == 3
  assert result.decision_correct == 3
  assert result.real_blockers_found == 1
  assert result.expected_blockers_total == 1
  assert result.unsupported_blockers_on_sound_plans == 0
  assert result.owner_questions_matched == 1
  assert result.expected_owner_questions_total == 1
  assert result.stage_placement_correct == 3
  assert result.stage_placement_total == 3
  assert result.evidence_accuracy_correct == 3
  assert result.evidence_accuracy_total == 3
  assert result.excluded_showcase_cases == ["showcase-public-before-after"]
  assert result.harness_isolation["status"] == "passed"
  assert result.surface == "native_claude_code"


def test_malformed_output_produces_actionable_parse_failure() -> None:
  cases_data = yaml.safe_load(
      (ROOT / "evals/fixtures/cases.yaml").read_text(encoding="utf-8")
  )
  outputs_data = yaml.safe_load(
      (ROOT / "evals/fixtures/replay/review_outputs.yaml").read_text(
          encoding="utf-8"
      )
  )
  outputs_data["outputs"][0]["decision"] = "maybe"

  result = eval_runner.score_review_outputs(cases_data, outputs_data)
  assert result.passed is False
  assert len(result.parse_failures) == 1
  assert "public-api-preserved" in result.parse_failures[0]
  assert "invalid decision" in result.parse_failures[0]


def test_unsupported_blocker_on_sound_or_uncertainty_plan_fails() -> None:
  cases_data = yaml.safe_load(
      (ROOT / "evals/fixtures/cases.yaml").read_text(encoding="utf-8")
  )
  outputs_data = yaml.safe_load(
      (ROOT / "evals/fixtures/replay/review_outputs.yaml").read_text(
          encoding="utf-8"
      )
  )
  outputs_data["outputs"][2]["findings"] = [
      {"id": "hallucinated-blocker", "severity": "blocker"}
  ]

  result = eval_runner.score_review_outputs(cases_data, outputs_data)
  assert result.passed is False
  assert result.unsupported_blockers_on_sound_plans == 1
  assert any("hallucinated-blocker" in err for err in result.case_errors)


def test_factuality_report_breaks_down_clean_and_flawed_recall_by_dataset() -> None:
  factuality_data = yaml.safe_load(
      (ROOT / "evals/fixtures/replay/factuality_outputs.yaml").read_text(
          encoding="utf-8"
      )
  )
  report = eval_runner.score_factuality_outputs(factuality_data)
  by_ds = {entry["dataset"]: entry for entry in report["datasets"]}

  assert by_ds["ragtruth"]["clean_correct"] == 2
  assert by_ds["ragtruth"]["clean_total"] == 3
  assert by_ds["ragtruth"]["flawed_correct"] == 2
  assert by_ds["ragtruth"]["flawed_total"] == 3
  assert by_ds["ragtruth"]["parse_errors"] == 0

  assert by_ds["summedits"]["clean_correct"] == 2
  assert by_ds["summedits"]["clean_total"] == 2
  assert by_ds["summedits"]["flawed_correct"] == 2
  assert by_ds["summedits"]["flawed_total"] == 3
  assert by_ds["summedits"]["parse_errors"] == 1
  assert report["totals"]["parse_errors"] == 1


def test_manifest_validation_enforces_out_of_git_and_required_fields() -> None:
  manifest_data = yaml.safe_load(
      (ROOT / "evals/manifests/external_cases.yaml").read_text(encoding="utf-8")
  )
  datasets = eval_runner.validate_manifest(manifest_data)
  assert {d["id"] for d in datasets} == {
      "ragtruth", "summedits", "heldout_egm_plans", "trek_trips",
  }

  manifest_data["datasets"][0]["keep_out_of_git"] = False
  with pytest.raises(eval_runner.EvalFormatError, match="keep_out_of_git"):
    eval_runner.validate_manifest(manifest_data)

  manifest_data["datasets"][0]["keep_out_of_git"] = True
  manifest_data["datasets"][0]["checksum"] = "sha256:" + "0" * 64
  with pytest.raises(eval_runner.EvalFormatError, match="placeholder"):
    eval_runner.validate_manifest(manifest_data)


def test_cli_replay_and_compare_commands(tmp_path: Path) -> None:
  completed = subprocess.run(
      [
          sys.executable,
          str(ROOT / "scripts/eval_runner.py"),
          "replay",
          "--format",
          "json",
      ],
      cwd=ROOT,
      capture_output=True,
      text=True,
      check=False,
  )
  assert completed.returncode == 0, completed.stderr
  payload = json.loads(completed.stdout)
  assert payload["review"]["passed"] is True
  assert payload["review"]["advisory"] is False

  live_outputs = yaml.safe_load(
      (ROOT / "evals/fixtures/replay/review_outputs.yaml").read_text(
          encoding="utf-8"
      )
  )
  live_outputs["execution_mode"] = "live_advisory"
  live_outputs["surface"] = "managed_agents"
  live_path = tmp_path / "live.yaml"
  live_path.write_text(yaml.safe_dump(live_outputs), encoding="utf-8")

  compare = subprocess.run(
      [
          sys.executable,
          str(ROOT / "scripts/eval_runner.py"),
          "compare",
          "--cases",
          str(ROOT / "evals/fixtures/cases.yaml"),
          "--outputs",
          str(live_path),
          "--baseline-outputs",
          str(live_path),
          "--format",
          "json",
      ],
      cwd=ROOT,
      capture_output=True,
      text=True,
      check=False,
  )
  assert compare.returncode == 0, compare.stderr
  compare_payload = json.loads(compare.stdout)
  assert compare_payload["review"]["advisory"] is True
  assert compare_payload["review"]["surface"] == "managed_agents"
  assert "baseline" in compare_payload

  malformed_outputs = yaml.safe_load(
      (ROOT / "evals/fixtures/replay/review_outputs.yaml").read_text(
          encoding="utf-8"
      )
  )
  malformed_outputs["outputs"][0]["decision"] = "invalid_decision"
  bad_path = tmp_path / "bad.yaml"
  bad_path.write_text(yaml.safe_dump(malformed_outputs), encoding="utf-8")
  bad_compare = subprocess.run(
      [
          sys.executable,
          str(ROOT / "scripts/eval_runner.py"),
          "compare",
          "--cases",
          str(ROOT / "evals/fixtures/cases.yaml"),
          "--outputs",
          str(bad_path),
          "--format",
          "json",
      ],
      cwd=ROOT,
      capture_output=True,
      text=True,
      check=False,
  )
  assert bad_compare.returncode != 0
  bad_payload = json.loads(bad_compare.stdout)
  assert "invalid decision" in bad_payload["review"]["parse_failures"][0]
