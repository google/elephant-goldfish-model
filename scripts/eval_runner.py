# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Offline-capable reproducible evals scorer, manifest validator, and CLI."""

import argparse
from dataclasses import dataclass, field
import json
from pathlib import Path
import sys
from typing import Any

import yaml

VALID_DECISIONS = frozenset({"proceed", "hold", "uncertainty"})
VALID_FACTUALITY_LABELS = frozenset({"clean", "flawed"})
REQUIRED_MANIFEST_FIELDS = (
    "id",
    "name",
    "kind",
    "upstream_url",
    "revision",
    "checksum",
    "fetch_mode",
    "keep_out_of_git",
    "attribution",
    "redistribution_terms",
    "split_rules",
    "case_ids",
)


class EvalFormatError(ValueError):
  """Raised when an eval fixture, manifest, or output record is malformed."""


@dataclass
class ReviewScoreResult:
  """Structured review scoring result with separated stage/evidence/isolation."""

  dataset: str
  execution_mode: str
  prompt_version: str
  model_version: str
  harness: str
  surface: str
  case_ids: list[str]
  excluded_showcase_cases: list[str]
  total_cases: int = 0
  decision_correct: int = 0
  real_blockers_found: int = 0
  expected_blockers_total: int = 0
  unsupported_blockers_on_sound_plans: int = 0
  owner_questions_matched: int = 0
  expected_owner_questions_total: int = 0
  stage_placement_correct: int = 0
  stage_placement_total: int = 0
  evidence_accuracy_correct: int = 0
  evidence_accuracy_total: int = 0
  parse_failures: list[str] = field(default_factory=list)
  case_errors: list[str] = field(default_factory=list)
  harness_isolation: dict[str, Any] = field(default_factory=dict)

  @property
  def passed(self) -> bool:
    return (
        not self.parse_failures
        and not self.case_errors
        and self.decision_correct == self.total_cases
        and self.real_blockers_found == self.expected_blockers_total
        and self.unsupported_blockers_on_sound_plans == 0
        and self.owner_questions_matched == self.expected_owner_questions_total
    )

  def to_dict(self) -> dict[str, Any]:
    return {
        "dataset": self.dataset,
        "execution_mode": self.execution_mode,
        "advisory": self.execution_mode != "replay",
        "prompt_version": self.prompt_version,
        "model_version": self.model_version,
        "harness": self.harness,
        "surface": self.surface,
        "case_ids": self.case_ids,
        "excluded_showcase_cases": self.excluded_showcase_cases,
        "total_cases": self.total_cases,
        "decision_correct": self.decision_correct,
        "real_blockers_found": self.real_blockers_found,
        "expected_blockers_total": self.expected_blockers_total,
        "unsupported_blockers_on_sound_plans": (
            self.unsupported_blockers_on_sound_plans
        ),
        "owner_questions_matched": self.owner_questions_matched,
        "expected_owner_questions_total": self.expected_owner_questions_total,
        "stage_placement": {
            "correct": self.stage_placement_correct,
            "total": self.stage_placement_total,
        },
        "evidence_accuracy": {
            "correct": self.evidence_accuracy_correct,
            "total": self.evidence_accuracy_total,
        },
        "harness_isolation": self.harness_isolation,
        "parse_failures": self.parse_failures,
        "case_errors": self.case_errors,
        "passed": self.passed,
    }


def _load_yaml(path: Path) -> dict[str, Any]:
  if not path.is_file():
    raise EvalFormatError(f"File not found: {path}")
  try:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
  except yaml.YAMLError as exc:
    raise EvalFormatError(f"Invalid YAML in {path}: {exc}") from exc
  if not isinstance(data, dict):
    raise EvalFormatError(f"Expected top-level mapping in {path}")
  return data


