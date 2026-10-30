# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Check required reads in an exported OpenCode 1.18.29 child session.

This is an offline evidence check. It does not control the running agent or
prove complete file coverage, context isolation, or transcript authenticity.
"""

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any


class EvidenceError(ValueError):
    """Evidence is missing, inconsistent, or outside the supported format."""


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvidenceError(f'{label} must be an object')
    return value


def _identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceError(f'{label} must be a nonempty string')
    return value


def _path(value: Any) -> str:
    path = _identifier(value, 'read path')
    if '\x00' in path or not path.startswith('/') or str(PurePosixPath(path)) != path:
        raise EvidenceError(f'read path must be an absolute canonical POSIX path: {path!r}')
    if '..' in PurePosixPath(path).parts:
        raise EvidenceError(f'read path must not contain ..: {path!r}')
    return path


def _nonempty_file_output(output: Any, expected_path: str) -> bool:
    if not isinstance(output, str):
        return False
    match = re.fullmatch(
        r'<path>([^\n]*)</path>\n<type>file</type>\n<content>\n(.*?)\n</content>'
        r'(?:\n\n<system-reminder>\n.*\n</system-reminder>)?',
        output, re.DOTALL,
    )
    if not match or match.group(1) != expected_path:
        return False
    lines = re.findall(r'^\d+: ?(.*)$', match.group(2), flags=re.MULTILINE)
    return any(line.strip() for line in lines)


def _interval(value: Any, label: str) -> tuple[int, int]:
    times = _object(value, label)
    start, end = times.get('start'), times.get('end')
    if type(start) is not int or type(end) is not int or start < 0 or end < start:
        raise EvidenceError(f'{label} must have ordered integer timestamps')
    return start, end


def verify(parent_events: list[Any], child_export: Any, required_paths: list[str]) -> None:
    """Raise EvidenceError unless every requested path has matched native evidence."""
    if not required_paths:
        raise EvidenceError('at least one required path is needed')
    required = {_path(path) for path in required_paths}
    if len(required) != len(required_paths):
        raise EvidenceError('duplicate required paths')

    child = _object(child_export, 'child export')
    info = _object(child.get('info'), 'child info')
    child_id = _identifier(info.get('id'), 'child session ID')
    parent_id = _identifier(info.get('parentID'), 'parent session ID')
    if child_id == parent_id or info.get('version') != '1.18.29':
        raise EvidenceError('child identity or OpenCode version is invalid')

    matching_tasks = []
    for raw in parent_events:
        event = _object(raw, 'parent event')
        if event.get('type') != 'tool_use':
            continue
        part = _object(event.get('part'), 'parent tool part')
        if part.get('tool') != 'task':
            continue
        state = _object(part.get('state'), 'task state')
        metadata = _object(state.get('metadata'), 'task metadata')
        if metadata.get('sessionId') == child_id:
            matching_tasks.append((event, part, state, metadata))
    if len(matching_tasks) != 1:
        raise EvidenceError('expected exactly one matching native child task')
    event, part, state, metadata = matching_tasks[0]
    _identifier(part.get('callID'), 'task call ID')
    _identifier(part.get('id'), 'parent task part ID')
    _identifier(part.get('messageID'), 'parent task message ID')
    task_input = _object(state.get('input'), 'task input')
    agent = _identifier(task_input.get('subagent_type'), 'task reviewer type')
    task_start, task_end = _interval(state.get('time'), 'parent task time')
    if (event.get('sessionID') != parent_id or part.get('sessionID') != parent_id
            or metadata.get('parentSessionId') != parent_id
            or info.get('agent') != agent
            or 'task_id' in task_input
            or state.get('status') != 'completed'
            or not isinstance(state.get('output'), str)
            or not state['output'].strip()):
        raise EvidenceError('native parent task identity or completion is invalid')

    messages = child.get('messages')
    if not isinstance(messages, list) or not messages:
        raise EvidenceError('child messages must be a nonempty list')
    seen_messages: set[str] = set()
    seen_parts: set[str] = set()
    seen_calls: set[str] = set()
    successful: set[str] = set()
    failed: set[str] = set()
    required_read_ends: list[int] = []
    final_message: dict[str, Any] | None = None
    for raw_message in messages:
        message = _object(raw_message, 'child message')
        message_info = _object(message.get('info'), 'message info')
        message_id = _identifier(message_info.get('id'), 'message ID')
        if message_id in seen_messages or message_info.get('sessionID') != child_id:
            raise EvidenceError('duplicate message or conflicting message session')
        seen_messages.add(message_id)
        role = message_info.get('role')
        if role not in ('user', 'assistant'):
            raise EvidenceError('unsupported child message role')
        parts = message.get('parts')
        if not isinstance(parts, list):
            raise EvidenceError('message parts must be a list')
        if role == 'assistant':
            final_message = message
        for raw_part in parts:
            child_part = _object(raw_part, 'child part')
            if child_part.get('type') != 'tool':
                continue
            if role != 'assistant':
                raise EvidenceError('tool part is not an assistant message')
            part_id = _identifier(child_part.get('id'), 'part ID')
            call_id = _identifier(child_part.get('callID'), 'tool call ID')
            if (part_id in seen_parts or call_id in seen_calls
                    or child_part.get('sessionID') != child_id
                    or child_part.get('messageID') != message_id):
                raise EvidenceError('duplicate or conflicting tool call identity')
            seen_parts.add(part_id)
            seen_calls.add(call_id)
            if child_part.get('tool') != 'read':
                continue
            read_state = _object(child_part.get('state'), 'read state')
            read_input = _object(read_state.get('input'), 'read input')
            read_path = _path(read_input.get('filePath'))
            status = read_state.get('status')
            if status not in ('completed', 'error'):
                raise EvidenceError('read did not finish')
            if read_path not in required:
                continue
            read_start, read_end = _interval(read_state.get('time'), 'required read time')
            if not task_start <= read_start <= read_end <= task_end:
                raise EvidenceError(f'required read occurred outside the parent task: {read_path}')
            required_read_ends.append(read_end)
            if status == 'error':
                failed.add(read_path)
            elif _nonempty_file_output(read_state.get('output'), read_path):
                successful.add(read_path)
            else:
                raise EvidenceError(f'malformed or empty native read result: {read_path}')

    if final_message is None:
        raise EvidenceError('missing child assistant completion')
    final_info = _object(final_message.get('info'), 'final message info')
    final_time = _object(final_info.get('time'), 'final message time')
    final_end = final_time.get('completed')
    text_parts = [
        part['text'] for part in final_message['parts']
        if isinstance(part, dict) and part.get('type') == 'text'
        and isinstance(part.get('text'), str)
    ]
    if (final_info.get('finish') != 'stop' or type(final_end) is not int
            or not task_start <= final_end <= task_end
            or not text_parts or not text_parts[-1].strip()):
        raise EvidenceError('missing completed child final text')
    if any(end > final_end for end in required_read_ends):
        raise EvidenceError('required read completed after the child final response')
    final_text = text_parts[-1]
    expected_output = (
        f'<task id="{child_id}" state="completed">\n<task_result>\n'
        f'{final_text}\n</task_result>\n</task>'
    )
    if state['output'] != expected_output:
        raise EvidenceError('parent task result does not match child final text')
    if required & failed:
        raise EvidenceError('required read has a failed or conflicting result')
    missing = required - successful
    if missing:
        raise EvidenceError('missing successful required reads: ' + ', '.join(sorted(missing)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent-trace', type=Path, required=True)
    parser.add_argument('--child-export', type=Path, required=True)
    parser.add_argument('--require', action='append', required=True, dest='required_paths')
    args = parser.parse_args()
    try:
        lines = args.parent_trace.read_text(encoding='utf-8').split('\n')
        parent = [json.loads(line) for line in lines if line.strip()]
        child = json.loads(args.child_export.read_text(encoding='utf-8'))
        verify(parent, child, args.required_paths)
    except (EvidenceError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f'INCOMPLETE: {exc}', file=sys.stderr)
        return 1
    print('Required native reads verified; this is not an isolation or coverage verdict.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
