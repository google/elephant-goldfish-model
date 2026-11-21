#!/usr/bin/env python3
# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Correlate native Cursor ReadFile calls and successes in one child store.

With --absent, also scan every cell of the closed store for a parent-only
canary marker. Exit 0 passes, 1 fails (missing read or marker found), and
3 is inconclusive (a cell uses a compression format this tool cannot search).
"""

import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import zlib

INCONCLUSIVE = 3
# Magic numbers of compressed formats that the standard library cannot decode.
UNSEARCHABLE_MAGIC = {b'\x28\xb5\x2f\xfd': 'zstd', b'\x04\x22\x4d\x18': 'lz4'}


def marker_forms(marker: str) -> dict[str, bytes]:
    """Byte encodings under which a stored copy of the marker could appear."""
    raw = marker.encode()
    forms = {'utf-8': raw, 'utf-16-le': marker.encode('utf-16-le')}
    # Base64 of any stream holding the marker contains the encoding of the
    # marker's 3-byte-aligned middle for one of three alignments.
    for start in range(3):
        chunk = raw[start:]
        forms[f'base64+{start}'] = base64.b64encode(chunk[:len(chunk) - len(chunk) % 3])
    return forms


def expand(cell: bytes) -> tuple[list[bytes], str | None]:
    """Return searchable byte views of a cell, or the name of an opaque codec."""
    views = [cell]
    for magic, codec in UNSEARCHABLE_MAGIC.items():
        if cell.startswith(magic):
            return views, codec
    for decode in (gzip.decompress, zlib.decompress):
        try:
            views.append(decode(cell))
        except (OSError, EOFError, zlib.error):
            continue
    return views, None


def scan_canaries(connection: sqlite3.Connection, markers: list[str]) -> dict:
    forms = {marker: marker_forms(marker) for marker in markers}
    found, unsearchable, cells = [], [], 0
    tables = [name for (name,) in connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'")]
    for table in tables:
        quoted = '"' + table.replace('"', '""') + '"'
        cursor = connection.execute(f'SELECT rowid, * FROM {quoted}')
        columns = [column[0] for column in cursor.description][1:]
        for rowid, *values in cursor:
            for column, value in zip(columns, values):
                if value is None or isinstance(value, (int, float)):
                    continue
                cells += 1
                data = value.encode() if isinstance(value, str) else bytes(value)
                views, codec = expand(data)
                if codec:
                    unsearchable.append({'table': table, 'column': column,
                                         'rowid': rowid, 'codec': codec})
                for index, marker in enumerate(markers):
                    for encoding, needle in forms[marker].items():
                        if needle and any(needle in view for view in views):
                            found.append({'marker_index': index, 'table': table,
                                          'column': column, 'rowid': rowid,
                                          'encoding': encoding})
    status = 'found' if found else 'inconclusive' if unsearchable else 'absent'
    return {'status': status, 'markers_checked': len(markers), 'cells_scanned': cells,
            'found': found, 'unsearchable': unsearchable}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('database', type=Path)
    parser.add_argument('--required', action='append', default=[])
    parser.add_argument('--absent', action='append', default=[],
                        help='parent-only canary marker that must not appear')
    args = parser.parse_args()
    if not args.required and not args.absent:
        parser.error('provide --required, --absent, or both')
    for marker in args.absent:
        if not re.fullmatch(r'[A-Za-z0-9-]{16,}', marker):
            parser.error('a canary marker needs 16 or more ASCII letters, digits, or -')
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
    canary = scan_canaries(connection, args.absent) if args.absent else None
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
    report = {'database_main_sha256': before_hash, 'opaque_blobs': opaque_blobs,
              'reads': reads, 'missing': missing}
    if canary is not None:
        report['canary'] = canary  # Never echoes the marker itself.
    print(json.dumps(report, indent=2))
    if missing or (canary and canary['status'] == 'found'):
        return 1
    return INCONCLUSIVE if canary and canary['status'] == 'inconclusive' else 0


if __name__ == '__main__':
    raise SystemExit(main())
