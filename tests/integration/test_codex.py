# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Opt-in native Codex tests. No API use or config changes unless enabled."""

import json
import os
import pathlib
import shutil
import shlex
import subprocess
import uuid
import zipfile
from collections.abc import Iterator
from urllib.parse import unquote, urlparse

import pytest


InstalledPlugin = tuple[str, str, pathlib.Path, pathlib.Path]


pytestmark = pytest.mark.skipif(
    os.environ.get("EGM_CODEX_LIVE") != "1",
    reason="Set EGM_CODEX_LIVE=1 to install a temporary plugin and use Codex",
)


def cli(*args: str) -> dict:
    result = subprocess.run(
        ["codex", "plugin", *args, "--json"],
        capture_output=True, text=True, timeout=120, check=True,
    )
    return json.loads(result.stdout)


@pytest.fixture(scope="module")
def installed_plugin(
    repo_root: pathlib.Path, tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[InstalledPlugin]:
    """Install the candidate through Codex without replacing the user's EGM."""
    assert shutil.which("codex"), "Codex CLI is required for live tests"
    source = tmp_path_factory.mktemp("egm-marketplace")
    release_zip = os.environ.get("EGM_CODEX_RELEASE_ZIP")
    if release_zip:
        with zipfile.ZipFile(release_zip) as bundle:
            assert bundle.testzip() is None, "Release ZIP is corrupt"
            bundle.extractall(source)
    else:
        shutil.copytree(
            repo_root, source, dirs_exist_ok=True,
            ignore=shutil.ignore_patterns(
                ".git", ".venv", "__pycache__", "node_modules"),
        )
    # The OpenAI ZIP omits the marketplace file; use the checked-in metadata for both.
    marketplace = json.loads(
        (repo_root / ".agents/plugins/marketplace.json").read_text()
    )
    marketplace_file = source / ".agents/plugins/marketplace.json"
    marketplace_file.parent.mkdir(parents=True, exist_ok=True)
    name = "egm-test-" + uuid.uuid4().hex[:12]
    marketplace["name"] = name
    marketplace_file.write_text(json.dumps(marketplace))
    selector = f"egm@{name}"
    try:
        cli("marketplace", "add", str(source))
        result = cli("add", selector)
        root = pathlib.Path(result["installedPath"])
        if release_zip:
            with zipfile.ZipFile(release_zip) as bundle:
                for relative in bundle.namelist():
                    installed = root / relative
                    assert installed.is_file(), (
                        f"Release file missing from installation: {relative}"
                    )
                    assert installed.read_bytes() == bundle.read(relative), (
                        f"Installed file differs from release ZIP: {relative}"
                    )
        yield selector, name, source, root
    finally:
        subprocess.run(["codex", "plugin", "remove", selector], check=False)
        subprocess.run(["codex", "plugin", "marketplace", "remove", name], check=False)


def read_trace(thread_id: str) -> list[dict]:
    """Read only the trace identified by this test's native thread event."""
    codex_home = pathlib.Path(
        os.environ.get("CODEX_HOME", pathlib.Path.home() / ".codex")
    )
    sessions = codex_home / "sessions"
    paths = list(sessions.rglob(f"*{thread_id}.jsonl"))
    assert len(paths) == 1, f"Expected one retained Codex trace for {thread_id}"
    return [
        json.loads(line) for line in paths[0].read_text(encoding="utf-8").split("\n")
        if line.strip()
    ]


def child_traces(trace: list[dict]) -> dict[str, list[dict]]:
    """Use native activity events; never trust a parent-written completion file."""
    activities = [
        e["payload"]["item"] for e in trace
        if e["type"] == "event_msg"
        and e["payload"].get("type") == "item_completed"
        and e["payload"].get("item", {}).get("type") == "SubAgentActivity"
    ]
    started = {a["agent_thread_id"] for a in activities if a["kind"] == "started"}
    completed = {a["agent_thread_id"] for a in activities if a["kind"] == "completed"}
    assert started, "No native SubAgentActivity launch evidence; check CLI trace schema"
    assert started <= completed, "Native reviewers did not all complete"
    children = {thread_id: read_trace(thread_id) for thread_id in started}
    for child in children.values():
        assert any(
            e["type"] == "event_msg"
            and e["payload"].get("type") == "task_complete"
            for e in child
        ), "Child has no completed turn"
    return children


def assert_isolated_spawns(trace: list[dict]) -> None:
    spawns = [
        json.loads(e["payload"]["arguments"]) for e in trace
        if e["type"] == "response_item"
        and e["payload"].get("type") == "function_call"
        and e["payload"].get("name", "").split("__")[-1] == "spawn_agent"
    ]
    assert spawns, "No native spawn tool arguments retained in trace"
    assert all(s.get("fork_context") is False or s.get("fork_turns") == "none"
               for s in spawns), "Reviewer inherited parent turns"


def successful_reads(trace: list[dict]) -> set[pathlib.Path]:
    """Inspect executed file reads, not filenames mentioned by the model."""
    paths = set()
    for event in trace:
        if (event.get("type") != "event_msg"
                or event.get("payload", {}).get("type") != "item_completed"):
            continue
        item = event["payload"].get("item", {})
        if (item.get("type") != "CommandExecution"
                or item.get("status") not in {"completed", "failed"}
                or not item.get("aggregated_output")):
            continue
        output = item["aggregated_output"]
        exit_code = item.get("exit_code")
        # A compound `cat` can return useful file contents and then fail on a
        # later missing operand. Count a file only when its own contents are
        # visibly present in the captured output.
        cwd_value = item.get("cwd")
        if not cwd_value:
            continue
        cwd = pathlib.Path(unquote(urlparse(cwd_value).path))
        for command in item.get("parsed_cmd", []):
            if command.get("type") == "read" and command.get("path"):
                if exit_code == 0:
                    paths.add((cwd / command["path"]).resolve())
            elif command.get("type") == "unknown":
                # Codex labels compound shell commands as unknown. Inspect
                # only standalone cat segments with literal absolute paths.
                raw = command.get("cmd", "")
                try:
                    lexer = shlex.shlex(raw, posix=True, punctuation_chars=";")
                    lexer.whitespace_split = True
                    tokens = list(lexer)
                except ValueError:
                    continue
                segments: list[list[str]] = [[]]
                for token in tokens:
                    if token == ";":
                        segments.append([])
                    else:
                        segments[-1].append(token)
                for args in segments:
                    if (len(args) <= 1 or args[0] != "cat"
                            or any(char in arg for arg in args
                                   for char in "$`|&<>*?{}()")
                            or not all(pathlib.Path(arg).is_absolute() for arg in args[1:])):
                        continue
                    for arg in args[1:]:
                        path = pathlib.Path(arg).resolve()
                        try:
                            contents = path.read_text(encoding="utf-8")
                        except (OSError, UnicodeError):
                            continue
                        evidence = contents[:200]
                        if evidence and evidence in output:
                            paths.add(path)
    return paths


def run_codex(
    installed_plugin: InstalledPlugin, workspace: pathlib.Path, prompt: str,
) -> list[dict]:
    selector, name, source, _ = installed_plugin
    # Ignore unrelated MCP servers, hooks, and plugins from user config while
    # retaining the CLI's normal authentication. Do not copy credentials.
    command = [
        "codex", "exec", "--ignore-user-config",
        "--skip-git-repo-check", "--sandbox", "workspace-write", "--json",
        "-c", "approval_policy=\"never\"",
        "-c", f'plugins={{{json.dumps(selector)}={{enabled=true}}}}',
        "-c", (
            f'marketplaces={{{json.dumps(name)}={{source_type="local",'
            f'source={json.dumps(str(source))}}}}}'
        ),
        "-c", "features.multi_agent=true",
        "-c", "features.remote_plugin=false",
        "-c", "features.hooks=false",
        "-c", "features.memories=false",
        "-c", "model_reasoning_effort=\"medium\"",
        "-C", str(workspace), "-",
    ]
    # Logs are outside the child workspace and prompts are sent over stdin.
    log = workspace.parent / (workspace.name + ".jsonl")
    with log.open("w") as stdout, log.with_suffix(".stderr").open("w") as stderr:
        result = subprocess.run(
            command, input=prompt, text=True, stdout=stdout, stderr=stderr,
            timeout=1200,
        )
    assert result.returncode == 0, f"Codex failed; inspect {log} and its .stderr"
    events = [json.loads(line) for line in log.read_text().split("\n") if line.strip()]
    assert any(e["type"] == "turn.completed" for e in events), log
    assert not any(e["type"] in {"error", "turn.failed"} for e in events), log
    thread_id = next(e["thread_id"] for e in events if e["type"] == "thread.started")
    trace = read_trace(thread_id)
    skill_root = str(installed_plugin[3] / "skills")
    assert skill_root in json.dumps(trace), "Installed skills not discovered"
    return trace


def test_fresh_context_isolation(
    installed_plugin: InstalledPlugin, tmp_path: pathlib.Path,
) -> None:
    marker = "parent-only-" + uuid.uuid4().hex
    prompt = f"""Native EGM isolation test. Parent-only marker: {marker}
Do not write or repeat this marker, or pass it to another agent.
Use a native general-purpose subagent with no inherited turns, using the
parameter in its actual schema (fork_context: false or fork_turns: "none").
Its exact task is:
'Do not use tools. If a parent-only marker is visible in your conversation,
return it verbatim. Otherwise return exactly UNKNOWN.'
Wait for its result. Do not simulate its response. Do not use memory services,
external services, or conversation history. Report the actual child response.
"""
    trace = run_codex(installed_plugin, tmp_path, prompt)
    assert_isolated_spawns(trace)
    children = child_traces(trace)
    assert len(children) == 1
    child = next(iter(children.values()))
    assert marker not in json.dumps(child), "Parent marker leaked into child context"
    answers = [
        e["payload"].get("last_agent_message", "") for e in child
        if e["type"] == "event_msg"
        and e["payload"].get("type") == "task_complete"
    ]
    assert answers[-1].strip() == "UNKNOWN", "Child failed the isolation probe"


def test_brainstorm_draft_review(
    installed_plugin: InstalledPlugin, tmp_path: pathlib.Path,
) -> None:
    prompt = """Run the installed EGM plugin's brainstorm, draft, and review
skills on this synthetic test project. Read the skills from your available
skills inventory; do not load a source checkout instead of the installed plugin.
Feature: an offline command that counts nonblank UTF-8 lines in one local file.
Use only the Python standard library. Print one decimal count plus newline.
Whitespace-only lines are blank; empty files produce 0. Invalid UTF-8, a missing
file, and permission errors produce a clear stderr error and exit 1; success
exits 0. No network, recursive traversal, writes to input, or extra features.
Author: test fixture. Produce design artifacts only, no implementation code.

This is a noninteractive integration fixture. For this fixture only, the
synthetic user explicitly approves the anchored hypothesis, Goldfish reviews,
each drafted section, and finalization to docs/designs/line-count.md up front.
These simulated approvals do not test interactive approval-gate behavior.
Use direct dispatch for this test so each reviewer is visible in the parent
trace; test nested delegation separately. Run real fresh-context native
reviewers, wait for completion, and write concepts_brief.md and design_draft.md.
Then run egm-review on design_draft.md with Step: uninterrupted and no additional
GoldfishContext. Produce all five stage reports, including implementation
readiness. Use distinct report paths; do not overwrite another stage's report.
Do not publish, commit, use external services or memory, or modify the plugin.
Do not invent completed reviewers. Stop with a clear failure if required tools
are unavailable. Keep the fixture small and reviews concise.
"""
    trace = run_codex(installed_plugin, tmp_path, prompt)
    root = installed_plugin[3]
    # v0.1.0 uses underscores; current source skill names use hyphens.
    skill_dirs = {
        path.name.replace("_", "-"): path
        for path in (root / "skills").iterdir()
        if path.is_dir()
    }
    assert {"egm-brainstorm", "egm-draft", "egm-review"} <= skill_dirs.keys()
    required_skill_reads = {
        skill_dirs[skill] / "SKILL.md"
        for skill in ("egm-brainstorm", "egm-draft", "egm-review")
    }
    reads = successful_reads(trace)
    assert required_skill_reads <= reads, "Installed skills not read"
    assert root / "docs/codex.md" in reads, "Codex reference not read"
    for name in ("concepts_brief.md", "design_draft.md", "docs/designs/line-count.md"):
        artifact = tmp_path / name
        assert artifact.is_file(), f"Missing workflow artifact: {name}"
        assert len(artifact.read_text().strip()) > 200, f"Trivial artifact: {name}"
    assert (tmp_path / "docs/designs/line-count.md").read_bytes() == (
        tmp_path / "design_draft.md"
    ).read_bytes(), "Final design differs from the reviewed draft"
    for name in (
        "zoom_out_report.md", "comprehension_report.md", "critic_report.md",
        "intermediate_zoom_out_report.md", "implementation_readiness_report.md",
    ):
        report = tmp_path / name
        assert report.is_file(), f"Missing stage report: {name}"
        assert len(report.read_text().strip()) > 100, f"Empty/trivial report: {name}"
    assert_isolated_spawns(trace)
    children = child_traces(trace)
    assert len(children) >= 15, "Expected six brainstorm and nine stage reviewers"
    assert not list(tmp_path.rglob("*.py")), "Design workflow wrote implementation code"
