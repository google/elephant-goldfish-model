# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Offline Cursor package contracts, not native workflow or isolation proof."""

import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess

import pytest

from .test_harnesses import REVIEWERS, frontmatter

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def installed(tmp_path: Path) -> Path:
    """Reproduce the documented copy, without another host's manifest."""
    package = tmp_path / "Cursor candidate café" / "egm"
    package.mkdir(parents=True)
    for name in (".cursor-plugin", "skills", "agents", "resources", "docs"):
        shutil.copytree(ROOT / name, package / name)
    shutil.copy2(ROOT / "LICENSE", package / "LICENSE")
    return package


def test_manifest_selects_native_adapters(installed: Path) -> None:
    manifest = json.loads(
        (installed / ".cursor-plugin/plugin.json").read_text(encoding="utf-8")
    )
    canonical = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    for field in ("name", "version", "homepage",
                  "repository", "license"):
        assert manifest[field] == canonical[field]
    assert manifest["author"] == {"name": "Google"}
    assert manifest["description"] == "Draft specs, review designs, and check implementation drift."
    assert manifest["skills"] == "./skills/"
    assert manifest["agents"] == "./.cursor-plugin/agents/"
    assert manifest["rules"] == "./.cursor-plugin/rules/"
    assert set(manifest) == {
        "name", "version", "description", "author", "homepage", "repository",
        "license", "skills", "agents", "rules", "logo",
    }
    assert not (installed / "plugin.json").exists()
    assert (installed / manifest["logo"]).is_file()
    for component in ("skills", "agents", "rules"):
        assert (installed / manifest[component]).is_dir()
    adapters = installed / manifest["agents"]
    assert {p.stem for p in adapters.glob("*.md")} == set(REVIEWERS)


@pytest.mark.parametrize("name", sorted(REVIEWERS))
def test_reviewers_use_canonical_personas(installed: Path, name: str) -> None:
    adapter = installed / ".cursor-plugin/agents" / f"{name}.md"
    config = frontmatter(adapter)
    persona = installed / "agents" / f"{name}.md"
    assert config["name"] == frontmatter(persona)["name"]
    assert config["readonly"] is True
    assert config["permissionMode"] == "readonly"
    assert config["is_background"] is False
    assert config["model"] == "inherit"
    assert set(config) == {
        "name", "description", "model", "readonly", "permissionMode", "is_background",
    }
    text = adapter.read_text(encoding="utf-8")
    paths = re.findall(r"EGM_ROOT/([\w/.-]+\.md)", text)
    assert paths == [f"agents/{name}.md"]
    assert all((installed / path).is_file() for path in paths)
    assert "incomplete review" in text
    assert len(text.splitlines()) < 25  # Routing only, no copied persona rules.
    assert persona.read_bytes() == (ROOT / "agents" / persona.name).read_bytes()


def test_relocated_package_keeps_all_canonical_resources(installed: Path) -> None:
    for folder in ("skills", "agents", "resources", "docs"):
        for source in (ROOT / folder).rglob("*"):
            if source.is_file():
                destination = installed / source.relative_to(ROOT)
                assert not destination.is_symlink()
                assert destination.read_bytes() == source.read_bytes()
    for prompt in [*installed.glob("skills/*/SKILL.md"),
                   *installed.glob("agents/*.md")]:
        if prompt.name == "SKILL.md":
            assert prompt.parents[2] == installed
        text = prompt.read_text(encoding="utf-8")
        for target in re.findall(
            r"`((?:agents|resources|references)/[^`\s]+\.md)`", text
        ):
            if any(char in target for char in "{}[]<>"):
                continue
            base = prompt.parent if target.startswith("references/") else installed
            assert (base / target).is_file(), f"{prompt}: missing {target}"
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if target.startswith("../../"):
                assert (prompt.parent / target.split("#")[0]).is_file()


