# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Check the read-only install diagnostic against whole and partial installs."""

import json
from pathlib import Path
import runpy
import shutil

import pytest

ROOT = Path(__file__).resolve().parents[2]
main = runpy.run_path(str(ROOT / "scripts/check_install.py"))["main"]
PLUGIN = ("plugin.json", "LICENSE", "README.md", "skills", "agents", "resources",
          "docs", "assets")


def install(tmp_path: Path, names: tuple[str, ...] = PLUGIN) -> Path:
  root = tmp_path / "egm"
  root.mkdir()
  for name in names:
    source = ROOT / name
    if source.is_dir():
      shutil.copytree(source, root / name)
    else:
      shutil.copyfile(source, root / name)
  return root


def run(root: Path, capsys: pytest.CaptureFixture[str], *flags: str) -> tuple[int, str]:
  code = main(["--root", str(root), "--no-exec", *flags])
  return code, capsys.readouterr().out


def test_complete_install_passes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
  code, out = run(install(tmp_path), capsys)
  assert code == 0
  assert "[FAIL]" not in out
  assert "[PASS] resource: All" in out


def test_skills_only_install_names_missing_resources(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
  code, out = run(install(tmp_path, ("plugin.json", "skills")), capsys)
  assert code == 1
  assert "Missing agents/style.md" in out
  assert "Missing resources/execution_instructions.md" in out
  assert out.count("fix: Install the whole plugin") == 1


def test_missing_manifest_fails(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
  root = install(tmp_path)
  (root / "plugin.json").unlink()
  code, out = run(root, capsys)
  assert code == 1
  assert "Missing plugin.json" in out


def test_truncated_skill_fails(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
  root = install(tmp_path)
  skill = next(root.glob("skills/*/SKILL.md"))
  skill.write_text("no frontmatter here\n")
  code, out = run(root, capsys)
  assert code == 1
  assert f"{skill.relative_to(root)} lacks name or description" in out


def test_symlinked_resource_warns_without_failing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
  root = install(tmp_path)
  target = tmp_path / "elsewhere"
  shutil.move(root / "agents", target)
  (root / "agents").symlink_to(target, target_is_directory=True)
  code, out = run(root, capsys)
  assert code == 0
  assert "[WARN] resource: Symlinked path agents/" in out


def test_undetectable_capabilities_stay_unknown(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
  _, out = run(install(tmp_path), capsys)
  assert "[UNKNOWN] isolation:" in out
  assert "[PASS] isolation" not in out


def test_diagnostic_changes_nothing_and_prints_no_environment(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch,
) -> None:
  monkeypatch.setenv("EGM_FAKE_SECRET", "s3cr3t-value")
  root = install(tmp_path)
  before = sorted((p.relative_to(root), p.stat().st_mtime_ns) for p in root.rglob("*"))
  _, out = run(root, capsys, "--json")
  after = sorted((p.relative_to(root), p.stat().st_mtime_ns) for p in root.rglob("*"))
  assert before == after
  assert "s3cr3t-value" not in out


def test_json_output_is_machine_readable(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
  code, out = run(install(tmp_path, ("plugin.json",)), capsys, "--json")
  report = json.loads(out)
  assert code == 1
  assert report["ok"] is False
  expected_version = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))["version"]
  assert report["version"] == expected_version
  assert {item["status"] for item in report["findings"]} >= {"PASS", "FAIL", "UNKNOWN"}


def test_missing_skills_fails(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
  root = install(tmp_path)
  shutil.rmtree(root / "skills")
  code, out = run(root, capsys)
  assert code == 1
  assert "No skills found" in out


def test_host_version_failure_falls_back_to_unknown(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch,
) -> None:
  import subprocess
  monkeypatch.setattr(shutil, "which", lambda cmd: "/bin/fake" if cmd == "claude" else None)
  class FakeCompletedProcess:
    returncode = 1
    stdout = ""
    stderr = "error: command failed"
  monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: FakeCompletedProcess())
  main(["--root", str(install(tmp_path))])
  out = capsys.readouterr().out
  assert "[UNKNOWN] host: Claude Code: `--version` exited with code 1" in out
