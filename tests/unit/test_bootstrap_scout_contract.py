# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Pin the egm-bootstrap scout failure contract.

The behavior itself is model-driven and covered by the
`bootstrap_scout_failure_is_loud` and `bootstrap_swarm_incomplete_report`
scenarios. These checks make sure a future edit to SKILL.md (for example a trim
to stay under the load limit), the worker return schema, or the design doc
cannot drop one of the clauses that turn a lost scout chunk into a visible,
named gap with a correct rerun command.
"""

import json
from pathlib import Path
import re

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills/egm-bootstrap/SKILL.md"
SCHEMA = ROOT / "skills/egm-bootstrap/references/worker-return.schema.json"
SCENARIOS = ROOT / "skills/egm-bootstrap/test_scenarios.yaml"
DESIGN = ROOT / "docs/designs/bootstrap.md"


def skill_text() -> str:
  return " ".join(SKILL.read_text(encoding="utf-8").split())


@pytest.mark.parametrize(
    ("clause", "pattern"),
    [
        # Scouts self-report what they read, so the worker can compare it with
        # the assignment. Without this field a short read is invisible.
        ("scout schema includes files_read",
         r'"files_read": \[\]'),
        ("files_read entries are path:start-end",
         r'`files_read` lists every read as `"path:start-end"`'),
        # The worker, not the scout, decides scope: scouts cannot list dirs.
        ("worker hands scouts explicit paths and line ranges",
         r"give each chunk explicit paths and line ranges"),
        ("worker checks coverage before merging",
         r"check that each scout's `files_read` covers its assignment"),
        # Any failure mode gets exactly one retry, including timeouts.
        ("failed, timed-out, and short scouts are retried once",
         r"Re-run once any scout that fails, times out, or under-reports coverage"),
        # After the retry, verified results are kept and the gap is marked.
        ("verified results are kept",
         r"keep every result backed by `files_read`"),
        ("incomplete marker names the uncovered range",
         r"\(Documentation incomplete: scout failed: <uncovered path:start-end>\)"),
        ("marker goes in every section",
         r"to each of `D`'s three sections"),
        ("uncovered ranges and reason are recorded",
         r"record `D` with the uncovered ranges and the reason"),
        # A rerun must not carry a stale marker forward.
        ("marker is removed once its range is covered",
         r"On a later run, remove a marker once its range is covered"),
        # Swarm mode: the record must survive the worker hop.
        ("worker payload carries incomplete entries",
         r"an `incomplete` array \(`path`, `ranges`, `reason`\)"),
        ("root merges workers' incomplete arrays",
         r"merge their `incomplete` arrays into the root's list for Step 5\.6"),
        # The run ends by telling the human what to rerun, from the original
        # path: rerunning with the directory as path would reclassify it as a
        # root blueprint and replace its component sections.
        ("final report lists ranges, reason, and rerun command from the original path",
         r"print its path relative to `path`, the uncovered `path:start-end` ranges, the reason, and the rerun command `egm-bootstrap path=<path>`"),
        # Inline mode has no fresh scout context: budget, and the rest counts
        # as uncovered so it gets the same marker and report line.
        ("inline mode keeps a read budget and marks the remainder",
         r"run the scout steps inline within a 250 KB per-directory read budget; treat the rest as uncovered"),
    ],
)
def test_scout_failure_contract(clause: str, pattern: str) -> None:
  assert re.search(pattern, skill_text()), (
      f"egm-bootstrap SKILL.md no longer states: {clause}"
  )


def test_rerun_command_never_targets_the_directory() -> None:
  """`path=<D>` would make the component directory a root blueprint."""
  assert "path=<D>" not in skill_text()


def test_worker_schema_carries_incomplete_entries() -> None:
  schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
  props = schema["properties"]
  assert "incomplete" in props, "worker payload has no place for incomplete directories"
  assert "incomplete" not in schema.get("required", []), (
      "incomplete must stay optional so fully covered workers need not emit it"
  )
  item = props["incomplete"]["items"]
  assert set(item["required"]) == {"path", "ranges", "reason"}
  assert item["properties"]["ranges"]["type"] == "array"


def load_scenario(scenario_id: str) -> dict:
  data = yaml.safe_load(SCENARIOS.read_text(encoding="utf-8"))
  scenario = next(
      (s for s in data["scenarios"] if s["scenario_id"] == scenario_id), None)
  assert scenario is not None, f"{scenario_id} scenario is missing"
  return scenario


def test_scout_failure_scenario_keeps_good_chunks_and_marks_gap() -> None:
  scenario = load_scenario("bootstrap_scout_failure_is_loud")
  assertions = [a for turn in scenario["turns"] for a in turn["assertions"]]
  forbidden = " ".join(
      a["pattern"] for a in assertions if a["type"] == "forbidden_pattern")
  required = " ".join(
      a["pattern"] for a in assertions if a["type"] == "required_pattern")
  # Uncovered symbols must not appear; a directory-as-path rerun is forbidden.
  for needle in ("uncovered_fn", "test_dir"):
    assert needle in forbidden, f"scenario no longer forbids {needle!r}"
  # Kept symbols, marker, directory, range, reason, rerun from original path.
  for needle in ("covered_fn", "documentation incomplete", "test_dir", "1965",
                 "timed out", "egm-bootstrap", "repo_root"):
    assert needle in required, f"scenario no longer requires {needle!r}"
  # The loose alternative n3wth flagged ('short' matches 'shortly') is gone.
  assert "|short|" not in required


def test_swarm_scenario_requires_root_to_surface_worker_gap() -> None:
  scenario = load_scenario("bootstrap_swarm_incomplete_report")
  assertions = [a for turn in scenario["turns"] for a in turn["assertions"]]
  prompt = " ".join(turn["user_input"] for turn in scenario["turns"])
  assert '"incomplete"' in prompt, "scenario must feed the root a worker incomplete entry"
  required = " ".join(
      a["pattern"] for a in assertions if a["type"] == "required_pattern")
  for needle in ("svc/beta", "900-1420", "timed out", "repo_root"):
    assert needle in required, f"swarm scenario no longer requires {needle!r}"
  assert any(a["type"] == "forbidden_pattern" for a in assertions), (
      "swarm scenario must forbid a false all-complete claim"
  )


def test_design_doc_matches_skill_fault_tolerance() -> None:
  """docs/designs/bootstrap.md must not describe the rules this PR replaced."""
  text = " ".join(DESIGN.read_text(encoding="utf-8").split())
  for stale in ("50,000 bytes", "Details pending/documentation failed",
                "read up to 300 lines"):
    assert stale not in text, f"design doc still says {stale!r}"
  for current in ("files_read", "Documentation incomplete: scout failed",
                  "`incomplete` array", "removes a marker once its range is covered"):
    assert current in text, f"design doc does not describe {current!r}"
