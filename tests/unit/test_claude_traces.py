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
