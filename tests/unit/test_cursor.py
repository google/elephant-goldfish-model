# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Offline Cursor package contracts, not native workflow or isolation proof."""

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import subprocess

import pytest

from .test_harnesses import frontmatter

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / ".cursor-plugin"
SHARED = ("skills", "agents", "resources")

# Canonical roles that coordinate children rather than review. They are named
# roles, not a count; every other persona in agents/ is a reviewer.
ORCHESTRATOR_ROLES = frozenset({"synthesizer", "bootstrap_orchestrator"})


def shared_skill_names() -> set[str]:
    return {frontmatter(p)["name"] for p in (ROOT / "skills").glob("*/SKILL.md")}


def reviewer_personas() -> list[str]:
    return sorted(p.stem for p in (ROOT / "agents").glob("*.md")
                  if p.stem not in ORCHESTRATOR_ROLES)


REVIEWER_PERSONAS = reviewer_personas()


def copy_package(destination: Path) -> Path:
    """Reproduce the documented install copy, without another host's manifest."""
    destination.mkdir(parents=True)
    for name in (".cursor-plugin", "skills", "agents", "resources", "docs"):
        shutil.copytree(ROOT / name, destination / name)
    shutil.copy2(ROOT / "LICENSE", destination / "LICENSE")
    return destination


@pytest.fixture
def installed(tmp_path: Path) -> Path:
    return copy_package(tmp_path / "Cursor candidate café" / "egm")


def test_reviewer_set_is_derived_from_shared_personas() -> None:
    personas = {p.stem for p in (ROOT / "agents").glob("*.md")}
    assert ORCHESTRATOR_ROLES <= personas, "Update ORCHESTRATOR_ROLES to the tree"
    assert REVIEWER_PERSONAS, "No reviewer personas discovered in agents/"
    # Cross-check the role split against the one data-driven signal in the tree:
    # only orchestrator adapters for Claude may dispatch children.
    dispatchers = {
        p.stem for p in (ROOT / ".claude-plugin/agents").glob("*.md")
        if "Agent" in (frontmatter(p).get("tools") or [])
    }
    assert dispatchers == ORCHESTRATOR_ROLES


def test_manifest_selects_native_adapters(installed: Path) -> None:
    manifest = json.loads(
        (installed / ".cursor-plugin/plugin.json").read_text(encoding="utf-8")
    )
    canonical = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    for field in ("name", "version", "description", "homepage",
                  "repository", "license"):
        assert manifest[field] == canonical[field]
    assert manifest["author"] == {"name": "Google"}
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
    assert {p.stem for p in adapters.glob("*.md")} == set(REVIEWER_PERSONAS)


@pytest.mark.parametrize("manifest_path", [
    ".cursor-plugin/plugin.json", ".cursor-plugin/marketplace.json",
])
def test_manifest_paths_stay_inside_the_plugin(installed: Path,
                                               manifest_path: str) -> None:
    """Cursor requires relative component paths without `..` or escapes."""
    data = json.loads((installed / manifest_path).read_text(encoding="utf-8"))
    paths = [data[key] for key in ("logo", "skills", "agents", "rules") if key in data]
    paths += [entry["source"] for entry in data.get("plugins", [])]
    assert paths
    for value in paths:
        pure = PurePosixPath(value)
        assert not pure.is_absolute() and "\\" not in value and ":" not in value
        assert ".." not in pure.parts, value
        resolved = (installed / value).resolve()
        assert resolved == installed.resolve() or installed.resolve() in resolved.parents


def test_plugin_directory_holds_only_glue_components() -> None:
    """Structural zero-duplication check: no forked skills, personas, or standards."""
    files = {p.relative_to(PLUGIN).as_posix() for p in PLUGIN.rglob("*") if p.is_file()}
    expected = {"plugin.json", "marketplace.json", "assets/icon.svg",
                "rules/egm.mdc"}
    expected |= {f"agents/{name}.md" for name in REVIEWER_PERSONAS}
    assert files == expected
    assert not any(p.is_symlink() for p in PLUGIN.rglob("*"))


def test_logo_is_a_checked_mirror_of_the_shared_asset() -> None:
    """The install copy omits root assets/, so the logo is a verified mirror."""
    assert (PLUGIN / "assets/icon.svg").read_bytes() == (ROOT / "assets/icon.svg").read_bytes()


