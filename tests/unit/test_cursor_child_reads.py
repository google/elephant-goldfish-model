# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Fail closed when native Cursor child read or canary evidence is incomplete."""

import base64
import gzip
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import zlib

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


MARKER = 'EGM-CANARY-0f3c9a7e5b2d4c18a6e1'


def store(tmp_path: Path, blobs: list[bytes], extra: bytes | None = None) -> Path:
    database = tmp_path / 'child.db'
    with sqlite3.connect(database) as connection:
        connection.execute('CREATE TABLE blobs (id TEXT PRIMARY KEY, data BLOB)')
        connection.executemany('INSERT INTO blobs VALUES (?, ?)',
                               [(str(i), blob) for i, blob in enumerate(blobs)])
        connection.execute('CREATE TABLE meta (key TEXT, value BLOB)')
        if extra is not None:
            connection.execute('INSERT INTO meta VALUES (?, ?)', ('k', extra))
    return database


def scan(database: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), str(database), *args],
                          text=True, capture_output=True, check=False)


def clean_records(path: str = '/fixture/persona.md') -> list[bytes]:
    return [json.dumps(call(path)).encode(), json.dumps(result(path)).encode()]


def test_absent_canary_passes_with_required_reads(tmp_path: Path) -> None:
    run = scan(store(tmp_path, clean_records()),
               '--required', '/fixture/persona.md', '--absent', MARKER)
    assert run.returncode == 0, run.stderr
    canary = json.loads(run.stdout)['canary']
    assert canary['status'] == 'absent'
    assert canary['cells_scanned'] > 0


def leak_text(prefix: str = '') -> bytes:
    return json.dumps({'role': 'user', 'content': f'{prefix}{MARKER}'}).encode()


@pytest.mark.parametrize('leak', [
    leak_text(),
    MARKER.encode('utf-16-le'),
    *(b'{"b":"' + base64.b64encode(b'x' * n + MARKER.encode()) + b'"}' for n in range(3)),
    gzip.compress(MARKER.encode()),
    zlib.compress(MARKER.encode()),
], ids=['json', 'utf16', 'base64-0', 'base64-1', 'base64-2', 'gzip', 'zlib'])
def test_leaked_canary_fails_in_any_encoding(tmp_path: Path, leak: bytes) -> None:
    run = scan(store(tmp_path, [*clean_records(), leak]), '--absent', MARKER)
    assert run.returncode == 1
    assert json.loads(run.stdout)['canary']['status'] == 'found'
    assert MARKER not in run.stdout  # The report never repeats the marker.


def test_leak_outside_the_blobs_table_fails(tmp_path: Path) -> None:
    run = scan(store(tmp_path, clean_records(), extra=MARKER.encode()), '--absent', MARKER)
    assert run.returncode == 1
    assert json.loads(run.stdout)['canary']['found'][0]['table'] == 'meta'


def test_undecodable_compression_is_inconclusive_not_absent(tmp_path: Path) -> None:
    run = scan(store(tmp_path, [*clean_records(), b'\x28\xb5\x2f\xfd' + b'\0' * 8]),
               '--absent', MARKER)
    assert run.returncode == 3
    canary = json.loads(run.stdout)['canary']
    assert canary['status'] == 'inconclusive'
    assert canary['unsearchable'][0]['codec'] == 'zstd'


@pytest.mark.parametrize('args', [[], ['--absent', 'short'], ['--absent', 'bad marker 123456']])
def test_canary_arguments_are_validated(tmp_path: Path, args: list[str]) -> None:
    run = scan(store(tmp_path, clean_records()), *args)
    assert run.returncode == 2
