# SPDX-License-Identifier: Apache-2.0
"""Disposable Git projects with known defects for native review tests."""

from pathlib import Path
import subprocess
import sys


def git(root: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True,
    ).stdout


def make_project(root: Path, mode: str, *, ignore_reports: bool = True) -> dict:
    root.mkdir()
    git(root, "init", "-b", "trunk")
    git(root, "config", "user.name", "Fixture")
    git(root, "config", "user.email", "fixture@example.invalid")
    (root / ".gitignore").write_text(
        ("reports/\n" if ignore_reports else "") + "CLAUDE.md\n__pycache__/\n"
    )
    (root / "README.md").write_text(
        "# Fixture\nRun local checks: `python3 -B -m unittest -v`.\n"
        "No dependencies, build, lint, typecheck or generation steps.\n"
    )
    good = 'def can_view(owner, user):\n    """Only the owner may view a record."""\n    return owner == user\n'
    (root / "access.py").write_text(good)
    (root / "total.py").write_text('def total(items):\n    """Sum every item, including the last."""\n    return sum(items)\n')
    (root / "test_project.py").write_text(
        'import unittest\nfrom access import can_view\nfrom total import total\n\n'
        'class Checks(unittest.TestCase):\n'
        '    def test_access(self):\n'
        '        self.assertTrue(can_view("a", "a"))\n'
        '        self.assertFalse(can_view("a", "b"))\n'
        '    def test_total(self):\n'
        '        self.assertEqual(total([2, 3]), 5)\n'
        '        self.assertEqual(total([]), 0)\n'
    )
    git(root, "add", ".")
    git(root, "-c", "core.hooksPath=/dev/null", "commit", "-m", "Fixture baseline")
    if mode == "review":
        (root / "access.py").write_text(good.replace("owner == user", "owner != user"))
        git(root, "add", "access.py")
        (root / "access.py").write_text(good)
        (root / "currency ü.py").write_text(
            'def cents(dollars):\n    """Convert whole dollar amounts to cents."""\n    return int(dollars)\n'
        )
    else:
        (root / "total.py").write_text(
            'def total(items):\n    """Sum every item, including the last."""\n'
            '    return sum(items[:-1])\n'
        )
    return {
        "head": git(root, "rev-parse", "HEAD"),
        "index": git(root, "ls-files", "--stage", "-z"),
        "files": {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()},
    }


def assert_preserved(root: Path, before: dict, mode: str) -> None:
    assert git(root, "rev-parse", "HEAD") == before["head"], "HEAD changed"
    assert git(root, "ls-files", "--stage", "-z") == before["index"], "Index changed"
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*")
              if p.is_file() and p.relative_to(root).parts[0] not in {".git", "reports"}
              and p.name != "CLAUDE.md"}
    assert actual == set(before["files"]), "Unexpected project files added or removed"
    for name, content in before["files"].items():
        assert not (root / name).is_symlink(), f"Source replaced by symlink: {name}"
        if mode == "fix" and name == "total.py":
            continue
        assert (root / name).read_bytes() == content, f"Unexpected source edit: {name}"
    if mode == "fix":
        result = subprocess.run(
            [sys.executable, "-B", "-m", "unittest", "-v"], cwd=root,
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
