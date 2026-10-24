# Copyright 2026 Google LLC. SPDX-License-Identifier: Apache-2.0
"""Version agreement, release identities, and archive checksum contracts."""

import hashlib
import json
from pathlib import Path
import runpy
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def release(monkeypatch: pytest.MonkeyPatch) -> dict:
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return runpy.run_path(str(ROOT / "scripts/prepare_release.py"))


@pytest.mark.parametrize("tag", ["0.1.0", "v01.1.0", "v0.1.0-rc.1", "v0.1.0;echo bad"])
def test_reject_invalid_tag(release: dict, tag: str) -> None:
    with pytest.raises(ValueError, match="Tag must"):
        release["version_for_tag"](ROOT, tag)


def test_release_version_matches_source(release: dict) -> None:
    version = json.loads((ROOT / "plugin.json").read_text())["version"]
    assert release["version_for_tag"](ROOT, f"v{version}") == version


def test_reject_host_version_drift(release: dict, tmp_path: Path) -> None:
    for name in ("plugin.json", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json"):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"version": "0.1.0"}))
    (tmp_path / ".codex-plugin/plugin.json").write_text('{"version":"0.2.0"}')
    with pytest.raises(ValueError, match="codex-plugin"):
        release["version_for_tag"](tmp_path, "v0.1.0")


def test_prepare_exact_archives(release: dict, tmp_path: Path) -> None:
    version = json.loads((ROOT / "plugin.json").read_text())["version"]
    destination = tmp_path / "release"
    commit = "a" * 40
    release["prepare"](ROOT, f"v{version}", destination, commit)
    sums = (destination / "SHA256SUMS").read_text().splitlines()
    assert len(sums) == 2
    for line in sums:
        digest, name = line.split("  ")
        assert name in {f"egm-claude-{version}.zip", f"egm-openai-{version}.zip"}
        archive = destination / name
        assert hashlib.sha256(archive.read_bytes()).hexdigest() == digest
        with zipfile.ZipFile(archive) as bundle:
            assert bundle.testzip() is None
            assert json.loads(bundle.read("plugin.json"))["version"] == version
    assert commit in (destination / "RELEASE_NOTES.md").read_text()
    with pytest.raises(FileExistsError):
        release["prepare"](ROOT, f"v{version}", destination, commit)


def test_reject_invalid_commit_without_writing(release: dict, tmp_path: Path) -> None:
    version = json.loads((ROOT / "plugin.json").read_text())["version"]
    destination = tmp_path / "release"
    with pytest.raises(ValueError, match="Git SHA"):
        release["prepare"](ROOT, f"v{version}", destination, "HEAD")
    assert not destination.exists()
