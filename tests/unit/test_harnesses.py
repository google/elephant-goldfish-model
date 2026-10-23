# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Offline packaging and isolation contracts for shared and host manifests."""

import json
import os
from pathlib import Path
import re
import runpy
import shutil
import subprocess

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_URL = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
NAME_RE = r"(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?"
COMPATIBILITY_MANIFESTS = (
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
    ".hermes/plugin.yaml",
    ".openclaw/openclaw.json",
    ".delta/plugin.json",
)
MARKETPLACES = (
    ".agents/plugins/marketplace.json",
    ".claude-plugin/marketplace.json",
)
EXPECTED_SKILLS = {
    "egm-bootstrap", "egm-brainstorm", "egm-draft", "egm-drift-report",
    "egm-resolve", "egm-review", "egm-review-loop",
}
REVIEWERS = (
    "codebase_details", "comprehension", "design_critic",
    "implementation_readiness", "structural", "style", "zoom_out",
)


@pytest.mark.parametrize("separator", ["\u0085", "\u2028", "\u2029"])
def test_jsonl_preserves_unicode_separators(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, separator: str
) -> None:
  """JSONL records end at LF, not Unicode separators inside JSON strings."""
  read_trace = runpy.run_path(str(ROOT / "tests/integration/test_codex.py"))[
      "read_trace"
  ]
  monkeypatch.setenv("CODEX_HOME", str(tmp_path))
  sessions = tmp_path / "sessions"
  sessions.mkdir()
  event = {"type": "response_item", "payload": {"text": f"left{separator}right"}}
  (sessions / "fixture-id.jsonl").write_text(
      json.dumps(event, ensure_ascii=False) + "\n", encoding="utf-8"
  )
  assert read_trace("fixture-id") == [event]


def read_manifest(path: str | Path) -> dict:
  target = ROOT / path if not Path(path).is_absolute() else Path(path)
  content = target.read_text(encoding="utf-8")
  data = yaml.safe_load(content)
  assert isinstance(data, dict), (
      f"Manifest at {path} did not parse into a dictionary: got {type(data).__name__}"
  )
  return data


# Backwards compatibility alias
read_json = read_manifest


def frontmatter(path: Path) -> dict:
  return yaml.safe_load(path.read_text(encoding="utf-8").split("---", 2)[1])


def test_portable_manifest_schema() -> None:
  manifest = read_manifest("plugin.json")
  assert manifest["$schema"] == SCHEMA_URL
  assert re.fullmatch(NAME_RE, manifest["name"])
  assert re.fullmatch(r"\d+\.\d+\.\d+", manifest["version"])


@pytest.mark.parametrize("path", COMPATIBILITY_MANIFESTS)
def test_compatibility_metadata_matches_root(path: str) -> None:
  canonical = read_manifest("plugin.json")
  manifest = read_manifest(path)
  for field in ("name", "version", "description", "repository", "license"):
    assert field in manifest, f"{path}: missing mandatory field '{field}'"
    assert manifest[field] == canonical[field], f"{path}: {field} drift"
  if "author" in manifest:
    assert manifest["author"] == canonical["author"], f"{path}: author drift"
  elif "interface" in manifest and "developerName" in manifest["interface"]:
    assert manifest["interface"]["developerName"] == canonical["author"]["name"], (
        f"{path}: developerName drift"
    )
  else:
    pytest.fail(f"{path}: missing author or interface.developerName")
  if "homepage" in manifest:
    assert manifest["homepage"] == canonical["homepage"], f"{path}: homepage drift"
  if "skills" in manifest:
    skills_root = (ROOT / manifest["skills"]).resolve()
    assert skills_root == ROOT / "skills"
    names = [frontmatter(s)["name"] for s in skills_root.glob("*/SKILL.md")]
    assert len(names) == len(set(names))
    assert set(names) == EXPECTED_SKILLS
  if "agents" in manifest and isinstance(manifest["agents"], str):
    assert (ROOT / manifest["agents"]).resolve() == ROOT / "agents"


