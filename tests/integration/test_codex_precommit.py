# SPDX-License-Identifier: Apache-2.0
"""Opt-in installed Codex precommit review, with native child evidence."""

import json
import os
from pathlib import Path
import warnings

import pytest

from .precommit_fixture import make_project, assert_preserved
from .precommit_trace import codex_full_reads, field, assert_seeded_findings, summary_field
from .test_codex import (
    installed_plugin, run_codex, child_traces, assert_isolated_spawns,
)

pytestmark = pytest.mark.skipif(
    os.environ.get("EGM_CODEX_LIVE") != "1", reason="Set EGM_CODEX_LIVE=1",
)


def test_native_precommit(installed_plugin, tmp_path: Path) -> None:
    root = installed_plugin[3]
    if not (root / "skills/egm-precommit-review/SKILL.md").is_file():
        pytest.skip("Release predates egm-precommit-review")
    workspace = tmp_path / "workspace"
    before = make_project(workspace, "review")
    prompt = f"""Run the installed egm-precommit-review skill.
RepoRoot: {workspace}
Mode: review
EGM artifact directory: {workspace / 'reports'}
Use its installed evidence protocol and a real fresh native reviewer.
This is a disposable local Python fixture. You may run the README unittest
command and read Git data. Do not materialize or test the staged candidate;
record its validation as not run. Do not edit source, stage, commit, install
dependencies or use the network. Use default BaseRef.
For auditable native reads in this fixture, use a separate plain cat command
for each absolute literal filename, including empty patches. Do path/type
checks separately; no conditional shells or compound cat commands. Pass that
read instruction to the child. Preserve its actual report and complete the workflow.
"""
    trace = run_codex(installed_plugin, workspace, prompt)
    assert_isolated_spawns(trace)
    children = child_traces(trace)
    assert len(children) == 1
    child = next(iter(children.values()))
    reads = codex_full_reads(child)
    assert (root / "agents/precommit_reviewer.md").resolve() in reads
    answers = [e["payload"].get("last_agent_message", "") for e in child
               if e["type"] == "event_msg" and e["payload"].get("type") == "task_complete"]
    assert answers and answers[-1].strip()
    answer = answers[-1]
    assert field(answer, "Status") == "complete"
    assert_seeded_findings(answer)
    assert "no findings" not in answer.lower()
    runs = list((workspace / "reports").glob("egm-precommit-*"))
    assert len(runs) == 1
    rounds = list(runs[0].glob("round-*"))
    assert len(rounds) == 1
    round_dir = rounds[0]
    assert (round_dir / "review.md").read_text().strip() == answer.strip()
    for filename in ("scope.md", "checks.md", "branch.patch", "staged.patch", "unstaged.patch"):
        assert (round_dir / filename).resolve() in reads
    copies = [p for p in (round_dir / "files").rglob("*") if p.is_file()]
    assert copies and all(p.resolve() in reads for p in copies)
    final = (runs[0] / "precommit_report.md").read_text().lower()
    assert "not run" in final and "incomplete" in final
    assert summary_field(final, "Outcome") == "findings remain"
    # Native dispatch payloads may be encrypted. Never call their absence proof.
    if "gAAAA" in json.dumps(trace):
        warnings.warn("Encrypted dispatch input cannot be fully audited", stacklevel=1)
    assert_preserved(workspace, before, "review")
