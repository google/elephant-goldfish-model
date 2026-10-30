# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Offline regression coverage for Claude's native transcript directory."""

import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import runpy
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("config_mode", ["unset", "default", "custom"])
@pytest.mark.parametrize(
    ("workspace_path", "project_name"),
    [
        (PurePosixPath("/work/egm probe.v1"), "-work-egm-probe-v1"),
        (PureWindowsPath(r"C:\work\egm probe.v1"), "C--work-egm-probe-v1"),
    ],
)
def test_trace_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, config_mode: str,
    workspace_path: PurePosixPath | PureWindowsPath, project_name: str,
) -> None:
  trace_directory = runpy.run_path(str(ROOT / "tests/integration/test_claude.py"))[
      "trace_directory"
  ]
  monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path / "home"))
  config = tmp_path / "home" / ".claude"
  if config_mode == "unset":
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
  else:
    if config_mode == "custom":
      config = tmp_path / "custom config"
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(config))

  workspace = Mock(spec=Path)
  workspace.resolve.return_value = workspace_path
  assert trace_directory(workspace) == (
      config / "projects" / project_name
  )


@pytest.mark.parametrize("result", [
    "success", "error", "missing", "unrelated", "empty", "whitespace",
    "empty_text_block", "whitespace_text_block", "valid_text_blocks",
])
def test_child_probe_requires_successful_read(result: str) -> None:
  check = runpy.run_path(str(ROOT / "tests/integration/test_claude.py"))[
      "assert_child_probe"
  ]
  persona = Path("/plugin/agents/zoom_out.md")
  events = [{"type": "assistant", "message": {"content": [{
      "type": "tool_use", "id": "read-persona", "name": "Read",
      "input": {"file_path": str(persona)},
  }]}}]
  if result != "missing":
    content = {
        "empty": "",
        "whitespace": " \t\n",
        "empty_text_block": [{"type": "text", "text": ""}],
        "whitespace_text_block": [{"type": "text", "text": " \t\n"}],
        "valid_text_blocks": [
            {"type": "text", "text": ""},
            {"type": "text", "text": "Persona text"},
        ],
    }.get(result, "Persona text")
    events.append({"type": "user", "message": {"content": [{
        "type": "tool_result",
        "tool_use_id": "other-read" if result == "unrelated" else "read-persona",
        "is_error": result == "error",
        "content": content,
    }]}})
  events.append({"type": "assistant", "message": {"content": [{
      "type": "text", "text": "UNKNOWN",
  }]}})
  raw = "\n".join(json.dumps(event) for event in events)
  if result in {"success", "valid_text_blocks"}:
    check(raw, persona, ["parent-only-marker"])
  else:
    with pytest.raises(AssertionError, match="successful native tool result"):
      check(raw, persona, ["parent-only-marker"])


@pytest.mark.parametrize("separator", ["\u0085", "\u2028", "\u2029"])
def test_child_probe_keeps_unicode_inside_json_records(separator: str) -> None:
  check = runpy.run_path(str(ROOT / "tests/integration/test_claude.py"))[
      "assert_child_probe"
  ]
  persona = Path("/plugin/agents/zoom_out.md")
  events = [
      {"type": "assistant", "message": {"content": [{
          "type": "tool_use", "id": "read", "name": "Read",
          "input": {"file_path": str(persona)},
      }]}},
      {"type": "user", "message": {"content": [{
          "type": "tool_result", "tool_use_id": "read",
          "content": f"Persona{separator}text",
      }]}},
      {"type": "assistant", "message": {"content": [{
          "type": "text", "text": "UNKNOWN",
      }]}},
  ]
  raw = "\n".join(json.dumps(event, ensure_ascii=False) for event in events)
  check(raw, persona, ["parent-only-marker"])
  with pytest.raises(AssertionError):
    check(raw, persona, ["Persona"])


