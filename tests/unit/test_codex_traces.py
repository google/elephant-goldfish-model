# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Offline regression tests for Codex command-read trace evidence."""

from pathlib import Path
import runpy
import shlex

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("parsed_command", "exit_code", "output", "expected"),
    [
        (
            lambda path: {
                "type": "unknown",
                "cmd": f"cat {shlex.quote(path)} "
                       f"{shlex.quote(str(Path(path).with_name('missing')))}",
            },
            1,
            "# Installed guide\n" + "guide content " * 20,
            True,
        ),
        (
            lambda path: {
                "type": "unknown",
                "cmd": f"pwd; rg --files -g 'README*' .; cat {shlex.quote(path)}",
            },
            0,
            "# Installed guide\n" + "guide content " * 20,
            True,
        ),
        (
            lambda path: {
                "type": "unknown",
                "cmd": f"cd {shlex.quote(str(Path(path).parent))} && cat {shlex.quote(path)}",
            },
            0,
            "# Installed guide\n" + "guide content " * 20,
            False,
        ),
        (
            lambda path: {
                "type": "unknown",
                "cmd": f"cat {shlex.quote(path)} | head",
            },
            0,
            "# Installed guide\n" + "guide content " * 20,
            False,
        ),
        (
            lambda path: {
                "type": "unknown",
                "cmd": f"cat {shlex.quote(path)} "
                       f"{shlex.quote(str(Path(path).with_name('missing')))}",
            },
            1,
            "cat: /missing: No such file or directory\n",
            False,
        ),
        (
            lambda path: {"type": "read", "path": str(path)},
            1,
            "# Installed guide\n" + "guide content " * 20,
            False,
        ),
        (
            lambda path: {"type": "read", "path": str(path)},
            0,
            "# Installed guide\n" + "guide content " * 20,
            True,
        ),
    ],
    ids=(
        "failed-cat-printed-file", "compound-cat-printed-file",
        "and-separated-cat-rejected", "piped-cat-rejected",
        "failed-cat-no-file-output", "failed-read", "successful-read",
    ),
)
def test_successful_reads_requires_native_trace_evidence(
    tmp_path: Path, parsed_command, exit_code: int, output: str,
    expected: bool,
) -> None:
    successful_reads = runpy.run_path(
        str(ROOT / "tests/integration/test_codex.py")
    )["successful_reads"]
    guide = tmp_path / "docs" / "codex.md"
    guide.parent.mkdir()
    guide.write_text("# Installed guide\n" + "guide content " * 20)
    command = parsed_command(str(guide))
    trace = [{
        "type": "event_msg",
        "payload": {
            "type": "item_completed",
            "item": {
                "type": "CommandExecution",
                "status": "failed" if exit_code else "completed",
                "exit_code": exit_code,
                "cwd": tmp_path.as_uri(),
                "parsed_cmd": [command],
                "aggregated_output": output,
            },
        },
    }]

    assert (guide.resolve() in successful_reads(trace)) is expected
