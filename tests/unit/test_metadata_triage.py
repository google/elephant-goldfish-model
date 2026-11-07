# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Check the metadata classifier and its workflow trust boundaries offline."""

from pathlib import Path
import subprocess

import yaml


ROOT = Path(__file__).resolve().parents[2]


def test_metadata_triage() -> None:
    result = subprocess.run(
        ["node", str(ROOT / "tests/metadata_triage.cjs")],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_metadata_workflow_boundaries() -> None:
    workflow = yaml.safe_load(
        (ROOT / ".github/workflows/metadata-triage.yml").read_text()
    )
    triggers = workflow.get("on", workflow.get(True))
    assert triggers["issues"]["types"] == ["opened"]
    assert triggers["pull_request_target"]["types"] == ["opened", "synchronize"]
    assert workflow["permissions"] == {}
    classify = workflow["jobs"]["classify"]
    publish = workflow["jobs"]["publish"]
    assert classify["permissions"]["issues"] == "read"
    assert "github.run_attempt == 1" in classify["if"]
    assert "workflow_dispatch" in publish["if"]
    assert "EGM_TRIAGE_APPLY" in publish["if"]
    for job in [classify, publish]:
        checkout = job["steps"][0]["with"]
        assert checkout["persist-credentials"] is False
        assert checkout["ref"] == "${{ github.event.pull_request.base.sha || github.sha }}"
        assert "GEMINI_API_KEY" not in str(publish)
