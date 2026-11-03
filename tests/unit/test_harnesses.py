# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Offline packaging and isolation contracts for shared and host manifests."""

import json
from pathlib import Path
import re
import runpy
from xml.etree import ElementTree

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
NAME_RE = r"(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?"
COMPATIBILITY_MANIFESTS = (
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
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


def read_json(path: str) -> dict:
  return json.loads((ROOT / path).read_text(encoding="utf-8"))


def frontmatter(path: Path) -> dict:
  return yaml.safe_load(path.read_text(encoding="utf-8").split("---", 2)[1])


def test_portable_manifest_schema() -> None:
  # The $schema key is deliberately omitted: omp (Oh My Pi) routes manifests
  # that declare the agent-plugins 1.0.0 schema to its strict validator, which
  # rejects the skills' disable-model-invocation frontmatter field.
  manifest = read_json("plugin.json")
  assert re.fullmatch(NAME_RE, manifest["name"])
  assert re.fullmatch(r"\d+\.\d+\.\d+", manifest["version"])


def test_openai_submission_metadata_and_assets() -> None:
  """Check public listing limits and bundled paths, not just JSON syntax."""
  extension = read_json("plugin.json")["extensions"]["com.openai"]
  codex = read_json(".codex-plugin/plugin.json")
  assert extension["interface"] == codex["interface"]
  assert extension["requires_local_executor"] is True
  assert codex["requires_local_executor"] is True
  assert codex["author"] == read_json("plugin.json")["author"]
  interface = extension["interface"]
  for field, limit in (
      ("displayName", 30), ("shortDescription", 30),
      ("longDescription", 4000), ("developerName", 80),
  ):
    assert 0 < len(interface[field]) <= limit, field
  assert len(interface["capabilities"]) <= 20
  assert all(0 < len(item) <= 120 for item in interface["capabilities"])
  for field in ("composerIcon", "logo"):
    path = interface[field]
    assert path.startswith("./assets/")
    asset = (ROOT / path).resolve()
    assert asset.is_relative_to(ROOT / "assets")
    assert asset.is_file() and asset.stat().st_size <= 5 * 1024 * 1024
    svg = ElementTree.parse(asset).getroot()
    assert float(svg.attrib["width"]) == float(svg.attrib["height"]) >= 48


@pytest.mark.parametrize("path", COMPATIBILITY_MANIFESTS)
def test_compatibility_metadata_matches_root(path: str) -> None:
  canonical = read_json("plugin.json")
  manifest = read_json(path)
  for field in ("name", "version", "description"):
    assert manifest[field] == canonical[field], f"{path}: {field} drift"
  for field in ("author", "homepage", "repository", "license"):
    if field in manifest:
      assert manifest[field] == canonical[field], f"{path}: {field} drift"
  if "interface" in manifest:
    assert manifest["interface"]["developerName"] == canonical["author"]["name"]
  if "skills" in manifest:
    skills_root = (ROOT / manifest["skills"]).resolve()
    assert skills_root == ROOT / "skills"
    names = [frontmatter(s)["name"] for s in skills_root.glob("*/SKILL.md")]
    assert len(names) == len(set(names))
    assert set(names) == EXPECTED_SKILLS


@pytest.mark.parametrize("path", MARKETPLACES)
def test_marketplace_resolves_shared_package(path: str) -> None:
  canonical = read_json("plugin.json")
  marketplace = read_json(path)
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
  assert f"${{CLAUDE_PLUGIN_ROOT}}/agents/{name}.md" in adapter.read_text()
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
  assert "${CLAUDE_PLUGIN_ROOT}/agents/synthesizer.md" in adapter.read_text()
  canonical = frontmatter(ROOT / "agents/synthesizer.md")
  assert canonical["name"] == config["name"]
  assert "tools" not in canonical
  manifest = read_json(".claude-plugin/plugin.json")["agents"]
  assert "./.claude-plugin/agents/synthesizer.md" in manifest
  assert "./agents/synthesizer.md" not in manifest


def test_claude_bootstrap_adapter_routes_to_skill() -> None:
  adapter = ROOT / ".claude-plugin/agents/bootstrap_orchestrator.md"
  config = frontmatter(adapter)
  assert set(config["tools"]) == {"Agent", "Bash", "Read", "Grep", "Glob", "Write", "Edit"}
  assert config["model"] == "inherit"
  text = adapter.read_text()
  assert "${CLAUDE_PLUGIN_ROOT}/agents/bootstrap_orchestrator.md" in text
  assert "${CLAUDE_PLUGIN_ROOT}/skills/egm-bootstrap/SKILL.md" in text
  canonical = frontmatter(ROOT / "agents/bootstrap_orchestrator.md")
  assert canonical["name"] == config["name"]
  manifest = read_json(".claude-plugin/plugin.json")["agents"]
  assert "./.claude-plugin/agents/bootstrap_orchestrator.md" in manifest
  assert "./agents/bootstrap_orchestrator.md" not in manifest


def test_claude_permissions_remain_under_user_control() -> None:
  """Bundled resources must not carry an automatic permission override."""
  manifest = read_json(".claude-plugin/plugin.json")
  assert "hooks" not in manifest
  assert not (ROOT / ".claude-plugin/hooks/allow_plugin_reads.sh").exists()
  assert not (ROOT / "hooks/hooks.json").exists()


def test_claude_manifest_agents_and_shared_personas_resolve() -> None:
  paths = read_json(".claude-plugin/plugin.json")["agents"]
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


def test_artifact_directory_override_is_documented_for_each_harness() -> None:
  # The models match this exact line in the user's prompt or instruction file.
  marker = "EGM artifact directory: "
  for guide in ("docs/claude.md", "docs/codex.md", "docs/harnesses.md"):
    text = " ".join((ROOT / guide).read_text(encoding="utf-8").split())
    assert marker in text, f"{guide} does not document `{marker}<path>`"
