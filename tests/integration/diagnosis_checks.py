# SPDX-License-Identifier: Apache-2.0
"""Input checks shared by the native diagnosis fixtures, without model calls."""

import re
import json
from pathlib import Path


def assert_unbiased_input(text: str, marker: str, hypothesis: str) -> None:
    """Reject the known parent theory even when its tracking label is omitted.

    This checks a known phrase, not every possible semantic paraphrase. Apply it
    to inputs, not the child result, where a theory can be independently found.
    Encrypted inputs must be reported as unavailable, not passed to this check.
    """
    assert not text.startswith("gAAAA"), "Encrypted input cannot be audited"
    assert marker not in text, "Parent-only marker leaked into diagnostic input"
    normalize = lambda value: " ".join(re.findall(r"\w+", value.casefold()))
    assert normalize(hypothesis) not in normalize(text), (
        "Parent hypothesis leaked into diagnostic input without its marker"
    )


def claude_reads(raw: str) -> dict[Path, str]:
    """Correlate successful, nonempty native Read results to requested paths."""
    calls, results = {}, {}
    for line in raw.split("\n"):
        if not line.strip():
            continue
        event = json.loads(line)
        content = event.get("message", {}).get("content", [])
        for block in content if isinstance(content, list) else []:
            if (event.get("type") == "assistant"
                    and block.get("type") == "tool_use"
                    and block.get("name") == "Read"):
                calls[block["id"]] = Path(block["input"]["file_path"]).resolve()
            if (event.get("type") == "user"
                    and block.get("type") == "tool_result"
                    and not block.get("is_error")):
                value = block.get("content", "")
                if isinstance(value, list):
                    value = "\n".join(p["text"] for p in value
                                      if p.get("type") == "text"
                                      and isinstance(p.get("text"), str))
                call_id = block.get("tool_use_id")
                if call_id in calls and isinstance(value, str) and value.strip():
                    results[calls[call_id]] = value
    return results


def claude_diagnosis_answer(raw: str) -> str:
    """Accept native final text or handback, with read-only investigation tools."""
    answer = None
    handback_id = None
    for line in raw.split("\n"):
        if not line.strip():
            continue
        event = json.loads(line)
        content = event.get("message", {}).get("content", [])
        for block in content if isinstance(content, list) else []:
            if event.get("type") == "assistant":
                assert handback_id is None, "Output after diagnosis handback"
                if block.get("type") == "text" and block.get("text", "").strip():
                    answer = block["text"]
                if block.get("type") == "tool_use":
                    assert block["name"] in {"Read", "Grep", "Glob", "SubagentHandback"}, (
                        "Diagnosis child used a forbidden tool"
                    )
                    if block["name"] == "SubagentHandback":
                        handback_id = block["id"]
                        data = block.get("input")
                        assert isinstance(data, dict), "Malformed diagnosis handback"
                        answer = data.get("message")
                        assert isinstance(answer, str) and answer.strip(), (
                            "Missing diagnosis handback"
                        )
                    else:
                        # Tool activity after prose means that prose was narration.
                        answer = None
            if (event.get("type") == "user"
                    and block.get("type") == "tool_result"
                    and block.get("tool_use_id") == handback_id):
                assert not block.get("is_error"), "Rejected diagnosis handback"
    assert isinstance(answer, str) and answer.strip(), "Missing final diagnosis"
    return answer