def test_host_rule_and_guide_keep_failure_and_artifact_contracts() -> None:
    rule = ROOT / ".cursor-plugin/rules/egm.mdc"
    assert frontmatter(rule)["alwaysApply"] is True
    text = " ".join(rule.read_text(encoding="utf-8").split())
    for contract in (
        "EGM_ROOT/docs/cursor.md", "absolute file paths", "Never resume",
        "human approval gates", "stop the stage", "Do not simulate",
    ):
        assert contract in text
    guide = " ".join((ROOT / "docs/cursor.md").read_text(encoding="utf-8").split())
    assert "EGM artifact directory: <path>" in guide
    assert "Grok Bot remains a separate, unverified surface" in guide
    assert "No complete Cursor workflow trace parser is supplied" in guide


def test_installed_cursor_native_loader(installed: Path) -> None:
    """Opt-in probe of the actual pinned loader, with no CLI main or model call."""
    bundle_path = os.environ.get("EGM_CURSOR_BUNDLE")
    if not bundle_path:
        pytest.skip("Set EGM_CURSOR_BUNDLE for the pinned native offline probe")
    bundle = Path(bundle_path).resolve()
    pins = {
        ("Darwin", "arm64"): "f6bd8dece34b56431ee74f1ac827e032d054381085e7da7088e85abdd1008330",
        ("Linux", "aarch64"): "90ec23826cd3089232b0b243b8954ac72fab0454dd86d7d71ddae29d39c75cd2",
    }
    expected = pins.get((platform.system(), platform.machine()))
    assert expected, "The native loader probe has not been audited on this platform"
    assert hashlib.sha256(bundle.read_bytes()).hexdigest() == expected, (
        "Re-audit the private loader interface before changing this version pin"
    )
    script = r'''
const fs = require('node:fs')
const Module = require('node:module')
const [filename, packageRoot] = process.argv.slice(1)
const entry = 'var __webpack_exports__=__webpack_require__("./src/main.tsx")'
const source = fs.readFileSync(filename, 'utf8')
if (!source.includes(entry)) throw new Error('Unrecognized bundle entry')
const deny = () => { throw new Error('Network/process use forbidden in offline probe') }
require('node:net').Socket.prototype.connect = deny
globalThis.fetch = deny
for (const key of ['spawn', 'spawnSync', 'exec', 'execSync', 'execFile', 'execFileSync', 'fork']) {
  require('node:child_process')[key] = deny
}
const loaded = new Module(filename, module)
loaded.filename = filename
loaded.paths = Module._nodeModulePaths(require('node:path').dirname(filename))
loaded._compile(source.replace(entry,
  'module.exports=__webpack_require__("../cursor-plugins/dist/index.js")'), filename)
loaded.exports.Y__(packageRoot, 'egm').then(plugin => {
  console.log(JSON.stringify({
    skills: plugin.skills.map(skill => skill.name),
    agents: plugin.agents.map(({ name, model, permissionMode }) => ({ name, model, permissionMode })),
    rules: plugin.rules.map(({ alwaysApply }) => ({ alwaysApply }))
  }))
}).catch(error => { console.error(error.message); process.exitCode = 1 })
'''
    result = subprocess.run(
        [str(bundle.parent / "node"), "-e", script, str(bundle), str(installed)],
        capture_output=True, text=True, check=True, timeout=30,
    )
    native = json.loads(result.stdout)
    assert set(native["skills"]) == {
        frontmatter(path)["name"] for path in (ROOT / "skills").glob("*/SKILL.md")
    }
    expected_agents = {
        frontmatter(ROOT / "agents" / f"{name}.md")["name"] for name in REVIEWERS
    }
    assert {agent["name"] for agent in native["agents"]} == expected_agents
    assert len(native["agents"]) == len(expected_agents)
    assert all(agent["permissionMode"] == "readonly" for agent in native["agents"])
    assert all(agent["model"] == "inherit" for agent in native["agents"])
    assert native["rules"] == [{"alwaysApply": True}]
