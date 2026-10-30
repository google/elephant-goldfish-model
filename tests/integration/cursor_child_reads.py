#!/usr/bin/env python3
# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Correlate native Cursor ReadFile calls and successes in one child store."""

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('database', type=Path)
    parser.add_argument('--required', action='append', required=True)
    args = parser.parse_args()
    database = args.database.resolve(strict=True)
    wal = Path(str(database) + '-wal')
    if wal.exists():
        raise ValueError('Provide a closed SQLite backup without a WAL file')
    before_hash = hashlib.sha256(database.read_bytes()).hexdigest()
    connection = sqlite3.connect(f'{database.as_uri()}?mode=ro', uri=True)
    calls: dict[str, str] = {}
    results: dict[str, dict] = {}
    failures: set[str] = set()
    opaque_blobs = 0
    for (data,) in connection.execute('SELECT data FROM blobs'):
        try:
            message = json.loads(data)
        except (ValueError, TypeError, UnicodeDecodeError) as error:
            prefixes = ('{', '[') if isinstance(data, str) else (b'{', b'[')
            if isinstance(data, (str, bytes)) and data.lstrip().startswith(prefixes):
                raise ValueError('Malformed JSON-looking blob') from error
            opaque_blobs += 1
            continue
        if not isinstance(message, dict):
            raise ValueError('Unexpected JSON blob structure')
        if message.get('role') not in ('assistant', 'tool'):
            continue
        if not isinstance(message.get('content'), list):
            raise ValueError('Malformed assistant or tool content')
        for entry in message.get('content', []):
            if not isinstance(entry, dict):
                raise ValueError('Malformed content entry')
            call_id = entry.get('toolCallId')
            if entry.get('toolName') != 'ReadFile':
                continue
            if not isinstance(call_id, str) or not call_id:
                raise ValueError('ReadFile entry lacks a call ID')
            expected_type = 'tool-call' if message['role'] == 'assistant' else 'tool-result'
            if entry.get('type') != expected_type:
                raise ValueError(f'Unexpected ReadFile entry type {call_id}')
            if message.get('role') == 'assistant' and entry.get('type') == 'tool-call':
                arguments = entry.get('args')
                path = arguments.get('path') if isinstance(arguments, dict) else None
                if not isinstance(path, str) or not path:
                    raise ValueError('ReadFile call lacks a path')
                if call_id in calls and calls[call_id] != path:
                    raise ValueError(f'Conflicting call {call_id}')
                calls[call_id] = path
            if message.get('role') == 'tool' and entry.get('type') == 'tool-result':
                high_level = (message.get('providerOptions', {}).get('cursor', {})
                              .get('highLevelToolCallResult', {}))
                is_error = high_level.get('isError')
                if is_error is True:
                    failures.add(call_id)
                elif is_error is False:
                    success = high_level.get('output', {}).get('success')
                    if not isinstance(success, dict):
                        raise ValueError(f'Malformed result {call_id}')
                    if call_id in results and results[call_id] != success:
                        raise ValueError(f'Conflicting result {call_id}')
                    results[call_id] = success
                else:
                    raise ValueError(f'Malformed result status {call_id}')
    connection.close()
    if wal.exists() or hashlib.sha256(database.read_bytes()).hexdigest() != before_hash:
        raise ValueError('SQLite store changed while being read')
    reads = []
    if failures & results.keys():
        raise ValueError('A read has conflicting success and error outcomes')
    for call_id, path in calls.items():
        result = results.get(call_id)
        if not result or result.get('path') != path:
            continue
        content = result.get('content')
        if not isinstance(content, str) or not content.strip():
            continue
        reads.append({'call_id': call_id, 'path': path, 'bytes': len(content.encode()),
                      'sha256': hashlib.sha256(content.encode()).hexdigest()})
    missing = sorted(set(args.required) - {read['path'] for read in reads})
    print(json.dumps({'database_main_sha256': before_hash, 'opaque_blobs': opaque_blobs,
                      'reads': reads, 'missing': missing}, indent=2))
    return bool(missing)


if __name__ == '__main__':
    raise SystemExit(main())
