# SPDX-License-Identifier: Apache-2.0
"""Negative controls for native precommit evidence."""

import json
from pathlib import Path
import runpy

import pytest

checks = runpy.run_path(str(Path(__file__).resolve().parents[1] / "integration/precommit_trace.py"))


def event(role, **block):
    return json.dumps({"type": role, "message": {"content": [block]}})


def test_summary_field_ignores_per_round_status():
    report = """# Precommit review report

- Review: complete (2 rounds)
- Validation: passed (working copy)
- Outcome: clean

## Round 1
- Review: complete with findings.
- Validation: failed.
"""
    assert checks["summary_field"](report, "Review") == "complete"
    assert checks["summary_field"](report, "Validation") == "passed"
    assert checks["summary_field"](report, "Outcome") == "clean"


@pytest.mark.parametrize("case", ["ok", "missing", "unrelated", "error", "empty"])
def test_read_requires_correlated_nonempty_success(case, tmp_path):
    path = tmp_path / "source.py"
    path.write_text("source\u2028code")
    trace = event("assistant", type="tool_use", name="Read", id="r", input={"file_path": str(path)})
    if case != "missing":
        trace += "\n" + event("user", type="tool_result", tool_use_id="x" if case == "unrelated" else "r",
                              is_error=case == "error", content=" " if case == "empty" else "source\u2028code")
    assert (path in checks["successful_reads"](trace)) == (case == "ok")


@pytest.mark.parametrize("case", ["full", "partial", "chunks", "wrong_content"])
def test_read_requires_all_source_lines(case, tmp_path):
    path = tmp_path / "source.py"
    path.write_text("first\nsecond\n")
    trace = event("assistant", type="tool_use", name="Read", id="r1",
                  input={"file_path": str(path), "offset": 1, "limit": 1 if case == "partial" else 2})
    trace += "\n" + event("user", type="tool_result", tool_use_id="r1",
                           content="1\tfirst" + ("\n2\tsecond" if case == "full" else "\n2\twrong" if case == "wrong_content" else ""))
    if case == "chunks":
        trace += "\n" + event("assistant", type="tool_use", name="Read", id="r2", input={"file_path": str(path), "offset": 2})
        trace += "\n" + event("user", type="tool_result", tool_use_id="r2", content="2\tsecond")
    assert (path in checks["successful_reads"](trace)) == (case in {"full", "chunks"})


@pytest.mark.parametrize("handback", [False, True])
def test_valid_completion(handback):
    answer = "Status: complete\nno findings"
    trace = (event("assistant", type="tool_use", name="SubagentHandback", id="h", input={"message": answer})
             if handback else event("assistant", type="text", text=answer))
    assert checks["child_answer"](trace) == answer


@pytest.mark.parametrize("case", ["write", "shell", "empty", "narration", "after_handback", "denied", "malformed"])
def test_invalid_completion(case):
    handback = event("assistant", type="tool_use", name="SubagentHandback", id="h", input={"message": "complete"})
    read = event("assistant", type="tool_use", name="Read", id="r", input={"file_path": "/source"})
    traces = {
        "write": event("assistant", type="tool_use", name="Write", id="w", input={}),
        "shell": event("assistant", type="tool_use", name="Bash", id="b", input={}),
        "empty": "",
        "narration": event("assistant", type="text", text="I will review") + "\n" + read,
        "after_handback": handback + "\n" + read,
        "denied": handback + "\n" + event("user", type="tool_result", tool_use_id="h", is_error=True, content="denied"),
        "malformed": event("assistant", type="tool_use", name="SubagentHandback", id="h", input="bad"),
    }
    with pytest.raises(AssertionError):
        checks["child_answer"](traces[case])


@pytest.mark.parametrize("value", ["not clean: validation not run", "incomplete", "findings remain"])
def test_non_clean_outcome_is_not_clean(value):
    assert checks["field"](f"- **Outcome:** {value}", "Outcome") != "clean"


@pytest.mark.parametrize("value,expected", [("clean.", "clean"), ("findings remain.", "findings remain")])
def test_status_allows_terminal_punctuation(value, expected):
    assert checks["field"](f"Outcome: {value}", "Outcome") == expected