def validate_cases(cases_data: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
  """Validate fixture cases and exclude showcase-only entries from scoring."""
  raw_cases = cases_data.get("cases")
  if not isinstance(raw_cases, list) or not raw_cases:
    raise EvalFormatError("Cases file must define a non-empty 'cases' list.")

  scored: list[dict[str, Any]] = []
  excluded_showcase: list[str] = []
  seen_ids: set[str] = set()

  for index, case in enumerate(raw_cases):
    if not isinstance(case, dict):
      raise EvalFormatError(f"Case at index {index} must be a mapping.")
    case_id = case.get("id")
    if not isinstance(case_id, str) or not case_id.strip():
      raise EvalFormatError(f"Case at index {index} is missing a string 'id'.")
    if case_id in seen_ids:
      raise EvalFormatError(f"Duplicate case id '{case_id}'.")
    seen_ids.add(case_id)

    decision = case.get("expected_decision")
    if decision not in VALID_DECISIONS:
      raise EvalFormatError(
          f"Case '{case_id}' has invalid expected_decision {decision!r}; "
          f"expected one of {sorted(VALID_DECISIONS)}."
      )
    if not isinstance(case.get("workflow"), str) or not case["workflow"].strip():
      raise EvalFormatError(f"Case '{case_id}' must record a 'workflow'.")

    if case.get("showcase", False):
      excluded_showcase.append(case_id)
      continue
    scored.append(case)

  if not scored:
    raise EvalFormatError("No non-showcase scored cases found.")
  return scored, excluded_showcase


def validate_manifest(manifest_data: dict[str, Any]) -> list[dict[str, Any]]:
  """Validate external dataset manifest fields and out-of-Git policy."""
  datasets = manifest_data.get("datasets")
  if not isinstance(datasets, list) or not datasets:
    raise EvalFormatError("Manifest must define a non-empty 'datasets' list.")

  for index, entry in enumerate(datasets):
    if not isinstance(entry, dict):
      raise EvalFormatError(f"Manifest dataset at index {index} must be a mapping.")
    ds_id = entry.get("id", f"<index {index}>")
    for field_name in REQUIRED_MANIFEST_FIELDS:
      if field_name not in entry:
        raise EvalFormatError(
            f"Manifest dataset '{ds_id}' is missing required field '{field_name}'."
        )
    if entry.get("keep_out_of_git") is not True:
      raise EvalFormatError(
          f"Manifest dataset '{ds_id}' must set keep_out_of_git: true."
      )
    checksum = entry.get("checksum")
    if checksum is not None:
      if not isinstance(checksum, str) or set(checksum.removeprefix("sha256:")) == {"0"}:
        raise EvalFormatError(
            f"Manifest dataset '{ds_id}' must use a verified checksum or null, "
            "never a placeholder."
        )
    case_ids = entry.get("case_ids")
    if not isinstance(case_ids, list) or not case_ids:
      raise EvalFormatError(
          f"Manifest dataset '{ds_id}' must list at least one pinned case_id."
      )
  return datasets


def _extract_finding_ids(findings: Any, case_id: str) -> list[str]:
  if not isinstance(findings, list):
    raise EvalFormatError(
        f"case_id={case_id}: 'findings' must be a list, got {type(findings).__name__}."
    )
  ids: list[str] = []
  for idx, item in enumerate(findings):
    if not isinstance(item, dict) or not isinstance(item.get("id"), str):
      raise EvalFormatError(
          f"case_id={case_id}: findings[{idx}] must be a mapping with string 'id'."
      )
    ids.append(item["id"])
  return ids


def _extract_question_ids(questions: Any, case_id: str) -> list[str]:
  if questions is None:
    return []
  if not isinstance(questions, list):
    raise EvalFormatError(
        f"case_id={case_id}: 'owner_questions' must be a list."
    )
  ids: list[str] = []
  for idx, item in enumerate(questions):
    if isinstance(item, dict) and isinstance(item.get("id"), str):
      ids.append(item["id"])
    elif isinstance(item, str):
      ids.append(item)
    else:
      raise EvalFormatError(
          f"case_id={case_id}: owner_questions[{idx}] must be a string or "
          "mapping with string 'id'."
      )
  return ids


def score_review_outputs(
    cases_data: dict[str, Any],
    outputs_data: dict[str, Any],
) -> ReviewScoreResult:
  """Score candidate review outputs against fixture expectations."""
  scored_cases, excluded_showcase = validate_cases(cases_data)

  raw_outputs = outputs_data.get("outputs")
  if not isinstance(raw_outputs, list):
    raise EvalFormatError(
        "Review outputs must contain a top-level 'outputs' list."
    )

  isolation = outputs_data.get("harness_isolation")
  if isolation is None:
    isolation = {
        "status": "not_run",
        "notes": "No harness isolation verification recorded.",
    }
  elif not isinstance(isolation, dict) or "status" not in isolation:
    raise EvalFormatError(
        "'harness_isolation' must be a mapping containing 'status'."
    )

  result = ReviewScoreResult(
      dataset=str(outputs_data.get("dataset") or cases_data.get("dataset") or "unknown"),
      execution_mode=str(outputs_data.get("execution_mode") or "live_advisory"),
      prompt_version=str(outputs_data.get("prompt_version") or "unspecified"),
      model_version=str(outputs_data.get("model_version") or "unspecified"),
      harness=str(outputs_data.get("harness") or "unspecified"),
      surface=str(outputs_data.get("surface") or "unspecified"),
      case_ids=[c["id"] for c in scored_cases],
      excluded_showcase_cases=excluded_showcase,
      total_cases=len(scored_cases),
      harness_isolation=isolation,
  )

  outputs_by_id: dict[str, dict[str, Any]] = {}
  for idx, record in enumerate(raw_outputs):
    if not isinstance(record, dict):
      result.parse_failures.append(
          f"outputs[{idx}]: expected mapping, got {type(record).__name__}."
      )
      continue
    case_id = record.get("case_id")
    if not isinstance(case_id, str) or not case_id.strip():
      result.parse_failures.append(
          f"outputs[{idx}]: missing required string 'case_id'."
      )
      continue
    if case_id in outputs_by_id:
      result.parse_failures.append(
          f"case_id={case_id}: duplicate output record."
      )
      continue
    outputs_by_id[case_id] = record

  for case in scored_cases:
    case_id = case["id"]
    expected_blockers = list(case.get("expected_blockers") or [])
    expected_questions = list(case.get("expected_owner_questions") or [])
    result.expected_blockers_total += len(expected_blockers)
    result.expected_owner_questions_total += len(expected_questions)

    expected_stage = case.get("expected_stage")
    expected_evidence = list(case.get("expected_evidence") or [])
    if expected_stage:
      result.stage_placement_total += 1
    if expected_evidence:
      result.evidence_accuracy_total += 1

    record = outputs_by_id.get(case_id)
    if record is None:
      result.parse_failures.append(
          f"case_id={case_id}: missing output record for scored fixture."
      )
      continue

    decision = record.get("decision")
    if decision not in VALID_DECISIONS:
      result.parse_failures.append(
          f"case_id={case_id}: invalid decision {decision!r}; "
          f"expected one of {sorted(VALID_DECISIONS)}."
      )
      continue

    try:
      finding_ids = _extract_finding_ids(record.get("findings"), case_id)
      question_ids = _extract_question_ids(record.get("owner_questions"), case_id)
    except EvalFormatError as exc:
      result.parse_failures.append(str(exc))
      continue

    if decision == case["expected_decision"]:
      result.decision_correct += 1
    else:
      result.case_errors.append(
          f"case_id={case_id}: expected decision '{case['expected_decision']}', "
          f"got '{decision}'."
      )

    matched_blockers = sum(1 for b in expected_blockers if b in finding_ids)
    result.real_blockers_found += matched_blockers
    if matched_blockers < len(expected_blockers):
      missing = [b for b in expected_blockers if b not in finding_ids]
      result.case_errors.append(
          f"case_id={case_id}: missed expected blockers {missing}."
      )

    if not case.get("allow_unsupported_blockers", False):
      unexpected_blockers = [
          f_id for f_id in finding_ids if f_id not in expected_blockers
      ]
      if unexpected_blockers:
        result.unsupported_blockers_on_sound_plans += len(unexpected_blockers)
        result.case_errors.append(
            f"case_id={case_id}: raised unsupported blockers {unexpected_blockers}."
        )

    matched_questions = sum(1 for q in expected_questions if q in question_ids)
    result.owner_questions_matched += matched_questions
    if matched_questions < len(expected_questions):
      missing_q = [q for q in expected_questions if q not in question_ids]
      result.case_errors.append(
          f"case_id={case_id}: missed expected owner questions {missing_q}."
      )

    if expected_stage and record.get("stage") == expected_stage:
      result.stage_placement_correct += 1

    if expected_evidence:
      actual_evidence = record.get("evidence") or []
      if isinstance(actual_evidence, list):
        actual_text = " ".join(str(item) for item in actual_evidence)
        if all(req in actual_text for req in expected_evidence):
          result.evidence_accuracy_correct += 1

  return result


def score_factuality_outputs(
    outputs_data: dict[str, Any],
) -> dict[str, Any]:
  """Compute clean and flawed recall by dataset with sample counts."""
  datasets = outputs_data.get("datasets")
  if not isinstance(datasets, list) or not datasets:
    raise EvalFormatError(
        "Factuality outputs must contain a non-empty 'datasets' list."
    )

  per_dataset: list[dict[str, Any]] = []
  totals = {
      "clean_correct": 0,
      "clean_total": 0,
      "flawed_correct": 0,
      "flawed_total": 0,
      "parse_errors": 0,
  }

  for ds in datasets:
    if not isinstance(ds, dict) or not isinstance(ds.get("dataset"), str):
      raise EvalFormatError("Each factuality dataset entry must have string 'dataset'.")
    ds_name = ds["dataset"]
    records = ds.get("records")
    if not isinstance(records, list):
      raise EvalFormatError(f"Dataset '{ds_name}' must contain a 'records' list.")

    clean_correct = 0
    clean_total = 0
    flawed_correct = 0
    flawed_total = 0
    parse_error_details: list[str] = []

    for idx, rec in enumerate(records):
      if not isinstance(rec, dict):
        parse_error_details.append(f"{ds_name}[{idx}]: expected mapping.")
        continue
      rec_id = rec.get("id", f"{ds_name}[{idx}]")
      expected = rec.get("expected")
      if expected not in VALID_FACTUALITY_LABELS:
        parse_error_details.append(
            f"{rec_id}: invalid expected label {expected!r}."
        )
        continue
      if expected == "clean":
        clean_total += 1
      else:
        flawed_total += 1

      if rec.get("parse_error") or rec.get("predicted") is None:
        reason = rec.get("parse_error") or "predicted is null"
        parse_error_details.append(f"{rec_id}: {reason}")
        continue

      predicted = rec.get("predicted")
      if predicted not in VALID_FACTUALITY_LABELS:
        parse_error_details.append(
            f"{rec_id}: invalid predicted label {predicted!r}."
        )
        continue

      if expected == "clean" and predicted == "clean":
        clean_correct += 1
      elif expected == "flawed" and predicted == "flawed":
        flawed_correct += 1

    clean_recall = (clean_correct / clean_total) if clean_total else 0.0
    flawed_recall = (flawed_correct / flawed_total) if flawed_total else 0.0

    per_dataset.append({
        "dataset": ds_name,
        "clean_correct": clean_correct,
        "clean_total": clean_total,
        "clean_recall": round(clean_recall, 4),
        "flawed_correct": flawed_correct,
        "flawed_total": flawed_total,
        "flawed_recall": round(flawed_recall, 4),
        "parse_errors": len(parse_error_details),
        "parse_error_details": parse_error_details,
    })

    totals["clean_correct"] += clean_correct
    totals["clean_total"] += clean_total
    totals["flawed_correct"] += flawed_correct
    totals["flawed_total"] += flawed_total
    totals["parse_errors"] += len(parse_error_details)

  return {
      "execution_mode": str(outputs_data.get("execution_mode") or "replay"),
      "prompt_version": str(outputs_data.get("prompt_version") or "unspecified"),
      "model_version": str(outputs_data.get("model_version") or "unspecified"),
      "datasets": per_dataset,
      "totals": totals,
  }


def format_markdown_report(
    review_result: ReviewScoreResult,
    factuality_result: dict[str, Any] | None = None,
    baseline_result: ReviewScoreResult | None = None,
) -> str:
  """Render a human-readable Markdown summary for CI logs or maintainers."""
  mode_note = (
      "Replay check (verifies parser and scorer; does not measure live model behavior)"
      if review_result.execution_mode == "replay"
      else "Live advisory run (measures review behavior; advisory only)"
  )
  lines = [
      "## EGM Eval Report",
      "",
      f"- **Mode**: {mode_note}",
      f"- **Dataset**: `{review_result.dataset}` ({len(review_result.case_ids)} scored cases; excluded showcase: {len(review_result.excluded_showcase_cases)})",
      f"- **Cases**: {', '.join(review_result.case_ids)}",
      f"- **Prompt / Model**: `{review_result.prompt_version}` / `{review_result.model_version}`",
      f"- **Harness / Surface**: `{review_result.harness}` / `{review_result.surface}`",
      f"- **Harness Isolation**: `{review_result.harness_isolation.get('status', 'not_run')}` — {review_result.harness_isolation.get('notes', '')}",
      "",
      "### Review Scoring",
      "",
      "| Metric | Value |",
      "| :--- | :--- |",
      f"| Decisions correct | {review_result.decision_correct}/{review_result.total_cases} |",
      f"| Real blockers found | {review_result.real_blockers_found}/{review_result.expected_blockers_total} |",
      f"| Unsupported blockers on sound/non-blocker plans | {review_result.unsupported_blockers_on_sound_plans} |",
      f"| Owner questions matched | {review_result.owner_questions_matched}/{review_result.expected_owner_questions_total} |",
      f"| Parse failures | {len(review_result.parse_failures)} |",
      f"| Stage placement (separate) | {review_result.stage_placement_correct}/{review_result.stage_placement_total} |",
      f"| Evidence accuracy (separate) | {review_result.evidence_accuracy_correct}/{review_result.evidence_accuracy_total} |",
  ]

  if baseline_result is not None:
    lines.extend([
        "",
        "### Plain-Review Baseline Comparison (Advisory)",
        "",
        f"- **Baseline Model / Prompt**: `{baseline_result.model_version}` / `{baseline_result.prompt_version}`",
        f"- **Baseline Decisions**: {baseline_result.decision_correct}/{baseline_result.total_cases}",
        f"- **Baseline Real Blockers**: {baseline_result.real_blockers_found}/{baseline_result.expected_blockers_total}",
        f"- **Baseline Unsupported Blockers**: {baseline_result.unsupported_blockers_on_sound_plans}",
    ])

  if factuality_result is not None:
    lines.extend([
        "",
        "### Factuality Report by Dataset",
        "",
        "| Dataset | Clean Recall (Count) | Flawed Recall (Count) | Parse Errors |",
        "| :--- | :--- | :--- | :--- |",
    ])
    for ds in factuality_result["datasets"]:
      clean_pct = f"{ds['clean_recall'] * 100:.1f}%"
      flawed_pct = f"{ds['flawed_recall'] * 100:.1f}%"
      lines.append(
          f"| `{ds['dataset']}` | {clean_pct} ({ds['clean_correct']}/{ds['clean_total']}) "
          f"| {flawed_pct} ({ds['flawed_correct']}/{ds['flawed_total']}) "
          f"| {ds['parse_errors']} |"
      )

  return "\n".join(lines)


def _default_repo_root() -> Path:
  return Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
      description="Run offline replay checks, manifest validation, or live comparisons."
  )
  subparsers = parser.add_subparsers(dest="command", required=True)

  replay_p = subparsers.add_parser(
      "replay", help="Run offline fixture, manifest, parser, and scorer checks."
  )
  replay_p.add_argument("--root", type=Path, default=_default_repo_root())
  replay_p.add_argument("--format", choices=("markdown", "json"), default="markdown")

  compare_p = subparsers.add_parser(
      "compare", help="Score a fresh candidate run (and optional plain-review baseline)."
  )
  compare_p.add_argument("--cases", type=Path, required=True)
  compare_p.add_argument("--outputs", type=Path, required=True)
  compare_p.add_argument("--baseline-outputs", type=Path, default=None)
  compare_p.add_argument("--format", choices=("markdown", "json"), default="markdown")

  manifest_p = subparsers.add_parser(
      "manifest", help="Validate external dataset manifest without downloading corpora."
  )
  manifest_p.add_argument("--root", type=Path, default=_default_repo_root())
  manifest_p.add_argument("--format", choices=("markdown", "json"), default="json")

  args = parser.parse_args(argv)

  try:
    if args.command == "replay":
      root = args.root.resolve()
      manifest_data = _load_yaml(root / "evals/manifests/external_cases.yaml")
      validate_manifest(manifest_data)
      cases_data = _load_yaml(root / "evals/fixtures/cases.yaml")
      review_outputs = _load_yaml(root / "evals/fixtures/replay/review_outputs.yaml")
      factuality_outputs = _load_yaml(
          root / "evals/fixtures/replay/factuality_outputs.yaml"
      )
      review_result = score_review_outputs(cases_data, review_outputs)
      factuality_result = score_factuality_outputs(factuality_outputs)
      if args.format == "json":
        print(json.dumps({
            "review": review_result.to_dict(),
            "factuality": factuality_result,
        }, indent=2))
      else:
        print(format_markdown_report(review_result, factuality_result))
      return 0 if review_result.passed else 1

    if args.command == "compare":
      cases_data = _load_yaml(args.cases)
      outputs_data = _load_yaml(args.outputs)
      review_result = score_review_outputs(cases_data, outputs_data)
      baseline_result = None
      if args.baseline_outputs is not None:
        baseline_data = _load_yaml(args.baseline_outputs)
        baseline_result = score_review_outputs(cases_data, baseline_data)
      if args.format == "json":
        payload: dict[str, Any] = {"review": review_result.to_dict()}
        if baseline_result is not None:
          payload["baseline"] = baseline_result.to_dict()
        print(json.dumps(payload, indent=2))
      else:
        print(format_markdown_report(review_result, baseline_result=baseline_result))
      return 0 if not review_result.parse_failures else 1

    if args.command == "manifest":
      root = args.root.resolve()
      manifest_data = _load_yaml(root / "evals/manifests/external_cases.yaml")
      datasets = validate_manifest(manifest_data)
      if args.format == "json":
        print(json.dumps({"datasets": datasets}, indent=2))
      else:
        for ds in datasets:
          print(f"- {ds['id']} ({ds['kind']}): {ds['revision']} [{ds['fetch_mode']}]")
      return 0

  except EvalFormatError as exc:
    print(f"ERROR: {exc}", file=sys.stderr)
    return 1

  return 0


if __name__ == "__main__":
  sys.exit(main())
