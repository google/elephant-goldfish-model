# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Exercise distributable contents, unsafe paths, and reproducible output."""

import json
from pathlib import Path
import re
import runpy
import shutil
from xml.etree import ElementTree
import zipfile

import pytest
import yaml

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
               ".claude-plugin/hooks/run.sh", "assets/private.txt",
               "docs/experimental-host.md"):
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
    for skill in source.glob("skills/*/SKILL.md"):
      prefix = skill.parent.relative_to(source)
      metadata = yaml.safe_load(bundle.read((prefix / "agents/openai.yaml").as_posix()))
      interface = metadata["interface"]
      assert interface["display_name"]
      assert 25 <= len(interface["short_description"]) <= 64
      for field in ("icon_small", "icon_large"):
        icon = Path(interface[field])
        assert not icon.is_absolute() and ".." not in icon.parts
        data = bundle.read((prefix / icon).as_posix())
        assert data == (skill.parent / icon).read_bytes()
        assert ElementTree.fromstring(data).tag == "{http://www.w3.org/2000/svg}svg"
    assert "skills/egm-bootstrap/references/worker-return.schema.json" in names
    assert "resources/document_standards/feature-spec-standard.md" in names
    assert "agents/design_critic.md" in names
    assert "docs/codex.md" in names
    assert "docs/claude.md" in names
    assert "assets/icon.svg" in names
    for image in re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', bundle.read("README.md").decode()):
      assert image in names, f"Unbundled README image: {image}"
    assert not names.intersection({"CONTRIBUTING.md", "AI_POLICY.md", "TESTING.md",
                                   ".github/PULL_REQUEST_TEMPLATE.md"})
    assert not any(p.startswith("docs/designs/") for p in names)
    assert not any(p.startswith(("site/", "tests/", ".github/workflows/", ".agents/"))
                   or "hooks/" in p or p.endswith("test_scenarios.yaml")
                   or p.endswith("/TEST.md") or p.endswith("marketplace.json")
                   for p in names)
    assert "assets/private.txt" not in names
    assert "docs/experimental-host.md" not in names
    assert "docs/directory.md" not in names
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
  check_links = runpy.run_path(str(ROOT / "tests/unit/test_link_integrity.py"))[
      "test_relative_markdown_links_resolve_on_disk"
  ]
  check_links(first)


@pytest.mark.parametrize("skill,base,facet", [
    ("bootstrap", "#1b6ef3", "#7cacf8"),
    ("brainstorm", "#1b6ef3", "#7cacf8"),
    ("draft", "#1b6ef3", "#7cacf8"),
    ("resolve", "#1b6ef3", "#7cacf8"),
    ("drift_report", "#e86e00", "#ff8d41"),
    ("review", "#e86e00", "#ff8d41"),
    ("review_loop", "#e86e00", "#ff8d41"),
])
def test_skill_icon_and_host_palette_match(skill: str, base: str, facet: str) -> None:
  root = ROOT / "skills" / f"egm-{skill.replace('_', '-')}"
  metadata = yaml.safe_load((root / "agents/openai.yaml").read_text())["interface"]
  assert metadata["brand_color"].lower() == base
  for field in ("icon_small", "icon_large"):
    svg = ElementTree.parse(root / metadata[field]).getroot()
    assert svg.get("viewBox") == "0 0 24 24"
    assert svg.findtext("{http://www.w3.org/2000/svg}title")
    colors = {
        value.lower() for element in svg.iter()
        for key, value in element.attrib.items()
        if key in ("fill", "stroke") and value != "none"
    }
    assert colors == {base, facet}


