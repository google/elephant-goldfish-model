# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Exercise native OpenCode delegation with a scripted local model.

This checks transport and permission behavior, not model compliance or full
workflow execution. The only data sent to the mock is synthetic fixture data.
"""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
from typing import Any

MARKER = 'EGM_PARENT_ONLY_SENTINEL'
SECRET = 'EGM_SYNTHETIC_SECRET'
REQUESTS: list[dict[str, Any]] = []


class MockProvider(BaseHTTPRequestHandler):
    fixture = ''

    def log_message(self, _format: str, *_args: object) -> None:
        pass

    def do_POST(self) -> None:
        request = json.loads(
            self.rfile.read(int(self.headers['Content-Length']))
        )
        REQUESTS.append(request)
        tools = {tool['function']['name'] for tool in request.get('tools', [])}
        has_result = any(
            message.get('role') == 'tool' for message in request['messages']
        )
        delta = {'role': 'assistant', 'content': 'SCRIPTED_COMPLETION'}
        finish = 'stop'
        if not has_result and 'task' in tools:
            delta = self.call(
                'task',
                {
                    'description': 'Probe child isolation',
                    'subagent_type': 'egm-zoom-out',
                    'prompt': 'Read the synthetic fixture .env file.',
                },
            )
            finish = 'tool_calls'
        elif not has_result and 'read' in tools:
            delta = self.call('read', {'filePath': self.fixture})
            finish = 'tool_calls'
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.end_headers()
        for payload in (delta, {}):
            event = {
                'id': 'synthetic',
                'object': 'chat.completion.chunk',
                'created': 1,
                'model': 'fixture',
                'choices': [
                    {
                        'index': 0,
                        'delta': payload,
                        'finish_reason': finish if not payload else None,
                    }
                ],
            }
            self.wfile.write(('data: ' + json.dumps(event) + '\n\n').encode())
        self.wfile.write(b'data: [DONE]\n\n')

    @staticmethod
    def call(name: str, arguments: dict[str, str]) -> dict[str, Any]:
        return {
            'role': 'assistant',
            'tool_calls': [
                {
                    'index': 0,
                    'id': 'fixture-call',
                    'type': 'function',
                    'function': {
                        'name': name,
                        'arguments': json.dumps(arguments),
                    },
                }
            ],
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--opencode', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source, binary = args.source.resolve(), args.opencode.resolve()
    version = subprocess.check_output(
        [str(binary), '--version'], text=True
    ).strip()
    assert version == '1.18.29', f'Unexpected OpenCode version: {version}'
    sha = subprocess.check_output(
        ['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True
    ).strip()
    status = subprocess.check_output(
        ['git', '-C', str(source), 'status', '--porcelain', '--untracked-files=all'],
        text=True,
    )
    assert not status, 'Source contains staged, unstaged, or untracked changes'
    args.output.mkdir(parents=True, exist_ok=False)
    server = ThreadingHTTPServer(('127.0.0.1', 0), MockProvider)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with tempfile.TemporaryDirectory(prefix='egm-native-probe-') as root:
            root = Path(root)
            project, home, install = (
                root / 'project',
                root / 'home',
                root / 'install',
            )
            project.mkdir()
            home.mkdir()
            (project / '.env').write_text(SECRET + '\n')
            MockProvider.fixture = str(project / '.env')
            subprocess.run(
                [
                    'python3',
                    str(source / 'adapters/opencode/install.py'),
                    str(install),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                timeout=60,
            )
            config = json.loads((install / 'opencode.json').read_text())
            config['provider'] = {
                'fixture': {
                    'npm': '@ai-sdk/openai-compatible',
                    'name': 'fixture',
                    'options': {
                        'baseURL': f'http://127.0.0.1:{server.server_port}/v1',
                        'apiKey': 'fixture',
                    },
                    'models': {'fixture': {'name': 'fixture'}},
                }
            }
            config['model'] = 'fixture/fixture'
            config_path = root / 'config.json'
            config_path.write_text(json.dumps(config))
            env = {
                'PATH': os.environ.get('PATH', '/usr/bin:/bin'),
                'HOME': str(home),
                'XDG_CONFIG_HOME': str(home / 'config'),
                'XDG_DATA_HOME': str(home / 'data'),
                'XDG_CACHE_HOME': str(home / 'cache'),
                'OPENCODE_CONFIG': str(config_path),
            }
            result = subprocess.run(
                [
                    str(binary),
                    'run',
                    '--format',
                    'json',
                    '--model',
                    'fixture/fixture',
                    '--agent',
                    'egm',
                    f'Parent-only marker: {MARKER}. Delegate without it.',
                ],
                cwd=project,
                env=env,
                text=True,
                capture_output=True,
                timeout=180,
            )
            (args.output / 'trace.jsonl').write_text(result.stdout)
            (args.output / 'stderr.txt').write_text(result.stderr)
            assert (
                result.returncode == 0
            ), f'OpenCode exited {result.returncode}; inspect stderr.txt'
            trace = [
                json.loads(line)
                for line in result.stdout.splitlines()
                if line.strip()
            ]
            tasks = [
                e
                for e in trace
                if e.get('type') == 'tool_use'
                and e['part'].get('tool') == 'task'
            ]
            assert (
                len(tasks) == 1
                and tasks[0]['part']['state']['status'] == 'completed'
            ), 'No completed native task'
            task = tasks[0]['part']['state']
            assert MARKER not in json.dumps(
                task['input']
            ), 'Parent marker passed to child'
            assert (
                task['metadata']['sessionId']
                != task['metadata']['parentSessionId']
            ), 'Child reused parent session'
            parent_requests = [
                r
                for r in REQUESTS
                if 'task'
                in {t['function']['name'] for t in r.get('tools', [])}
            ]
            assert any(
                MARKER in json.dumps(r) for r in parent_requests
            ), 'Parent marker did not reach provider'
            children = [
                r
                for r in REQUESTS
                if 'read'
                in {t['function']['name'] for t in r.get('tools', [])}
                and 'task'
                not in {t['function']['name'] for t in r.get('tools', [])}
            ]
            assert children, 'No native child provider request observed'
            assert all(
                task['input']['prompt'] in json.dumps(r) for r in children
            ), 'Child request does not match task prompt'
            assert all(
                MARKER not in json.dumps(r) for r in children
            ), 'Parent marker reached child'
            assert all(
                {t['function']['name'] for t in r['tools']}
                == {'read', 'glob', 'grep'}
                for r in children
            ), 'Unexpected child tools'
            results = [
                json.dumps(m.get('content'))
                for r in children
                for m in r['messages']
                if m.get('role') == 'tool'
            ]
            assert results, 'No child tool result observed'
            observations = {
                'parent_marker_seen_in_parent': True,
                'native_task_input': task['input'],
                'native_task_metadata': task['metadata'],
                'child_tools': sorted(
                    {t['function']['name'] for t in children[0]['tools']}
                ),
                'child_marker_present': any(
                    MARKER in json.dumps(r) for r in children
                ),
                'child_tool_results': results,
            }
            (args.output / 'child-observations.json').write_text(
                json.dumps(observations, indent=2) + '\n'
            )
            assert all(
                SECRET not in r for r in results
            ), 'Synthetic secret reached child'
            assert any(
                'prevents you from using this specific tool call' in r
                for r in results
            ), 'No native denial result'
            summary = {
                'head': sha,
                'opencode_version': version,
                'model': 'scripted local mock',
                'native_child_completed': True,
                'child_tools': ['glob', 'grep', 'read'],
                'parent_marker_seen_in_parent': True,
                'parent_marker_in_child': False,
                'fixture_env_read': 'denied',
                'scope': (
                    'One scripted delegation and one synthetic read; not full '
                    'workflow, model behavior, or general isolation'
                ),
            }
            (args.output / 'summary.json').write_text(
                json.dumps(summary, indent=2) + '\n'
            )
            print(json.dumps(summary, indent=2))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=10)


if __name__ == '__main__':
    main()
