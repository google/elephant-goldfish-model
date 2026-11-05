# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Adversarial evidence checks for exported native OpenCode child sessions."""

from copy import deepcopy
from pathlib import Path
import runpy

import pytest


MODULE = runpy.run_path(str(
    Path(__file__).resolve().parents[2] / 'tests/integration/opencode_trace_verifier.py'
))
verify = MODULE['verify']
EvidenceError = MODULE['EvidenceError']
PERSONA = '/bundle/agents/zoom_out.md'
TARGET = '/project/design.md'


def read_part(part_id: str, call_id: str, path: str) -> dict:
    return {
        'type': 'tool', 'tool': 'read', 'id': part_id, 'callID': call_id,
        'sessionID': 'child', 'messageID': 'assistant-1',
        'state': {
            'status': 'completed', 'input': {'filePath': path},
            'time': {'start': 110, 'end': 120},
            'output': (
                f'<path>{path}</path>\n<type>file</type>\n<content>\n'
                '1: content\n\n(End of file - total 1 lines)\n</content>'
            ),
        },
    }


@pytest.fixture
def evidence() -> tuple[list[dict], dict]:
    parent = [{
        'type': 'tool_use', 'sessionID': 'parent',
        'part': {
            'type': 'tool', 'tool': 'task', 'callID': 'task-1', 'id': 'task-part',
            'messageID': 'parent-message', 'sessionID': 'parent',
            'state': {
                'status': 'completed',
                'output': (
                    '<task id="child" state="completed">\n<task_result>\n'
                    'Completed\n</task_result>\n</task>'
                ),
                'input': {'subagent_type': 'egm-zoom-out'},
                'time': {'start': 100, 'end': 130},
                'metadata': {'sessionId': 'child', 'parentSessionId': 'parent'},
            },
        },
    }]
    child = {
        'info': {
            'id': 'child', 'parentID': 'parent', 'version': '1.18.29',
            'agent': 'egm-zoom-out',
        },
        'messages': [
            {'info': {'id': 'user-1', 'sessionID': 'child', 'role': 'user'}, 'parts': []},
            {
                'info': {'id': 'assistant-1', 'sessionID': 'child', 'role': 'assistant'},
                'parts': [read_part('part-1', 'call-1', PERSONA),
                          read_part('part-2', 'call-2', TARGET)],
            },
            {
                'info': {'id': 'assistant-2', 'sessionID': 'child', 'role': 'assistant',
                         'finish': 'stop', 'time': {'completed': 123}},
                'parts': [{'type': 'text', 'text': 'Completed'}],
            },
        ],
    }
    return parent, child


def test_accepts_correlated_nonempty_read_results(evidence: tuple[list[dict], dict]) -> None:
    parent, child = evidence
    verify(parent, child, [PERSONA, TARGET])


def test_accepts_last_text_part_from_multi_part_final_message(
    evidence: tuple[list[dict], dict],
) -> None:
    parent, child = evidence
    child['messages'][2]['parts'] = [
        {'type': 'text', 'text': 'First'},
        {'type': 'text', 'text': 'Completed'},
    ]
    verify(parent, child, [PERSONA, TARGET])


def test_accepts_native_system_reminder_suffix(evidence: tuple[list[dict], dict]) -> None:
    parent, child = evidence
    part = child['messages'][1]['parts'][0]
    part['state']['output'] += '\n\n<system-reminder>\nApplicable instructions\n</system-reminder>'
    verify(parent, child, [PERSONA])


def test_child_claim_cannot_substitute_for_a_missing_read(
    evidence: tuple[list[dict], dict],
) -> None:
    parent, child = evidence
    child['messages'][1]['parts'] = [read_part('part-2', 'call-2', TARGET)]
    child['messages'][2]['parts'][0]['text'] = f'I read {PERSONA}'
    parent[0]['part']['state']['output'] = (
        '<task id="child" state="completed">\n<task_result>\n'
        f'I read {PERSONA}\n</task_result>\n</task>'
    )
    with pytest.raises(EvidenceError, match='missing successful required reads'):
        verify(parent, child, [PERSONA, TARGET])