def shingles(text: str, size: int = 10) -> set[tuple[str, ...]]:
    words = re.findall(r"\w+", text.lower())
    return {tuple(words[i:i + size]) for i in range(len(words) - size + 1)}


def test_cursor_text_copies_no_shared_content() -> None:
    """Hash and 10-word overlap against every shared skill, persona, and resource."""
    shared_hashes: dict[str, Path] = {}
    shared_shingles: set[tuple[str, ...]] = set()
    for folder in SHARED:
        for source in (ROOT / folder).rglob("*"):
            if not source.is_file():
                continue
            shared_hashes[hashlib.sha256(source.read_bytes()).hexdigest()] = source
            if source.suffix in {".md", ".mdc", ".yaml", ".json"}:
                shared_shingles |= shingles(source.read_text(encoding="utf-8"))
    glue = [*PLUGIN.glob("agents/*.md"), *PLUGIN.glob("rules/*.mdc")]
    assert glue
    for path in glue:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest not in shared_hashes, f"{path} duplicates {shared_hashes.get(digest)}"
        overlap = shingles(path.read_text(encoding="utf-8")) & shared_shingles
        assert not overlap, f"{path} copies shared text: {' '.join(min(overlap))}"


def readonly_registration_errors(config: dict) -> list[str]:
    """Static mirror of the probe-verified registration contract.

    The pinned loader honors `permissionMode`; the documented `.cursor/agents`
    surface uses `readonly`. Both are required because they are read by
    different ingestion surfaces.
    """
    errors = []
    if config.get("permissionMode") != "readonly":
        errors.append("permissionMode is not readonly (pinned plugin loader)")
    if config.get("readonly") is not True:
        errors.append("readonly is not true (documented subagent surface)")
    if config.get("is_background") is not False:
        errors.append("is_background is not false")
    if config.get("model") != "inherit":
        errors.append("model is not inherit")
    return errors


VALID = {"name": "egm-x", "description": "x", "model": "inherit",
         "readonly": True, "permissionMode": "readonly", "is_background": False}


@pytest.mark.parametrize("override", [
    {"permissionMode": None},
    {"permissionMode": "default"},
    {"readonly": None},
    {"readonly": "true"},
    {"readonly": False, "permissionMode": "default"},
    {"is_background": True},
    {"model": "gpt-x"},
])
def test_write_probe_harness_rejects_writable_configurations(override: dict) -> None:
    config = {k: v for k, v in {**VALID, **override}.items() if v is not None}
    assert readonly_registration_errors(config)


def test_write_probe_harness_accepts_the_reference_configuration() -> None:
    assert readonly_registration_errors(VALID) == []


def test_every_registered_cursor_agent_is_readonly(installed: Path) -> None:
    """Fail on any agent in the selected directory that could register writable."""
    adapters = sorted((installed / ".cursor-plugin/agents").glob("*"))
    assert adapters
    for adapter in adapters:
        assert adapter.suffix == ".md", adapter
        assert readonly_registration_errors(frontmatter(adapter)) == [], adapter


@pytest.mark.parametrize("name", REVIEWER_PERSONAS)
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
        "Write each completed stage report before dispatching the next stage",
        "Do not include parent history or deliberation",
        "egm-lite Goldfish review", "generic child, which is not read-only",
        "State what is missing, how to remedy it",
        "completed and verified before the stop",
    ):
        assert contract in text, contract
    guide = " ".join((ROOT / "docs/cursor.md").read_text(encoding="utf-8").split())
    assert "EGM artifact directory: <path>" in guide
    assert "Grok Bot remains a separate, unverified surface" in guide
    assert "No complete Cursor workflow trace parser is supplied" in guide


def test_guide_states_no_drifting_component_counts() -> None:
    """Counts drift as skills and personas change; the tests derive them."""
    guide = (ROOT / "docs/cursor.md").read_text(encoding="utf-8")
    number = r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
    drift = re.findall(
        rf"\b{number}\s+(?:EGM\s+|shared\s+|read-only\s+)*"
        r"(?:skills|reviewers|reviewer registrations|personas)\b",
        guide, flags=re.IGNORECASE,
    )
    assert drift == []