@pytest.mark.parametrize("case", ["ok", "missing", "no_result", "unrelated", "before_review", "after_certification", "echo"])
def test_validation_requires_real_ordered_checks(case):
    def command(key, text="python3 -B -m unittest -v"):
        return event("assistant", type="tool_use", name="Bash", id=key, input={"command": text})
    def result(key, ok):
        return event("user", type="tool_result", tool_use_id=key, is_error=not ok,
                     content="Ran 2 tests in 0.1s\n\n" + ("OK\n" if ok else "FAILED (failures=1)\n"))
    a1 = event("assistant", type="tool_use", name="Agent", id="a1", input={})
    done = event("user", type="tool_result", tool_use_id="a1", content="finding")
    a2 = event("assistant", type="tool_use", name="Agent", id="a2", input={})
    passed = [command("pass", 'echo "python3 -B -m unittest -v"' if case == "echo" else "python3 -B -m unittest -v")]
    if case != "no_result":
        passed += [result("other" if case == "unrelated" else "pass", True)]
    if case == "missing":
        passed = []
    before, after = (passed, []) if case == "before_review" else ([], passed)
    tail = []
    if case == "after_certification":
        tail, after = after, []
    raw = "\n".join([command("fail"), result("fail", False), *before, a1, done, *after, a2, *tail])
    if case == "ok":
        checks["assert_validation"](raw, "fix")
    else:
        with pytest.raises(AssertionError):
            checks["assert_validation"](raw, "fix")


@pytest.mark.parametrize("case", ["ok", "failed", "running", "compound", "missing", "nonempty"])
def test_empty_codex_patch_requires_completed_literal_read(case, tmp_path):
    p = tmp_path / "empty.patch"
    if case != "missing":
        p.write_text("not empty" if case == "nonempty" else "")
    cmd = f"cat '{p}'" + ("; true" if case == "compound" else "")
    trace = [{"type": "event_msg", "payload": {"type": "item_completed", "item": {
        "type": "CommandExecution", "status": "running" if case == "running" else "completed",
        "exit_code": 1 if case == "failed" else 0,
        "parsed_cmd": [{"type": "read", "cmd": cmd}], "aggregated_output": "",
    }}}]
    assert (p in checks["codex_full_reads"](trace)) == (case == "ok")


@pytest.mark.parametrize("case", ["full", "truncated", "head"])
def test_codex_read_requires_complete_contents(case, tmp_path):
    p = tmp_path / "source.txt"
    p.write_text("first\nsecond\n")
    trace = [{"type": "event_msg", "payload": {"type": "item_completed", "item": {
        "type": "CommandExecution", "status": "completed", "exit_code": 0,
        "parsed_cmd": [{"type": "read", "cmd": f"{'head -1' if case == 'head' else 'cat'} '{p}'"}],
        "aggregated_output": "first\nsecond\n" if case == "full" else "first\n",
    }}}]
    assert (p in checks["codex_full_reads"](trace)) == (case == "full")


@pytest.mark.parametrize("case", ["both", "reversed", "coverage_only", "wrong_layer", "unstaged", "description_only", "one_defect"])
def test_seeded_findings_cannot_be_satisfied_by_coverage(case):
    access = "1. access.py:3 (staged) - != inverts access for non-owners."
    currency = "2. currency ü.py:3 (untracked) - dollars need multiplication by 100."
    text = "Coverage: access.py (staged), currency ü.py (untracked)\nFindings:\n"
    if case == "both":
        text += access + "\n" + currency
    elif case == "reversed":
        text += "1. access.py:3 (staged index) reverses the owner check.\n" + currency
    elif case == "wrong_layer":
        text += access.replace("staged", "working copy") + "\n" + currency
    elif case == "unstaged":
        text += access.replace("staged", "unstaged") + "\n" + currency
    elif case == "description_only":
        text += access.replace("staged", "unstaged") + " The index is correct.\n" + currency
    elif case == "one_defect":
        text += currency
    if case in {"both", "reversed"}:
        checks["assert_seeded_findings"](text)
    else:
        with pytest.raises(AssertionError):
            checks["assert_seeded_findings"](text)


@pytest.mark.parametrize("cmd,valid", [
    ("python3 -B -m unittest -v", True),
    ("cd '/a path'; python3 -B -m unittest -v", True),
    ("cd /repo && python3 -B -m unittest", True),
    ('echo "python3 -B -m unittest -v"', False),
    ("python3 -B -m unittest -v; true", False),
    ("python3 -B -m unittest -v || true", False),
])
def test_direct_unittest_command(cmd, valid):
    assert checks["is_unittest_command"](cmd) == valid
