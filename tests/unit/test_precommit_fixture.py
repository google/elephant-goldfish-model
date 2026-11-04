# SPDX-License-Identifier: Apache-2.0
"""Prove the native fixtures exercise different Git layers and real failures."""

from pathlib import Path
import runpy
import subprocess
import sys

fixture = runpy.run_path(str(Path(__file__).resolve().parents[1] / "integration/precommit_fixture.py"))


def test_staged_defect_is_hidden_by_working_copy(tmp_path: Path) -> None:
    root = tmp_path / "project"
    fixture["make_project"](root, "review")
    git = fixture["git"]
    assert b"owner != user" in git(root, "show", ":access.py")
    assert b"owner == user" in (root / "access.py").read_bytes()
    assert git(root, "diff", "HEAD", "--", "access.py") == b""
    assert git(root, "diff", "--cached", "--", "access.py")
    assert git(root, "diff", "--", "access.py")
    assert "currency ü.py".encode() in git(root, "ls-files", "--others", "--exclude-standard", "-z")
    result = subprocess.run([sys.executable, "-B", "-m", "unittest"], cwd=root, capture_output=True)
    assert result.returncode == 0, result.stderr


def test_fix_fixture_fails_until_source_is_corrected(tmp_path: Path) -> None:
    root = tmp_path / "project"
    before = fixture["make_project"](root, "fix")
    command = [sys.executable, "-B", "-m", "unittest"]
    failed = subprocess.run(command, cwd=root, capture_output=True)
    assert failed.returncode != 0 and b"2 != 5" in failed.stderr
    p = root / "total.py"
    p.write_text(p.read_text().replace("items[:-1]", "items"))
    fixture["assert_preserved"](root, before, "fix")