def test_guide_keeps_experimental_status_and_unverified_gates() -> None:
    guide = (ROOT / "docs/cursor.md").read_text(encoding="utf-8")
    flat = " ".join(guide.split())
    assert "# Cursor integration (experimental)" in guide
    assert "Do not add Cursor to the supported-host table" in flat
    for gate in ("Installation", "Workflow", "Isolation"):
        assert re.search(rf"^\| {gate} \|.*\| Unverified", guide, re.MULTILINE), gate
    for field in ("Candidate commit", "Package checksum manifest", "Cursor version",
                  "Model identifier", "Run date"):
        assert field in guide, field
    steps = re.findall(r"^### Runbook step \d+", guide, re.MULTILINE)
    assert len(steps) >= 6
    assert flat.count("Model usage: requires your explicit authorization") >= 4
    harnesses = (ROOT / "docs/harnesses.md").read_text(encoding="utf-8")
    install = re.search(r"^## Install\n(.*?)^#", harnesses, re.MULTILINE | re.DOTALL)
    rows = [line for line in install.group(1).splitlines() if line.startswith("|")]
    assert rows and not any("Cursor" in row for row in rows)


NATIVE_PROBE = r'''
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
BUNDLE_PINS = {
    ("Darwin", "arm64"): "f6bd8dece34b56431ee74f1ac827e032d054381085e7da7088e85abdd1008330",
    ("Linux", "aarch64"): "90ec23826cd3089232b0b243b8954ac72fab0454dd86d7d71ddae29d39c75cd2",
}


@pytest.fixture
def native_loader():
    """Opt-in pinned loader, run without the CLI entry point or a model call."""
    bundle_path = os.environ.get("EGM_CURSOR_BUNDLE")
    if not bundle_path:
        pytest.skip("Set EGM_CURSOR_BUNDLE for the pinned native offline probe")
    bundle = Path(bundle_path).resolve()
    expected = BUNDLE_PINS.get((platform.system(), platform.machine()))
    assert expected, "The native loader probe has not been audited on this platform"
    assert hashlib.sha256(bundle.read_bytes()).hexdigest() == expected, (
        "Re-audit the private loader interface before changing this version pin"
    )

    def load(package: Path) -> dict:
        result = subprocess.run(
            [str(bundle.parent / "node"), "-e", NATIVE_PROBE, str(bundle), str(package)],
            capture_output=True, text=True, check=True, timeout=30,
        )
        return json.loads(result.stdout)
    return load


def test_installed_cursor_native_loader(installed: Path, native_loader) -> None:
    native = native_loader(installed)
    assert set(native["skills"]) == shared_skill_names()
    assert len(native["skills"]) == len(shared_skill_names())
    expected_agents = {
        frontmatter(ROOT / "agents" / f"{name}.md")["name"] for name in REVIEWER_PERSONAS
    }
    assert {agent["name"] for agent in native["agents"]} == expected_agents
    assert len(native["agents"]) == len(expected_agents)
    assert all(agent["permissionMode"] == "readonly" for agent in native["agents"])
    assert all(agent["model"] == "inherit" for agent in native["agents"])
    assert native["rules"] == [{"alwaysApply": True}]


def drop_field(package: Path, line: str) -> None:
    for adapter in (package / ".cursor-plugin/agents").glob("*.md"):
        text = adapter.read_text(encoding="utf-8")
        assert line + "\n" in text
        adapter.write_text(text.replace(line + "\n", ""), encoding="utf-8")


@pytest.mark.parametrize(("dropped", "registers_readonly"), [
    ("permissionMode: readonly", False),  # `readonly: true` alone
    ("readonly: true", True),             # `permissionMode` alone
])
def test_native_loader_honored_readonly_field(tmp_path: Path, native_loader,
                                              dropped: str,
                                              registers_readonly: bool) -> None:
    """Negative control: which field the pinned loader actually honors.

    This explains why both fields stay: each surface reads a different one.
    """
    package = copy_package(tmp_path / "field probe" / "egm")
    drop_field(package, dropped)
    native = native_loader(package)
    assert len(native["agents"]) == len(REVIEWER_PERSONAS)
    modes = {agent["permissionMode"] == "readonly" for agent in native["agents"]}
    assert modes == {registers_readonly}
