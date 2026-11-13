# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Run the actual issue triage workflow against an offline GitHub API harness."""

from pathlib import Path
import subprocess

import yaml


def test_issue_triage() -> None:
  root = Path(__file__).resolve().parents[2]
  workflow = yaml.safe_load(
      (root / ".github/workflows/issue-triage.yml").read_text(encoding="utf-8")
  )
  trigger = workflow.get("on", workflow.get(True))
  assert trigger == {"issues": {"types": ["opened"]}}
  job = workflow["jobs"]["issue-triage"]
  assert job["permissions"] == {"issues": "write"}
  steps = job["steps"]
  script = next(
      step["with"]["script"]
      for step in steps
      if step.get("uses", "").startswith("actions/github-script@")
  )
  result = subprocess.run(
      ["node", str(root / "tests/issue_triage.cjs")],
      input=script,
      capture_output=True,
      text=True,
      timeout=30,
      check=False,
  )
  assert result.returncode == 0, result.stdout + result.stderr
