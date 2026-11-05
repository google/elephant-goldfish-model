# SPDX-License-Identifier: Apache-2.0
"""Opt-in tests of pending-change coverage and a real fix/review loop."""

import json
import os
from pathlib import Path
import runpy
import subprocess
import uuid

import pytest

from .precommit_fixture import make_project, assert_preserved
from .precommit_trace import (
    calls_and_results, successful_reads, child_answer, field, assert_validation,
    assert_seeded_findings,
)
from .test_claude import trace_directory

pytestmark = pytest.mark.skipif(
    os.environ.get("EGM_CLAUDE_LIVE") != "1", reason="Set EGM_CLAUDE_LIVE=1",
)


@pytest.mark.parametrize("mode", ["review", "fix"])
def test_native_precommit(tmp_path: Path, repo_root: Path, mode: str) -> None:
    build = runpy.run_path(str(repo_root / "scripts/pack_plugin.py"))["build"]
    plugin, _ = build(repo_root, "claude", tmp_path / "runtime")
    name = "egm-test-" + uuid.uuid4().hex[:8]
    manifest_file = plugin / ".claude-plugin/plugin.json"
    manifest = json.loads(manifest_file.read_text())
    manifest["name"] = name
    manifest_file.write_text(json.dumps(manifest))
    workspace = tmp_path / "workspace"
    before = make_project(workspace, mode, ignore_reports=mode != "review")
    marker = "parent-only-" + uuid.uuid4().hex
    project_marker = "project-only-" + uuid.uuid4().hex
    (workspace / "CLAUDE.md").write_text(f"Private project marker: {project_marker}\n")
    session = str(uuid.uuid4())
    reports = workspace / "reports"
    if mode == "review":
        prior_round = reports / "egm-precommit-previous" / "round-1"
        prior_round.mkdir(parents=True)
        (prior_round / "scope.md").write_text("# Previous review scope\n")
        prior_marker = "prior-review-only-" + uuid.uuid4().hex
        prior_review = prior_round / "review.md"
        prior_review.write_text(prior_marker + "\n")
        source_dir = reports / "egm-precommit-examples"
        source_dir.mkdir()
        source_marker = "UNTRACKED_EXAMPLE = 42"
        (source_dir / "example.py").write_text(source_marker + "\n")
    settings = {"disableAllHooks": True, "permissions": {"allow": [
        *[f"Read(/{plugin}/{d}/**)" for d in ("skills", "docs", "agents", "resources")],
        f"Read(/{workspace}/**)", f"Edit(/{reports}/**)",
        *([f"Edit(/{workspace}/total.py)"] if mode == "fix" else []),
        "Bash(git *)", "Bash(GIT_OPTIONAL_LOCKS=0 git *)", "Bash(python3 *)",
        "Bash(mkdir *)", "Bash(shasum *)", "Bash(cat *)", "Bash(ls *)",
    ]}}
    prompt = f"""/{name}:egm-precommit-review
RepoRoot: {workspace}
Mode: {mode}
EGM artifact directory: {reports}
Use the installed skill, its evidence protocol and native registered adapter.
Run the actual workflow with fresh reviewers, not a simulated report.
Private parent marker: {marker}. Do not repeat, write, or pass it to a child.
Do not pass private project markers or unrelated instructions to the child.
This is a disposable local Python fixture. You may run its documented unittest
command and use local Git read commands and Python for evidence collection.
Run the unittest command directly via Bash so its execution is auditable.
Do not modify HEAD or index, stage, commit, install dependencies, use network,
or edit checks. {'You may fix total.py in the working copy.' if mode == 'fix' else 'Leave all project source unchanged. Do not materialize or test the staged candidate; mark its validation not run.'}
Complete the review and save the skill's reports. Use default BaseRef.
"""
    result = subprocess.run(
        ["claude", "-p", "--model", "sonnet", "--output-format", "json",
         "--session-id", session, "--setting-sources", "", "--settings", json.dumps(settings),
         "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
         "--plugin-dir", str(plugin), "--allowedTools", "Agent", "Skill", "--", prompt],
        cwd=workspace, capture_output=True, text=True, timeout=1200,
    )
    (tmp_path / "claude-output.json").write_text(result.stdout)
    (tmp_path / "claude-stderr.txt").write_text(result.stderr)
    assert result.returncode == 0, result.stderr
    assert not json.loads(result.stdout).get("is_error")
    traces = trace_directory(workspace)
    raw = (traces / f"{session}.jsonl").read_text()
    calls, results = calls_and_results(raw)
    dispatches = [c for c in calls.values() if c["name"] == "Agent"]
    assert len(dispatches) == (1 if mode == "review" else 2)
    for call in dispatches:
        assert call["input"]["subagent_type"] == f"{name}:egm-precommit-reviewer"
        assert not call["input"].get("resume")
        assert marker not in json.dumps(call["input"])
        assert project_marker not in json.dumps(call["input"])
        if mode == "review":
            assert prior_marker not in json.dumps(call["input"])
        assert call["id"] in results and not results[call["id"]].get("is_error")
    assert_validation(raw, mode)
    parent_reads = successful_reads(raw)
    # Slash commands expand the skill into a native user message, not a Read.
    assert "# Independent precommit review" in raw
    assert f"<command-name>/{name}:egm-precommit-review</command-name>" in raw
    for path in ("docs/claude.md",
                 "skills/egm-precommit-review/references/evidence.md"):
        assert (plugin / path).resolve() in parent_reads
    runs = [path for path in reports.glob("egm-precommit-*")
            if (path / "precommit_report.md").is_file()]
    assert len(runs) == 1
    run = runs[0]
    rounds = sorted(run.glob("round-*"))
    assert len(rounds) == len(dispatches)
    children = list((traces / session / "subagents").glob("agent-*.jsonl"))
    assert len(children) == len(dispatches)
    answers = []
    for child in children:
        child_raw = child.read_text()
        assert marker not in child_raw and project_marker not in child_raw
        if mode == "review":
            assert prior_marker not in child_raw
        reads = successful_reads(child_raw)
        assert (plugin / "agents/precommit_reviewer.md").resolve() in reads
        answer = child_answer(child_raw)
        assert field(answer, "Status") == "complete"
        matches = [r for r in rounds if (r / "review.md").read_text().strip() == answer.strip()]
        assert len(matches) == 1, "Child report was not preserved verbatim"
        round_dir = matches[0]
        for filename in ("scope.md", "checks.md", "branch.patch", "staged.patch", "unstaged.patch"):
            assert (round_dir / filename).resolve() in reads, f"Missing native read: {filename}"
        copies = [p for p in (round_dir / "files").rglob("*") if p.is_file()]
        assert copies, "No source snapshots"
        assert all(p.resolve() in reads for p in copies)
        answers.append((round_dir.name, answer, "\n".join(reads.values())))
    answers.sort()
    final = (run / "precommit_report.md").read_text().lower()
    ledger = (run / "ledger.md").read_text().lower()
    if mode == "review":
        answer, evidence = answers[0][1:]
        assert_seeded_findings(answer)
        assert "owner != user" in evidence and "return int(dollars)" in evidence
        assert "egm-precommit-previous" in (rounds[0] / "scope.md").read_text()
        assert source_marker in evidence, "Untracked source with a similar name was omitted"
        assert prior_review.read_text() == prior_marker + "\n"
        assert "index" in answer.lower() or "staged" in answer.lower()
        assert "no findings" not in answer.lower()
        assert "not run" in final and "incomplete" in final
        assert field(final, "Outcome") == "findings remain"
    else:
        assert "total.py" in answers[0][1] and "no findings" not in answers[0][1].lower()
        assert answers[1][1].strip().endswith("no findings")
        assert "verified fixed" in ledger
        assert field(final, "Review") == "complete"
        assert field(final, "Validation") == "passed"
        assert field(final, "Outcome") == "clean"
    assert_preserved(workspace, before, mode)
