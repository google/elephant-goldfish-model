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


@pytest.mark.parametrize("prefix", [
    "", "cd other; ", ". setup.sh; ", "cat ignored\ncd other\n",
])
@pytest.mark.parametrize("include_output", [True, False])
def test_mixed_cat_paths_require_stable_cwd_and_actual_contents(
    tmp_path: Path, prefix: str, include_output: bool,
) -> None:
    successful_reads = runpy.run_path(
        str(ROOT / "tests/integration/test_codex.py")
    )["successful_reads"]
    persona = tmp_path / "persona.md"
    observations = tmp_path / "observations.md"
    persona.write_text("Independent persona content")
    observations.write_text("Observed failure evidence")
    trace = [{"type": "event_msg", "payload": {
        "type": "item_completed", "item": {
            "type": "CommandExecution", "status": "completed", "exit_code": 0,
            "cwd": tmp_path.as_uri(),
            "parsed_cmd": [{"type": "unknown", "cmd": (
                f"{prefix}cat {shlex.quote(str(persona))} observations.md; rg --files src"
            )}],
            "aggregated_output": (persona.read_text() + "\n" + observations.read_text()
                                  if include_output else "src/catalog.py"),
        },
    }}]
    expected = {persona, observations} if not prefix and include_output else set()
    assert successful_reads(trace) == expected
