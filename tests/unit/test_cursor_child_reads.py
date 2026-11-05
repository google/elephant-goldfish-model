# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Fail closed when native Cursor child read evidence is incomplete."""

import json
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / 'integration/cursor_child_reads.py'


def probe(tmp_path: Path, messages: list[dict], required: str) -> subprocess.CompletedProcess:
    database = tmp_path / 'child.db'
    with sqlite3.connect(database) as connection:
        connection.execute('CREATE TABLE blobs (id TEXT PRIMARY KEY, data BLOB)')
        connection.executemany(
            'INSERT INTO blobs VALUES (?, ?)',
            [(str(index), json.dumps(message).encode()) for index, message in enumerate(messages)],
        )
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(database), '--required', required],
        text=True, capture_output=True, check=False,
    )


def call(path: str, call_id: str = 'call-1') -> dict:
    return {'role': 'assistant', 'content': [
        {'type': 'tool-call', 'toolName': 'ReadFile', 'toolCallId': call_id,
         'args': {'path': path}},
    ]}


def result(path: str, call_id: str = 'call-1', error: bool = False,
           content: str = 'fixture content') -> dict:
    return {
        'role': 'tool',
        'content': [{'type': 'tool-result', 'toolName': 'ReadFile', 'toolCallId': call_id}],
        'providerOptions': {'cursor': {'highLevelToolCallResult': {
            'isError': error, 'output': {'success': {'path': path, 'content': content}},
        }}},
    }


def test_correlated_success_is_required(tmp_path: Path) -> None:
    path = '/fixture/persona.md'
    run = probe(tmp_path, [call(path), result(path)], path)
    assert run.returncode == 0
    record = json.loads(run.stdout)
    assert record['missing'] == []
    assert record['reads'][0]['path'] == path
    assert record['reads'][0]['bytes'] == len('fixture content')


def test_request_without_success_fails(tmp_path: Path) -> None:
    run = probe(tmp_path, [call('/fixture/persona.md')], '/fixture/persona.md')
    assert run.returncode != 0
    assert json.loads(run.stdout)['missing'] == ['/fixture/persona.md']


def test_wrong_call_cannot_satisfy_request(tmp_path: Path) -> None:
    path = '/fixture/persona.md'
    run = probe(tmp_path, [call(path), result(path, call_id='other')], path)
    assert run.returncode != 0


@pytest.mark.parametrize(('returned_path', 'error'), [
    ('/fixture/persona.md', True),
    ('/fixture/other.md', False),
])
def test_error_or_wrong_path_cannot_satisfy_request(
    tmp_path: Path, returned_path: str, error: bool,
) -> None:
    path = '/fixture/persona.md'
    run = probe(tmp_path, [call(path), result(returned_path, error=error)], path)
    assert run.returncode != 0


def test_empty_success_cannot_satisfy_request(tmp_path: Path) -> None:
    path = '/fixture/persona.md'
    run = probe(tmp_path, [call(path), result(path, content='  ')], path)
    assert run.returncode != 0


def test_malformed_read_call_cannot_be_ignored(tmp_path: Path) -> None:
    path = '/fixture/persona.md'
    malformed = {'role': 'assistant', 'content': [
        {'type': 'tool-call', 'toolName': 'ReadFile', 'args': {'path': path}},
    ]}
    run = probe(tmp_path, [call(path), result(path), malformed], path)
    assert run.returncode != 0


def test_unexpected_read_entry_type_cannot_be_ignored(tmp_path: Path) -> None:
    path = '/fixture/persona.md'
    malformed = {'role': 'assistant', 'content': [
        {'type': 'unexpected', 'toolName': 'ReadFile', 'toolCallId': 'call-2'},
    ]}
    run = probe(tmp_path, [call(path), result(path), malformed], path)
    assert run.returncode != 0


def test_live_wal_is_rejected(tmp_path: Path) -> None:
    database = tmp_path / 'child.db'
    with sqlite3.connect(database) as connection:
        connection.execute('CREATE TABLE blobs (id TEXT PRIMARY KEY, data BLOB)')
    Path(str(database) + '-wal').write_bytes(b'not-a-backup')
    run = subprocess.run(
        [sys.executable, str(SCRIPT), str(database), '--required', '/fixture/persona.md'],
        text=True, capture_output=True, check=False,
    )
    assert run.returncode != 0
    assert 'without a WAL file' in run.stderr


def test_conflicting_error_after_success_fails(tmp_path: Path) -> None:
    path = '/fixture/persona.md'
    run = probe(tmp_path, [call(path), result(path), result(path, error=True)], path)
    assert run.returncode != 0
    assert 'conflicting success and error' in run.stderr


def test_malformed_json_array_fails(tmp_path: Path) -> None:
    path = '/fixture/persona.md'
    database = tmp_path / 'child.db'
    with sqlite3.connect(database) as connection:
        connection.execute('CREATE TABLE blobs (id TEXT PRIMARY KEY, data BLOB)')
        connection.executemany('INSERT INTO blobs VALUES (?, ?)', [
            ('1', json.dumps(call(path)).encode()),
            ('2', json.dumps(result(path)).encode()),
            ('3', b'[oops'),
        ])
    run = subprocess.run(
        [sys.executable, str(SCRIPT), str(database), '--required', path],
        text=True, capture_output=True, check=False,
    )
    assert run.returncode != 0
    assert 'Malformed JSON-looking blob' in run.stderr