@pytest.mark.parametrize('change', [
    'error', 'empty', 'unrelated_output', 'wrong_message', 'wrong_session',
    'duplicate_call', 'duplicate_part', 'wrong_parent', 'duplicate_task',
    'missing_completion', 'wrong_version', 'relative_path', 'wrong_agent',
    'read_outside_task', 'missing_read_time', 'resumed_task', 'read_after_final',
    'mismatched_task_result', 'mismatched_task_result_id', 'zero_limit', 'arbitrary_suffix',
])
def test_rejects_unreliable_or_conflicting_evidence(
    evidence: tuple[list[dict], dict], change: str,
) -> None:
    parent, child = deepcopy(evidence)
    part = child['messages'][1]['parts'][0]
    if change == 'error':
        part['state'] = {'status': 'error', 'input': {'filePath': PERSONA},
                         'time': {'start': 110, 'end': 120}, 'error': 'denied'}
    elif change == 'empty':
        part['state']['output'] = (
            f'<path>{PERSONA}</path>\n<type>file</type>\n<content>\n'
            '1:  \n\n(End of file - total 1 lines)\n</content>'
        )
    elif change == 'unrelated_output':
        part['state']['output'] = part['state']['output'].replace(PERSONA, TARGET)
    elif change == 'wrong_message':
        part['messageID'] = 'another-message'
    elif change == 'wrong_session':
        part['sessionID'] = 'another-session'
    elif change == 'duplicate_call':
        child['messages'][1]['parts'][1]['callID'] = part['callID']
    elif change == 'duplicate_part':
        child['messages'][1]['parts'][1]['id'] = part['id']
    elif change == 'wrong_parent':
        parent[0]['part']['state']['metadata']['parentSessionId'] = 'another-parent'
    elif change == 'duplicate_task':
        parent.append(deepcopy(parent[0]))
    elif change == 'missing_completion':
        child['messages'][2]['info']['finish'] = 'tool-calls'
    elif change == 'wrong_version':
        child['info']['version'] = '2.0.0'
    elif change == 'relative_path':
        part['state']['input']['filePath'] = 'agents/zoom_out.md'
    elif change == 'wrong_agent':
        child['info']['agent'] = 'egm-comprehension'
    elif change == 'read_outside_task':
        part['state']['time']['start'] = 99
    elif change == 'missing_read_time':
        del part['state']['time']
    elif change == 'resumed_task':
        parent[0]['part']['state']['input']['task_id'] = 'old-child'
    elif change == 'read_after_final':
        part['state']['time'] = {'start': 124, 'end': 125}
    elif change == 'mismatched_task_result':
        parent[0]['part']['state']['output'] = (
            parent[0]['part']['state']['output'].replace('Completed', 'Something else')
        )
    elif change == 'mismatched_task_result_id':
        parent[0]['part']['state']['output'] = (
            parent[0]['part']['state']['output'].replace('id="child"', 'id="old-child"')
        )
    elif change == 'zero_limit':
        part['state']['input']['limit'] = 0
        part['state']['output'] = (
            f'<path>{PERSONA}</path>\n<type>file</type>\n<content>\n\n\n'
            '(Showing lines 1-0 of 3. Use offset=1 to continue.)\n</content>'
        )
    elif change == 'arbitrary_suffix':
        part['state']['output'] += '\nUnrecognized suffix'
    with pytest.raises(EvidenceError):
        verify(parent, child, [PERSONA, TARGET])


def test_rejects_conflicting_results_for_one_required_path(
    evidence: tuple[list[dict], dict],
) -> None:
    parent, child = evidence
    child['messages'][1]['parts'].append({
        **read_part('part-3', 'call-3', PERSONA),
        'state': {'status': 'error', 'input': {'filePath': PERSONA},
                  'time': {'start': 110, 'end': 120}, 'error': 'denied'},
    })
    with pytest.raises(EvidenceError, match='failed or conflicting'):
        verify(parent, child, [PERSONA])


def test_rejects_duplicate_or_noncanonical_required_paths(
    evidence: tuple[list[dict], dict],
) -> None:
    parent, child = evidence
    for required in ([PERSONA, PERSONA], ['/bundle/../agents/zoom_out.md'], []):
        with pytest.raises(EvidenceError):
            verify(parent, child, required)
