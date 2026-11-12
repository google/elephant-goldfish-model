# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Devin packages retain shared content without contributor instruction leakage."""
import json
from pathlib import Path
import runpy
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def test_devin_runtime(tmp_path):
    build = runpy.run_path(str(ROOT / "scripts/pack_plugin.py"))["build"]
    runtime, archive = build(ROOT, "devin", tmp_path)
    assert (runtime / "AGENTS.md").read_bytes() == (ROOT / "adapters/devin/AGENTS.md").read_bytes()
    assert (runtime / "AGENTS.md").read_bytes() != (ROOT / "AGENTS.md").read_bytes()
    assert not (runtime / ".claude-plugin").exists()
    for pattern in ("skills/*/SKILL.md", "agents/*.md", "resources/document_standards/*.md"):
        sources = list(ROOT.glob(pattern))
        assert sources
        for source in sources:
            assert (runtime / source.relative_to(ROOT)).read_bytes() == source.read_bytes()
    assert (runtime / "docs/devin.md").is_file()
    canonical = json.loads((ROOT / "plugin.json").read_text())
    native = json.loads((runtime / ".devin-plugin/plugin.json").read_text())
    for key, value in native.items():
        assert canonical[key] == value
    with zipfile.ZipFile(archive) as package:
        assert package.read("AGENTS.md") == (runtime / "AGENTS.md").read_bytes()
        assert "adapters/devin/AGENTS.md" not in package.namelist()
        assert not any(name.startswith(("tests/", ".git/")) for name in package.namelist())
