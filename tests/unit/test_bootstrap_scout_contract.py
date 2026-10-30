# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Pin the egm-bootstrap scout failure contract.

The behavior itself is model-driven and covered by the
`bootstrap_scout_failure_is_loud` scenario. These checks make sure a future
edit to SKILL.md (for example a trim to stay under the load limit) cannot drop
one of the clauses that turn a lost scout chunk into a visible gap instead of a
README that looks complete.
"""

from pathlib import Path
import re

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills/egm-bootstrap/SKILL.md"
SCENARIOS = ROOT / "skills/egm-bootstrap/test_scenarios.yaml"


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
        ("worker checks coverage before merging and retries once",
         r"check that each scout's `files_read` covers its assignment; re-run a short scout once"),
        # A lost or short chunk fails the whole directory; no partial merge.
        ("short coverage counts as failure",
         r"fails, times out, or still under-reports coverage after the retry"),
        ("partial results are discarded, not merged",
         r"discard its partial results"),
        ("incomplete placeholder",
         r'\["\(Documentation incomplete: scout failed\)"\]'),
        ("uncovered ranges and reason are recorded",
         r"record `D` with the uncovered `path:start-end` ranges and the reason"),
        # The run ends by telling the human what to rerun.
        ("final report lists ranges, reason, and rerun command",
         r"print its path, the uncovered `path:start-end` ranges, the reason, and the rerun command `egm-bootstrap path=<D>`"),
        # Inline mode has no fresh scout context, so it keeps a byte budget.
        ("inline mode keeps a read budget",
         r"run the scout steps inline within a 250 KB per-directory read budget"),
    ],
)
def test_scout_failure_contract(clause: str, pattern: str) -> None:
  assert re.search(pattern, skill_text()), (
      f"egm-bootstrap SKILL.md no longer states: {clause}"
  )


def test_scout_failure_scenario_rejects_partial_merge() -> None:
  """The behavioral scenario must still forbid citing symbols from a lost chunk."""
  data = yaml.safe_load(SCENARIOS.read_text(encoding="utf-8"))
  scenario = next(
      (s for s in data["scenarios"]
       if s["scenario_id"] == "bootstrap_scout_failure_is_loud"), None)
  assert scenario is not None, "bootstrap_scout_failure_is_loud scenario is missing"
  kinds = {a["type"] for turn in scenario["turns"] for a in turn["assertions"]}
  assert "forbidden_pattern" in kinds, (
      "scenario must forbid merged symbols from the failed chunk"
  )
  required = " ".join(
      a["pattern"] for turn in scenario["turns"]
      for a in turn["assertions"] if a["type"] == "required_pattern")
  for needle in ("documentation incomplete", "1965", "egm-bootstrap"):
    assert needle in required, f"scenario no longer requires {needle!r}"