@pytest.mark.parametrize("target", ["claude", "openai"])
def test_bundles_readme_images(source: Path, tmp_path: Path, target: str) -> None:
  image_dir = source / "docs/assets"
  image_dir.mkdir(exist_ok=True)
  image = image_dir / "readme-header.svg"
  image.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
  (image_dir / "private.txt").write_text("must not ship")
  readme = source / "README.md"
  readme.write_text(readme.read_text() + '\n![Header](docs/assets/readme-header.svg)\n')
  _, archive = build(source, target, tmp_path / "output")
  with zipfile.ZipFile(archive) as bundle:
    assert bundle.read("docs/assets/readme-header.svg") == image.read_bytes()
    assert "docs/assets/private.txt" not in bundle.namelist()


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


@pytest.mark.parametrize("key", ["composerIcon", "logo"])
def test_rejects_missing_openai_interface_icons(
    source: Path, tmp_path: Path, key: str,
) -> None:
  path = source / "plugin.json"
  manifest = json.loads(path.read_text())
  del manifest["extensions"]["com.openai"]["interface"][key]
  path.write_text(json.dumps(manifest))
  with pytest.raises(ValueError, match=f"Missing OpenAI interface reference: {key}"):
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


@pytest.mark.parametrize("target", ["claude", "openai"])
@pytest.mark.parametrize("missing", [
    "skills",
    "skills/egm-bootstrap/SKILL.md",
    "skills/egm-brainstorm/SKILL.md",
    "skills/egm-draft/SKILL.md",
    "skills/egm-drift-report/SKILL.md",
    "skills/egm-resolve/SKILL.md",
    "skills/egm-review/SKILL.md",
    "skills/egm-review-loop/SKILL.md",
    "skills/egm-review/agents/openai.yaml",
    "skills/egm-review/assets/icon.svg",
    "skills/egm-bootstrap/references/worker-return.schema.json",
    "skills/egm-draft/references/design_doc.md",
    "agents/design_critic.md",
    "resources/execution_instructions.md",
    "resources/document_standards/zoom-out-standard.md",
    "docs/harnesses.md",
])
def test_incomplete_source_fails_before_output(
    source: Path, tmp_path: Path, target: str, missing: str,
) -> None:
  path = source / missing
  if path.is_dir():
    shutil.rmtree(path)
  else:
    path.unlink()
  output = tmp_path / "output"
  with pytest.raises(ValueError, match="Missing required file"):
    build(source, target, output)
  assert not output.exists()


@pytest.mark.parametrize("target", ["claude", "openai"])
@pytest.mark.parametrize("suffix", ["", ".zip"])
def test_rejects_dangling_output_symlinks(
    source: Path, tmp_path: Path, target: str, suffix: str,
) -> None:
  output = tmp_path / "output"
  output.mkdir()
  outside = tmp_path / "outside"
  link = output / f"egm-{target}{suffix}"
  link.symlink_to(outside, target_is_directory=not suffix)
  with pytest.raises(ValueError, match="already exists"):
    build(source, target, output)
  assert link.is_symlink()
  assert not outside.exists()
  assert list(output.iterdir()) == [link]


@pytest.mark.parametrize("target", ["claude", "openai"])
@pytest.mark.parametrize("claim", ["file", "dangling-symlink", "symlink"])
def test_archive_claimed_after_preflight_is_not_overwritten(
    source: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    target: str, claim: str,
) -> None:
  output = tmp_path / "output"
  archive = output / f"egm-{target}.zip"
  outside = tmp_path / "outside.zip"
  if claim == "symlink":
    outside.write_bytes(b"outside file must not change")
  original_zipfile = zipfile.ZipFile

  def claim_archive(*args, **kwargs):
    if claim != "file":
      archive.symlink_to(outside)
    else:
      archive.write_bytes(b"another build owns this file")
    return original_zipfile(*args, **kwargs)

  monkeypatch.setattr(zipfile, "ZipFile", claim_archive)
  with pytest.raises(FileExistsError):
    build(source, target, output)
  if claim != "file":
    assert archive.is_symlink()
    if claim == "symlink":
      assert outside.read_bytes() == b"outside file must not change"
    else:
      assert not outside.exists()
  else:
    assert archive.read_bytes() == b"another build owns this file"
  assert not list(output.glob(".egm-*"))


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
