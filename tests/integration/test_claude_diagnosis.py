# SPDX-License-Identifier: Apache-2.0
"""Opt-in test of the installed Claude diagnosis workflow and native child."""

import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import uuid

import pytest

from .diagnosis_checks import (
    assert_hypothesis_write_order, assert_unbiased_input, claude_diagnosis_answer,
    claude_reads,
)
from .test_claude import trace_directory

pytestmark = pytest.mark.skipif(
    os.environ.get("EGM_CLAUDE_LIVE") != "1",
    reason="Set EGM_CLAUDE_LIVE=1 to use an authenticated Claude CLI",
)


@pytest.mark.parametrize("prior_run", [False, True], ids=["fresh", "prior-run"])
def test_independent_bug_diagnosis(
    tmp_path: Path, repo_root: Path, prior_run: bool,
) -> None:
    build = runpy.run_path(str(repo_root / "scripts/pack_plugin.py"))["build"]
    plugin, _ = build(repo_root, "claude", tmp_path / "runtime")
    workspace = tmp_path / "workspace"
    source = workspace / "src"
    source.mkdir(parents=True)
    fixture = source / "catalog.py"
    shutil.copyfile(repo_root / "tests/fixtures/diagnosis/catalog.py", fixture)
    original = fixture.read_bytes()
    name = "egm-test-" + uuid.uuid4().hex[:8]
    manifest_path = plugin / ".claude-plugin/plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["name"] = name
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    parent_marker = "parent-only-" + uuid.uuid4().hex
    project_marker = "project-only-" + uuid.uuid4().hex
    hypothesis = "TTL expiration is broken"
    (workspace / "CLAUDE.md").write_text(
        f"Project instruction marker: {project_marker}.\n", encoding="utf-8"
    )
    session = str(uuid.uuid4())
    reports = source / "reports"
    old_hypothesis = source / ".local/old/egm-diagnosis-first/elephant_hypothesis.md"
    old_marker = "old-hypothesis-" + uuid.uuid4().hex
    if prior_run:
        subprocess.run(["git", "init", "-q"], cwd=source, check=True)
        (source / ".gitignore").write_text(".local/\n", encoding="utf-8")
        old_hypothesis.parent.mkdir(parents=True)
        old_hypothesis.write_text(old_marker, encoding="utf-8")
    settings = {
        "disableAllHooks": True,
        "permissions": {"allow": [
            *[f"Read(/{plugin}/{folder}/**)" for folder in
              ("agents", "docs", "resources", "skills")],
            f"Read(/{workspace}/**)", f"Edit(/{reports}/**)", "Bash(find *)",
        ]},
    }
    completion = (
        "Write all four artifacts and preserve the original child report unchanged."
        if not prior_run else "Report whether dispatch was possible."
    )
    prompt = f"""/{name}:egm-diagnose
Run the installed skill. SourceRoot: {source}
EGM artifact directory: {reports}
Symptom: south's guide lookup returns North guide instead of South guide.
Repro: create Catalog(); call lookup('north', 'guide', now=0), then
lookup('south', 'guide', now=1). Reported results: North guide twice.
Expected: North guide followed by South guide.
Parent-only initial hypothesis: {hypothesis}. Preserve it unchanged with the
label {parent_marker}. Follow the installed skill's persistence rules. Keep
both the theory and label out of observations and the child's task.
Investigate using the installed diagnosis skill and its native adapter, using
this candidate plugin's namespace {name}. If dispatch is allowed by the skill,
run one fresh foreground Goldfish.
Do not execute reproductions in this fixture; mark checks as not run. Do not
edit source, write tests, use external services, publish, or commit.
Use Read, Grep, Glob, and Write for local files. The parent may also use find
for metadata-only inspection. Write creates parent folders.
{completion}
"""
    result = subprocess.run(
        ["claude", "-p", "--output-format", "json", "--session-id", session,
         "--setting-sources", "", "--settings", json.dumps(settings),
         "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
         "--plugin-dir", str(plugin), "--tools", "Agent,Read,Grep,Glob,Write,Bash",
         "--allowedTools", "Agent",
         "--", prompt],
        cwd=workspace, capture_output=True, text=True, timeout=600,
    )
    # Logs stay with the temporary fixture, not in source or a public artifact.
    (tmp_path / "claude-result.json").write_text(result.stdout, encoding="utf-8")
    (tmp_path / "claude-stderr.txt").write_text(result.stderr, encoding="utf-8")
    assert result.returncode == 0, result.stderr
    outcome = json.loads(result.stdout)
    assert not outcome.get("is_error"), result.stdout
    traces = trace_directory(workspace)
    raw_parent = (traces / f"{session}.jsonl").read_text(encoding="utf-8")
    calls = []
    for line in raw_parent.split("\n"):
        if not line.strip():
            continue
        event = json.loads(line)
        content = event.get("message", {}).get("content", [])
        for block in content if isinstance(content, list) else []:
            if (event.get("type") == "assistant"
                    and block.get("type") == "tool_use"
                    and block.get("name") == "Agent"):
                calls.append(block)
    if prior_run:
        assert not calls, "Launched Goldfish with a readable prior hypothesis"
        assert "egm-diagnosis-first" in outcome["result"]
        assert old_marker not in raw_parent
        assert old_hypothesis.read_text(encoding="utf-8") == old_marker
        assert not list(reports.glob("egm-diagnosis-*"))
        return
    assert len(calls) == 1
    call = calls[0]["input"]
    assert call["subagent_type"] == f"{name}:egm-bug-diagnosis"
    assert not call.get("resume")
    assert_unbiased_input(call["prompt"], parent_marker, hypothesis)
    children = list((traces / session / "subagents").glob("agent-*.jsonl"))
    assert len(children) == 1
    raw_child = children[0].read_text(encoding="utf-8")
    assert parent_marker not in raw_child and project_marker not in raw_child
    runs = list(reports.glob("egm-diagnosis-*"))
    assert len(runs) == 1
    run = runs[0]
    observations = run / "observations.md"
    assert_unbiased_input(observations.read_text(encoding="utf-8"),
                          parent_marker, hypothesis)
    hypothesis_path = run / "elephant_hypothesis.md"
    assert parent_marker in hypothesis_path.read_text(encoding="utf-8")
    reads = claude_reads(raw_child)
    required = {plugin / "agents/bug_diagnosis.md", observations, fixture}
    assert {path.resolve() for path in required} <= reads.keys()
    assert (run / "elephant_hypothesis.md").resolve() not in reads
    assert "self.cache.get(slug)" in reads[fixture.resolve()]
    assert "self.records[(tenant, slug)]" in reads[fixture.resolve()]
    parent_reads = claude_reads(raw_parent)
    assert (plugin / "docs/claude.md").resolve() in parent_reads
    answer = claude_diagnosis_answer(raw_child)
    assert_hypothesis_write_order(raw_parent, hypothesis_path, parent_marker, answer)
    preserved = (run / "goldfish_diagnosis.md").read_text(encoding="utf-8")
    assert preserved.strip() == answer.strip(), "Child report was rewritten"
    assert "tenant" in answer.lower() and "slug" in answer.lower()
    assert "catalog.py:" in answer
    assert "falsif" in answer.lower() or "disprov" in answer.lower()
    report = (run / "diagnosis_report.md").read_text(encoding="utf-8")
    assert "diverg" in report.lower()
    assert fixture.read_bytes() == original
    assert sorted(p.relative_to(source).as_posix() for p in source.rglob("*")
                  if p.is_file() and not p.is_relative_to(reports)) == ["catalog.py"]
