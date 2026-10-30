# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Run the actual scope workflow against an offline GitHub API harness."""

from pathlib import Path
import subprocess

import yaml


def test_scope_advisory() -> None:
  root = Path(__file__).resolve().parents[2]
  workflow = yaml.safe_load(
      (root / ".github/workflows/pr-scope-advisory.yml").read_text()
  )
  steps = workflow["jobs"]["scope-advisory"]["steps"]
  script = next(step["with"]["script"] for step in steps
                if step.get("uses", "").startswith("actions/github-script@"))
  result = subprocess.run(
      ["node", str(root / "tests/scope_advisory.cjs")],
      input=script, capture_output=True, text=True, timeout=30,
  )
  assert result.returncode == 0, result.stdout + result.stderr