@pytest.mark.parametrize("path", MARKETPLACES)
def test_marketplace_resolves_shared_package(path: str) -> None:
  canonical = read_manifest("plugin.json")
  marketplace = read_manifest(path)
  assert marketplace["name"] == "egm"
  assert len(marketplace["plugins"]) == 1
  entry = marketplace["plugins"][0]
  assert entry["name"] == canonical["name"]
  assert (ROOT / entry["source"]).resolve() == ROOT
  if "description" in entry:
    assert entry["description"] == canonical["description"]
  if path == ".agents/plugins/marketplace.json":
    assert entry["policy"] == {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL",
    }
    assert entry["category"] == "Productivity"


@pytest.mark.parametrize("name", REVIEWERS)
def test_claude_reviewers_are_read_only_with_fresh_context(name: str) -> None:
  adapter = ROOT / ".claude-plugin/agents" / f"{name}.md"
  config = frontmatter(adapter)
  assert isinstance(config["tools"], list)
  assert set(config["tools"]) == {"Read", "Grep", "Glob"}
  assert config["model"] == "inherit"
  assert config["omitClaudeMd"] is True
  assert "memory" not in config
  assert f"${{CLAUDE_PLUGIN_ROOT}}/agents/{name}.md" in adapter.read_text(encoding="utf-8")
  canonical = frontmatter(ROOT / "agents" / f"{name}.md")
  assert canonical["name"] == config["name"]
  assert "tools" not in canonical
  assert "omitClaudeMd" not in canonical


def test_claude_synthesizer_adapter_is_tool_restricted() -> None:
  adapter = ROOT / ".claude-plugin/agents/synthesizer.md"
  config = frontmatter(adapter)
  assert set(config["tools"]) == {"Agent", "Read", "Grep", "Glob", "Write"}
  assert config["model"] == "inherit"
  assert "memory" not in config
  assert "${CLAUDE_PLUGIN_ROOT}/agents/synthesizer.md" in adapter.read_text(encoding="utf-8")
  canonical = frontmatter(ROOT / "agents/synthesizer.md")
  assert canonical["name"] == config["name"]
  assert "tools" not in canonical
  manifest = read_manifest(".claude-plugin/plugin.json")["agents"]
  assert "./.claude-plugin/agents/synthesizer.md" in manifest
  assert "./agents/synthesizer.md" not in manifest


def test_claude_bootstrap_adapter_routes_to_skill() -> None:
  adapter = ROOT / ".claude-plugin/agents/bootstrap_orchestrator.md"
  config = frontmatter(adapter)
  assert "tools" not in config
  assert config["model"] == "inherit"
  text = adapter.read_text(encoding="utf-8")
  assert "${CLAUDE_PLUGIN_ROOT}/agents/bootstrap_orchestrator.md" in text
  assert "${CLAUDE_PLUGIN_ROOT}/skills/egm_bootstrap/SKILL.md" in text
  canonical = frontmatter(ROOT / "agents/bootstrap_orchestrator.md")
  assert canonical["name"] == config["name"]
  manifest = read_manifest(".claude-plugin/plugin.json")["agents"]
  assert "./.claude-plugin/agents/bootstrap_orchestrator.md" in manifest
  assert "./agents/bootstrap_orchestrator.md" not in manifest


READ_HOOK = ".claude-plugin/hooks/allow_plugin_reads.sh"


def find_posix_shell() -> str | None:
  if os.name != "nt":
    return shutil.which("sh") or shutil.which("bash") or "sh"
  for name in ("sh", "bash"):
    candidate = shutil.which(name)
    if candidate and "system32" not in candidate.lower():
      return candidate
  git = shutil.which("git")
  if git:
    git_root = Path(git).resolve().parents[1]
    for rel in ("bin/sh.exe", "usr/bin/sh.exe", "bin/bash.exe", "usr/bin/bash.exe"):
      sh_path = git_root / rel
      if sh_path.is_file():
        return str(sh_path)
  for pf in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
    if pf:
      for rel in ("Git/bin/sh.exe", "Git/usr/bin/sh.exe", "Git/bin/bash.exe"):
        sh_path = Path(pf) / rel
        if sh_path.is_file():
          return str(sh_path)
  return None


