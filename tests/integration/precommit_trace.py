# SPDX-License-Identifier: Apache-2.0
"""Read native Claude evidence; reports alone do not establish execution."""

import json
import re
import shlex
from pathlib import Path


def blocks(raw: str):
    for line in raw.split("\n"):
        if line.strip():
            event = json.loads(line)
            content = event.get("message", {}).get("content", [])
            for block in content if isinstance(content, list) else []:
                yield event.get("type"), block


def calls_and_results(raw: str) -> tuple[dict, dict]:
    calls, results = {}, {}
    for role, block in blocks(raw):
        if role == "assistant" and block.get("type") == "tool_use":
            calls[block["id"]] = block
        if role == "user" and block.get("type") == "tool_result":
            results[block["tool_use_id"]] = block
    return calls, results


def successful_reads(raw: str) -> dict[Path, str]:
    calls, results = calls_and_results(raw)
    reads, lines = {}, {}
    for key, call in calls.items():
        result = results.get(key, {})
        content = result.get("content", "")
        if isinstance(content, list):
            content = "\n".join(b["text"] for b in content if b.get("type") == "text")
        if (call["name"] == "Read" and not result.get("is_error")
                and isinstance(content, str) and content.strip()):
            path = Path(call["input"]["file_path"]).resolve()
            if not path.is_file():
                continue
            expected = path.read_text(encoding="utf-8")
            if not expected:
                if "empty" in content.lower() and call["input"].get("offset", 1) == 1:
                    reads[path] = content
                continue
            if content == expected:
                reads[path] = content
                continue
            coverage = lines.setdefault(path, {})
            for match in re.finditer(r"(?m)^[ \t]*(\d+)(?:\t|→)([^\n]*)", content):
                coverage[int(match[1])] = match[2]
            expected_lines = expected.split("\n")
            if expected.endswith("\n"):
                expected_lines.pop()
            if all(coverage.get(n) == text for n, text in enumerate(expected_lines, 1)):
                reads[path] = expected
    return reads


def child_answer(raw: str) -> str:
    answer, handback = None, None
    for role, block in blocks(raw):
        if role == "assistant":
            assert handback is None, "Output after handback"
            if block.get("type") == "text" and block.get("text", "").strip():
                answer = block["text"]
            if block.get("type") == "tool_use":
                assert block["name"] in {"Read", "Grep", "Glob", "SubagentHandback"}
                answer = None
                if block["name"] == "SubagentHandback":
                    handback = block["id"]
                    data = block.get("input")
                    assert isinstance(data, dict)
                    answer = data.get("message")
        if (role == "user" and block.get("type") == "tool_result"
                and block.get("tool_use_id") == handback):
            assert not block.get("is_error"), "Rejected handback"
    assert isinstance(answer, str) and answer.strip(), "Missing completed report"
    return answer


def field(text: str, name: str) -> str:
    plain = text.replace("**", "").replace("`", "")
    matches = re.findall(rf"(?mi)^\s*(?:-\s*)?{re.escape(name)}:\s*([^\n]+)", plain)
    assert len(matches) == 1, f"Missing or ambiguous {name} field"
    return matches[0].strip().lower().split(" (", 1)[0].removesuffix(".")


def unittest_runs(raw: str) -> list[tuple[int, bool]]:
    """Require a direct unittest command and its native result, in event order."""
    calls, _ = calls_and_results(raw)
    runs = []
    for position, (role, block) in enumerate(blocks(raw)):
        if role != "user" or block.get("type") != "tool_result":
            continue
        call = calls.get(block.get("tool_use_id"), {})
        command = call.get("input", {}).get("command", "")
        if call.get("name") != "Bash" or not is_unittest_command(command):
            continue
        content = block.get("content", "")
        if not isinstance(content, str) or not re.search(r"Ran 2 tests? in", content):
            continue
        if re.search(r"(?m)^OK\s*$", content) and not block.get("is_error"):
            runs.append((position, True))
        elif "FAILED (failures=" in content and block.get("is_error"):
            runs.append((position, False))
    return runs