@pytest.mark.parametrize("result", [
    "denied", "missing", "unrelated", "success", "empty", "duplicate",
    "wrong_sentinel", "extra_read",
])
def test_denied_persona_requires_correlated_error(result: str) -> None:
  check = runpy.run_path(str(ROOT / "tests/integration/test_claude.py"))[
      "assert_child_probe"
  ]
  persona = Path("/plugin/agents/zoom_out.md")
  read = {"type": "tool_use", "id": "persona", "name": "Read",
          "input": {"file_path": str(persona)}}
  events = [{"type": "assistant", "message": {"content": [read]}}]
  if result != "missing":
    response = {"type": "tool_result",
                "tool_use_id": "other" if result == "unrelated" else "persona",
                "is_error": result != "success",
                "content": [{"type": "text", "text": (
                    "" if result == "empty" else "Permission denied"
                )}]}
    events.append({"type": "user", "message": {"content": [response]}})
    if result == "duplicate":
      events.append(events[-1])
  if result == "extra_read":
    events.append({"type": "assistant", "message": {"content": [read]}})
  events.append({"type": "assistant", "message": {"content": [{
      "type": "text", "text": "UNKNOWN" if result == "wrong_sentinel"
      else "Cannot read the persona.\nRESOURCE_UNREADABLE",
  }]}})
  raw = "\n".join(json.dumps(event) for event in events)
  if result == "denied":
    check(raw, persona, ["parent-only-marker"], deny_persona=True)
  else:
    with pytest.raises(AssertionError):
      check(raw, persona, ["parent-only-marker"], deny_persona=True)


PERSONA = Path("/plugin/agents/zoom_out.md")


def assistant(*blocks: dict) -> dict:
  return {"type": "assistant", "message": {"content": list(blocks)}}


def tool_result(tool_use_id: str, is_error: bool = False) -> dict:
  return {"type": "user", "message": {"content": [{
      "type": "tool_result", "tool_use_id": tool_use_id, "is_error": is_error,
      "content": "Permission denied" if is_error else "Accepted",
  }]}}


def text(value: str) -> dict:
  return {"type": "text", "text": value}


def read(tool_use_id: str = "persona") -> dict:
  return {"type": "tool_use", "id": tool_use_id, "name": "Read",
          "input": {"file_path": str(PERSONA)}}


def handback(tool_input: object, tool_use_id: str = "handback") -> dict:
  return {"type": "tool_use", "id": tool_use_id, "name": "SubagentHandback",
          "input": tool_input}


def check_child(events: list[dict], deny_persona: bool, markers=("parent-only",)) -> None:
  check = runpy.run_path(str(ROOT / "tests/integration/test_claude.py"))[
      "assert_child_probe"
  ]
  raw = "\n".join(json.dumps(event) for event in events)
  check(raw, PERSONA, list(markers), deny_persona=deny_persona)


def read_events(deny_persona: bool) -> list[dict]:
  return [assistant(read()), tool_result("persona", is_error=deny_persona)]


def sentinels(deny_persona: bool) -> tuple[str, str]:
  """Returns the expected sentinel, followed by the other probe's sentinel."""
  pair = ("RESOURCE_UNREADABLE", "UNKNOWN")
  return pair if deny_persona else pair[::-1]


@pytest.mark.parametrize("deny_persona", [False, True], ids=["scoped", "denied"])
@pytest.mark.parametrize(
    "shape", [
        "issue", "acknowledged", "narrated", "explained", "agreeing", "extra_input",
        "text_only",
    ],
)
def test_child_probe_accepts_handback_and_legacy_text(
    deny_persona: bool, shape: str,
) -> None:
  expected, _ = sentinels(deny_persona)
  answer = {"message": expected}
  events = read_events(deny_persona)
  if shape == "narrated":
    events.insert(0, assistant(text("Reading the persona first.")))
  if shape == "explained":
    answer = {"message": f"The probe finished.\n{expected}"}
  if shape == "agreeing":
    events.append(assistant(text(expected)))
  if shape == "extra_input":
    answer = {"message": expected, "note": "done"}
  events.append(
      assistant(text(expected)) if shape == "text_only"
      else assistant(handback(answer))
  )
  if shape == "acknowledged":
    events.append(tool_result("handback"))
  check_child(events, deny_persona)