def run_read_hook(tool_name: str, tool_input: dict) -> str:
  shell = find_posix_shell()
  if not shell:
    pytest.skip("POSIX shell not available on Windows")
  hook_path = (ROOT / READ_HOOK).as_posix() if os.name == "nt" else str(ROOT / READ_HOOK)
  result = subprocess.run(
      [shell, hook_path],
      input=json.dumps({"tool_name": tool_name, "tool_input": tool_input}),
      capture_output=True,
      text=True,
      check=True,
      env={**os.environ, "CLAUDE_PLUGIN_ROOT": ROOT.as_posix() if os.name == "nt" else str(ROOT)},
  )
  return result.stdout


def test_claude_read_hook_is_registered() -> None:
  hooks = read_manifest(".claude-plugin/plugin.json")["hooks"]["PreToolUse"]
  assert [hook["matcher"] for hook in hooks] == ["Read|Grep|Glob"]
  command = hooks[0]["hooks"][0]["command"]
  assert command == f'"${{CLAUDE_PLUGIN_ROOT}}/{READ_HOOK}"'


@pytest.mark.parametrize(
    ("tool_name", "tool_input", "allowed"),
    [
        ("Read", {"file_path": "{root}/agents/style.md"}, True),
        ("Read", {"file_path": "{root}/docs/claude.md"}, True),
        ("Read", {"file_path": "{root}/skills/egm_review/SKILL.md"}, True),
        ("Grep", {"pattern": "x", "path": "{root}/resources"}, True),
        ("Glob", {"pattern": "**/*.md", "path": "{root}/agents"}, True),
        ("Read", {"file_path": "/etc/passwd"}, False),
        ("Read", {"file_path": "{root}/agents/../../etc/passwd"}, False),
        ("Read", {"file_path": "{root}-evil/agents/style.md"}, False),
        ("Read", {"file_path": "{root}/agents-evil/style.md"}, False),
        ("Read", {"file_path": "{root}/README.md"}, False),
        ("Read", {"file_path": "{root}/.claude/settings.local.json"}, False),
        ("Grep", {"pattern": "x", "path": "{root}"}, False),
        ("Grep", {"pattern": '"path":"{root}/agents"', "path": "/etc"}, False),
        ("Glob", {"pattern": "**/*.md"}, False),
        ("Glob", {"pattern": "/etc/*", "path": "{root}/agents"}, False),
        ("Glob", {"pattern": "~/.ssh/*", "path": "{root}/agents"}, False),
    ],
)
def test_claude_read_hook_approves_plugin_folders_only(
    tool_name: str, tool_input: dict, allowed: bool
) -> None:
  """Only clean paths in the folders EGM reads skip the permission prompt."""
  root_str = ROOT.as_posix() if os.name == "nt" else str(ROOT)
  tool_input = {k: v.replace("{root}", root_str) for k, v in tool_input.items()}
  output = run_read_hook(tool_name, tool_input)
  assert ('"permissionDecision":"allow"' in output) is allowed


def test_claude_manifest_agents_and_shared_personas_resolve() -> None:
  paths = read_manifest(".claude-plugin/plugin.json")["agents"]
  assert all((ROOT / path).is_file() for path in paths)
  personas = [frontmatter(p)["name"] for p in (ROOT / "agents").glob("*.md")]
  assert len(personas) == len(set(personas)), "Ambiguous persona name"


def test_bundled_prompt_dependencies_and_harness_guides() -> None:
  assert (ROOT / "docs/claude.md").is_file()
  assert (ROOT / "docs/codex.md").is_file()
  skills = list((ROOT / "skills").glob("*/SKILL.md"))
  for skill in skills:
    text = skill.read_text(encoding="utf-8")
    assert "${CLAUDE_PLUGIN_ROOT}/docs/claude.md" in text
    targets = re.findall(r"\[Codex integration\]\(([^)]+)\)", text)
    assert len(targets) == 1
    assert (skill.parent / targets[0]).resolve() == ROOT / "docs/codex.md"

  prompts = skills + list((ROOT / "agents").glob("*.md"))
  for prompt in prompts:
    for target in re.findall(
        r"`((?:agents|resources|references)/[^`\s]+\.md)`",
        prompt.read_text(encoding="utf-8"),
    ):
      if any(char in target for char in "{}[]<>"):
        continue
      base = prompt.parent if target.startswith("references/") else ROOT
      assert (base / target).is_file(), f"{prompt}: missing {target}"