def is_unittest_command(command: str) -> bool:
    if any(c in command for c in "\n\r$`"):
        return False
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
        lexer.whitespace_split = True
        args = list(lexer)
    except ValueError:
        return False
    if len(args) >= 3 and args[0] == "cd" and args[2] in {";", "&&"}:
        args = args[3:]
    return args in (["python3", "-B", "-m", "unittest"],
                    ["python3", "-B", "-m", "unittest", "-v"])


def assert_seeded_findings(answer: str) -> None:
    """Require two distinct findings, not path mentions in a coverage list."""
    plain = answer.replace("**", "").replace("`", "")
    section = re.split(r"(?mi)^\s*(?:#{1,6}\s*)?Findings:\s*", plain)
    assert len(section) == 2, "Missing Findings section"
    section = re.split(r"(?mi)^\s*(?:#{1,6}\s*)?(?:Previous findings|Validation limits):", section[1])[0]
    findings = re.findall(r"(?ms)^\s*\d+\.\s+(.*?)(?=^\s*\d+\.\s+|\Z)", section)

    def layer(finding: str, path: str, expected: str) -> bool:
        match = re.search(rf"{re.escape(path)}:\d+\s*\(([^)]*)\)", finding)
        return bool(match and re.search(rf"(?i)\b(?:{expected})\b", match[1]))

    access = [i for i, f in enumerate(findings) if layer(f, "access.py", "staged|index")
              and re.search(r"(?i)!=|invert|revers|non.owner|unauthori[sz]ed", f)]
    currency = [i for i, f in enumerate(findings) if layer(f, "currency ü.py", "untracked")
                and re.search(r"100|500|factor|dollars.*cents", f)]
    assert access and currency and set(access).isdisjoint(currency), "Missing distinct seeded defects"


def assert_validation(raw: str, mode: str) -> None:
    events = list(blocks(raw))
    dispatches = [(i, b["id"]) for i, (role, b) in enumerate(events)
                  if role == "assistant" and b.get("type") == "tool_use"
                  and b.get("name") == "Agent"]
    assert len(dispatches) == (2 if mode == "fix" else 1)
    runs = unittest_runs(raw)
    assert any(i < dispatches[0][0] for i, _ in runs), "No native preflight checks"
    if mode == "review":
        assert any(ok for _, ok in runs)
        return
    assert any(i < dispatches[0][0] and not ok for i, ok in runs)
    completed = [i for i, (role, b) in enumerate(events)
                 if role == "user" and b.get("type") == "tool_result"
                 and b.get("tool_use_id") == dispatches[0][1] and not b.get("is_error")]
    assert len(completed) == 1, "First review did not complete"
    assert any(completed[0] < i < dispatches[1][0] and ok for i, ok in runs), (
        "No passing checks after first review and before fresh re-review"
    )


def codex_full_reads(trace: list[dict]) -> set[Path]:
    """Require a successful literal single cat and complete retained contents."""
    reads = set()
    for event in trace:
        payload = event.get("payload", {})
        if event.get("type") != "event_msg" or payload.get("type") != "item_completed":
            continue
        item = payload.get("item", {})
        if (item.get("type") != "CommandExecution" or item.get("exit_code") != 0
                or item.get("status") != "completed"):
            continue
        commands = item.get("parsed_cmd", [])
        if len(commands) != 1:
            continue
        command = commands[0].get("cmd", "")
        if any(c in command for c in "\n\r;$`|&<>*?{}()"):
            continue
        try:
            args = shlex.split(command)
        except ValueError:
            continue
        if len(args) != 2 or args[0] != "cat":
            continue
        path = Path(args[1])
        if path.is_absolute() and not path.is_symlink() and path.is_file():
            contents = path.read_text(encoding="utf-8")
            if contents in item.get("aggregated_output", ""):
                reads.add(path.resolve())
    return reads