@pytest.mark.parametrize("deny_persona", [False, True], ids=["scoped", "denied"])
@pytest.mark.parametrize("case", [
    "input_missing", "input_string", "input_list", "message_missing",
    "message_none", "message_list", "message_dict", "message_bool",
    "id_missing", "two_handbacks", "text_after", "read_after", "same_message_text_after",
    "failed_ack", "duplicate_ack", "before_read_result", "same_message_as_read",
    "competing_text", "both_sentinels",
])
def test_child_probe_rejects_malformed_or_ambiguous_handback(
    deny_persona: bool, case: str,
) -> None:
  expected, other = sentinels(deny_persona)
  good = handback({"message": expected})
  no_id = {key: value for key, value in good.items() if key != "id"}
  no_input = {key: value for key, value in good.items() if key != "input"}
  prior = read_events(deny_persona)
  events = {
      "input_missing": [*prior, assistant(no_input)],
      "input_string": [*prior, assistant(handback(expected))],
      "input_list": [*prior, assistant(handback([expected]))],
      "message_missing": [*prior, assistant(handback({"text": expected}))],
      "message_none": [*prior, assistant(handback({"message": None}))],
      "message_list": [*prior, assistant(handback({"message": [expected]}))],
      "message_dict": [*prior, assistant(handback({"message": {"text": expected}}))],
      "message_bool": [*prior, assistant(handback({"message": True}))],
      "id_missing": [*prior, assistant(no_id)],
      "two_handbacks": [
          *prior, assistant(good), assistant(handback({"message": expected}, "second")),
      ],
      "text_after": [*prior, assistant(good), assistant(text(expected))],
      "read_after": [*prior, assistant(good), assistant(read("again"))],
      "same_message_text_after": [*prior, assistant(good, text(expected))],
      "failed_ack": [*prior, assistant(good), tool_result("handback", is_error=True)],
      "duplicate_ack": [
          *prior, assistant(good), tool_result("handback"), tool_result("handback"),
      ],
      "before_read_result": [assistant(read()), assistant(good), prior[1]],
      "same_message_as_read": [assistant(read(), good), prior[1]],
      "competing_text": [*prior, assistant(text(other), good)],
      "both_sentinels": [*prior, assistant(handback({"message": f"{other}\n{expected}"}))],
  }[case]
  with pytest.raises(AssertionError, match="SubagentHandback"):
    check_child(events, deny_persona)


@pytest.mark.parametrize("deny_persona", [False, True], ids=["scoped", "denied"])
@pytest.mark.parametrize("case", [
    "empty", "whitespace", "wrong_sentinel", "no_read", "other_tool",
    "other_tool_after", "similar_name", "wrong_path", "wrong_read_status",
    "second_read", "read_missing_result",
])
def test_child_probe_handback_keeps_read_and_tool_restrictions(
    deny_persona: bool, case: str,
) -> None:
  expected, other = sentinels(deny_persona)
  good = handback({"message": expected})
  prior = read_events(deny_persona)
  bash = {"type": "tool_use", "id": "bash", "name": "Bash", "input": {"command": "ls"}}
  wrong_path = {**read(), "input": {"file_path": "/plugin/agents/other.md"}}
  events = {
      "empty": [*prior, assistant(handback({"message": ""}))],
      "whitespace": [*prior, assistant(handback({"message": " \t\n"}))],
      "wrong_sentinel": [*prior, assistant(handback({"message": other}))],
      "no_read": [assistant(good)],
      "other_tool": [assistant(bash), *prior, assistant(good)],
      "other_tool_after": [*prior, assistant(bash), assistant(good)],
      "similar_name": [*prior, assistant({**good, "name": "subagenthandback"})],
      "wrong_path": [assistant(wrong_path), prior[1], assistant(good)],
      "wrong_read_status": [
          assistant(read()), tool_result("persona", is_error=not deny_persona),
          assistant(good),
      ],
      "second_read": [*prior, assistant(read("again")), assistant(good)],
      "read_missing_result": [assistant(read()), assistant(read("again")),
                              tool_result("again", is_error=deny_persona),
                              assistant(good)],
  }[case]
  with pytest.raises(AssertionError):
    check_child(events, deny_persona)


@pytest.mark.parametrize("deny_persona", [False, True], ids=["scoped", "denied"])
@pytest.mark.parametrize("field", ["message", "note"])
def test_child_probe_handback_rejects_marker_despite_valid_sentinel(
    deny_persona: bool, field: str,
) -> None:
  expected, _ = sentinels(deny_persona)
  answer = {"message": expected}
  answer[field] = f"parent-only\n{expected}"
  events = [*read_events(deny_persona), assistant(handback(answer))]
  check_child(events, deny_persona, markers=())
  with pytest.raises(AssertionError):
    check_child(events, deny_persona)
