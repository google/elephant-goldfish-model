# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Exercise distributable contents, unsafe paths, and reproducible output."""

import json
from pathlib import Path
import runpy
import shutil
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[2]
build = runpy.run_path(str(ROOT / "scripts/pack_plugin.py"))["build"]


@pytest.fixture
def source(tmp_path: Path) -> Path:
  root = tmp_path / "source"
  root.mkdir()
  for name in ("plugin.json", "LICENSE", "README.md", "TESTING.md",
               "CONTRIBUTING.md", "AI_POLICY.md"):
    shutil.copyfile(ROOT / name, root / name)
  (root / ".github").mkdir()
  shutil.copyfile(ROOT / ".github/PULL_REQUEST_TEMPLATE.md",
                  root / ".github/PULL_REQUEST_TEMPLATE.md")
  for name in ("skills", "agents", "resources", "docs", "assets",
               ".claude-plugin", ".codex-plugin"):
    shutil.copytree(ROOT / name, root / name)
  return root


@pytest.mark.parametrize("target", ["claude", "openai"])
def test_runtime_bundle_is_complete_and_reproducible(
    source: Path, tmp_path: Path, target: str,
) -> None:
  for name in ("site/font.woff2", "tests/secret.txt", ".github/workflows/a.yml",
               ".agents/plugins/marketplace.json", "hooks/run.sh",
               ".claude-plugin/hooks/run.sh", "assets/private.txt"):
    file = source / name
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text("must not ship")
  first, archive = build(source, target, tmp_path / "first")
  _, repeated = build(source, target, tmp_path / "second")
  assert archive.read_bytes() == repeated.read_bytes()
  with zipfile.ZipFile(archive) as bundle:
    assert bundle.testzip() is None
    names = set(bundle.namelist())
    assert len([p for p in names if p.endswith("/SKILL.md")]) == 7
    assert "skills/egm_bootstrap/references/worker-return.schema.json" in names
    assert "resources/document_standards/feature-spec-standard.md" in names
    assert "agents/design_critic.md" in names
    assert "docs/codex.md" in names
    assert "docs/claude.md" in names
    assert "assets/icon.svg" in names
    assert "CONTRIBUTING.md" in names
    assert "AI_POLICY.md" in names
    assert ".github/PULL_REQUEST_TEMPLATE.md" in names
    assert not any(p.startswith(("site/", "tests/", ".github/workflows/", ".agents/"))
                   or "hooks/" in p or p.endswith("test_scenarios.yaml")
                   or p.endswith("/TEST.md") or p.endswith("marketplace.json")
                   for p in names)
    assert "assets/private.txt" not in names
    assert (".claude-plugin/plugin.json" in names) == (target == "claude")
    assert (".claude-plugin/icon.png" in names) == (target == "claude")
    assert (".claude-plugin/agents/style.md" in names) == (target == "claude")
    assert (".codex-plugin/plugin.json" in names) == (target == "openai")
    for info in bundle.infolist():
      assert not Path(info.filename).is_absolute()
      assert ".." not in Path(info.filename).parts
      assert info.date_time == (1980, 1, 1, 0, 0, 0)
      assert info.external_attr >> 16 == 0o100644
      assert bundle.read(info) == (first / info.filename).read_bytes()


@pytest.mark.parametrize("directory", [False, True])
def test_rejects_symlinked_runtime_paths(
    source: Path, tmp_path: Path, directory: bool,
) -> None:
  victim = source / ("agents" if directory else "assets/icon.svg")
  outside = tmp_path / "outside"
  shutil.move(str(victim), outside)
  victim.symlink_to(outside, target_is_directory=directory)
  with pytest.raises(ValueError, match="Symlink"):
    build(source, "openai", tmp_path / "output")


@pytest.mark.parametrize("reference", ["../escape.svg", "/tmp/icon.svg",
                                       "./assets/missing.svg"])
def test_rejects_escaping_or_missing_manifest_assets(
    source: Path, tmp_path: Path, reference: str,
) -> None:
  path = source / "plugin.json"
  manifest = json.loads(path.read_text())
  manifest["extensions"]["com.openai"]["interface"]["logo"] = reference
  path.write_text(json.dumps(manifest))
  with pytest.raises(ValueError, match="Unbundled"):
    build(source, "openai", tmp_path / "output")


def test_refuses_hooks_and_overwrites(source: Path, tmp_path: Path) -> None:
  output = tmp_path / "output"
  build(source, "claude", output)
  with pytest.raises(ValueError, match="already exists"):
    build(source, "claude", output)
  path = source / ".claude-plugin/plugin.json"
  manifest = json.loads(path.read_text())
  manifest["hooks"] = {"PreToolUse": []}
  path.write_text(json.dumps(manifest))
  with pytest.raises(ValueError, match="hooks"):
    build(source, "claude", tmp_path / "other")


def test_refuses_portable_hook_override(source: Path, tmp_path: Path) -> None:
  path = source / "plugin.json"
  manifest = json.loads(path.read_text())
  manifest["extensions"]["com.openai"]["hooks"] = "./hooks/hooks.json"
  path.write_text(json.dumps(manifest))
  with pytest.raises(ValueError, match="hooks"):
    build(source, "openai", tmp_path / "output")


@pytest.mark.parametrize("field", ["apps", "mcpServers"])
def test_refuses_unbundled_services(source: Path, tmp_path: Path, field: str) -> None:
  path = source / "plugin.json"
  manifest = json.loads(path.read_text())
  manifest["extensions"]["com.openai"][field] = "./missing.json"
  path.write_text(json.dumps(manifest))
  with pytest.raises(ValueError, match="dependencies"):
    build(source, "openai", tmp_path / "output")


def test_published_claude_runtime_is_current(tmp_path: Path) -> None:
  """The directory subfolder must contain exactly the reviewed runtime."""
  generated, _ = build(ROOT, "claude", tmp_path)
  published = ROOT / "distributions/claude"

  def contents(folder: Path) -> dict[str, bytes]:
    return {p.relative_to(folder).as_posix(): p.read_bytes()
            for p in folder.rglob("*") if p.is_file()}

  assert contents(published) == contents(generated), (
      "Regenerate distributions/claude with scripts/pack_plugin.py"
  )
