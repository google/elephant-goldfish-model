# SPDX-License-Identifier: Apache-2.0
"""Negative controls for the diagnosis workflow's native evidence checks."""

import json
from pathlib import Path
import runpy

import pytest

checks = runpy.run_path(str(
    Path(__file__).resolve().parents[1] / "integration/diagnosis_checks.py"
))


def record(role: str, *blocks: dict) -> dict:
    return {"type": role, "message": {"content": list(blocks)}}


def raw(*events: dict) -> str:
    return "\n".join(json.dumps(e) for e in events)


@pytest.mark.parametrize("case", ["success", "error", "empty", "unrelated", "missing"])
def test_diagnosis_reads_require_correlated_success(case: str, tmp_path: Path) -> None:
    persona = tmp_path / "persona.md"
    read = record("assistant", {"type": "tool_use", "name": "Read", "id": "read1",
                                "input": {"file_path": str(persona)}})
    response = record("user", {
        "type": "tool_result", "tool_use_id": "other" if case == "unrelated" else "read1",
        "content": " \n" if case == "empty" else "Persona\u2028text",
        "is_error": case == "error",
    })
    trace = raw(read) if case == "missing" else raw(read, response)
    reads = checks["claude_reads"](trace)
    assert (persona.resolve() in reads) == (case == "success")


@pytest.mark.parametrize("handback", [False, True])
def test_native_diagnosis_answer(handback: bool) -> None:
    answer = "Status: complete\nRanked candidates: insufficient evidence"
    block = ({"type": "tool_use", "name": "SubagentHandback", "id": "final",
              "input": {"message": answer}} if handback
             else {"type": "text", "text": answer})
    assert checks["claude_diagnosis_answer"](raw(record("assistant", block))) == answer


@pytest.mark.parametrize("case", [
    "write", "shell", "missing", "only_narration", "after_handback", "denied_handback",
    "empty_handback", "malformed_handback",
])
def test_rejects_missing_or_invalid_native_diagnosis(case: str) -> None:
    final = {"type": "tool_use", "name": "SubagentHandback", "id": "final",
             "input": {"message": "Status: complete"}}
    text = {"type": "text", "text": "I will investigate."}
    read = {"type": "tool_use", "name": "Read", "id": "read1",
            "input": {"file_path": "/source.py"}}
    traces = {
        "write": raw(record("assistant", {**read, "name": "Write"})),
        "shell": raw(record("assistant", {**read, "name": "Bash"})),
        "missing": "",
        "only_narration": raw(record("assistant", text), record("assistant", read)),
        "after_handback": raw(record("assistant", final), record("assistant", text)),
        "denied_handback": raw(record("assistant", final), record("user", {
            "type": "tool_result", "tool_use_id": "final", "is_error": True,
            "content": "Rejected",
        })),
        "empty_handback": raw(record("assistant", {**final, "input": {"message": ""}})),
        "malformed_handback": raw(record("assistant", {**final, "input": "complete"})),
    }
    with pytest.raises(AssertionError):
        checks["claude_diagnosis_answer"](traces[case])
