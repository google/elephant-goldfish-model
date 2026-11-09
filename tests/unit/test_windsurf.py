# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Offline Windsurf workspace routing contracts."""

from pathlib import Path

from .test_harnesses import EXPECTED_SKILLS, frontmatter


def test_windsurf_adapter_routes_to_shared_skills_without_copied_text(
    repo_root: Path,
) -> None:
  rule = repo_root / ".windsurf/rules/egm.md"
  assert rule.is_file()
  rule_cfg = frontmatter(rule)
  assert rule_cfg["trigger"] == "model_decision"
  assert "fresh-context" in rule.read_text(encoding="utf-8")

  workflow_files = sorted((repo_root / ".windsurf/workflows").glob("*.md"))
  assert {w.stem for w in workflow_files} == EXPECTED_SKILLS
  for workflow in workflow_files:
    skill_name = workflow.stem
    text = workflow.read_text(encoding="utf-8")
    assert f"skills/{skill_name}/SKILL.md" in text
    assert (repo_root / "skills" / skill_name / "SKILL.md").is_file()
    assert len(text.splitlines()) <= 15, f"{workflow} must stay a thin pointer"
