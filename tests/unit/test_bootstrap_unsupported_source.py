# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Run the egm-bootstrap Unsupported Source Check command on sample trees."""

import os
from pathlib import Path
import re
import shutil
import subprocess

import pytest

REFERENCE = (Path(__file__).resolve().parents[2]
             / "skills/egm-bootstrap/references/unsupported-source-check.md")
FILES = ("src/a.xyz", "src/my file.xyz", "src/b.py", "test/runtests.xyz",
         "docs/index.md", "Makefile", ".env", ".github/ci.xyz",
         "node_modules/m/i.xyz", "third_party/v/v.xyz", "out/gen.xyz")


def inventory(root: Path) -> dict[str, int]:
  text = REFERENCE.read_text(encoding="utf-8")
  command = re.search(r"```sh\n(.*?)```", text, re.S).group(1)
  shell = shutil.which("bash")
  assert shell, "POSIX bash is required for the inventory command"
  completed = subprocess.run(
      [shell, "-c", command.replace("<path>", root.as_posix())],
      env={**os.environ, "GIT_CEILING_DIRECTORIES": str(root.parent)},
      text=True, capture_output=True, timeout=30, check=True,
  )
  counts = {}
  for line in completed.stdout.splitlines():
    count, extension, example = line.split(" ", 2)
    assert Path(root, example).is_file(), line
    counts[extension] = int(count)
  return counts


@pytest.mark.parametrize("use_git", [True, False])
def test_inventory_counts_extensions(tmp_path: Path, use_git: bool) -> None:
  root = tmp_path / "tree"
  for name in FILES:
    (root / name).parent.mkdir(parents=True, exist_ok=True)
    (root / name).write_text("x\n", encoding="utf-8")
  if use_git:
    assert shutil.which("git"), "git is required for the Git listing"
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / ".gitignore").write_text("out/\n", encoding="utf-8")
  # Test directories count; hidden, system, and Git-ignored paths do not.
  expected_xyz = 3 if use_git else 4
  assert inventory(root) == {".xyz": expected_xyz, ".py": 1, ".md": 1}
