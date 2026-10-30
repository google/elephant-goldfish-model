# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Exercise native reviewer isolation using a scripted, local provider.

This probe uses no model. It does not verify workflow or approval behavior.
"""

import http.server
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
from typing import Any
import uuid


PACKAGE = Path(__file__).resolve().parents[2]
CHILD_TAG = 'EGM_CHILD_CONTROLLED'


def tool_call(call_id: str, name: str, arguments: dict[str, str]) -> dict[str, Any]:
    return {
        'id': call_id,
        'type': 'function',
        'function': {'name': name, 'arguments': json.dumps(arguments)},
    }


def main() -> None:
    cli = shutil.which('copilot')
    assert cli, 'Copilot CLI is required; the controlled probe must not skip'
    version = subprocess.check_output([cli, '--version'], text=True)
    assert 'GitHub Copilot CLI 1.0.82.' in version, version

    marker = 'PRIVATE-' + uuid.uuid4().hex
    observations: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix='egm-copilot-controlled-') as directory:
        root = Path(directory)

        class Provider(http.server.BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: object) -> None:
                pass

            def do_POST(self) -> None:
                payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                messages = payload['messages']
                names = [tool['function']['name'] for tool in payload.get('tools', [])]
                child = any(CHILD_TAG in str(msg.get('content', '')) for msg in messages)
                tool_results = sum(msg.get('role') == 'tool' for msg in messages)
                last = messages[-1]
                observations.append({
                    'child': child,
                    'marker': marker in json.dumps(messages),
                    'tools': names,
                    'last_tool_id': last.get('tool_call_id'),
                    'last_tool_content': last.get('content', ''),
                })

                if child and tool_results == 0:
                    call = tool_call('call_read', 'view', {
                        'path': str(PACKAGE / 'agents/zoom_out.md'),
                    })
                elif child and tool_results == 1:
                    call = tool_call('call_forbidden', 'create', {
                        'path': str(root / 'copilot-forbidden-write'),
                        'file_text': 'unexpected',
                    })
                elif not child and tool_results == 0:
                    call = tool_call('call_child', 'task', {
                        'description': 'Controlled child probe',
                        'agent_type': 'egm:egm-zoom-out',
                        'mode': 'sync',
                        'name': 'controlled-probe',
                        'prompt': CHILD_TAG + ': read the canonical persona and reply UNKNOWN.',
                    })
                else:
                    call = None

                content = 'UNKNOWN' if child else 'DONE'
                message: dict[str, Any] = {'role': 'assistant', 'content': content}
                if call:
                    message = {'role': 'assistant', 'content': None, 'tool_calls': [call]}
                finish = 'tool_calls' if call else 'stop'
                response = {
                    'id': 'chatcmpl-test', 'object': 'chat.completion', 'created': 1,
                    'model': 'gpt-4.1',
                    'choices': [{'index': 0, 'message': message, 'finish_reason': finish}],
                    'usage': {'prompt_tokens': 10, 'completion_tokens': 10, 'total_tokens': 20},
                }
                self.send_response(200)
                if payload.get('stream'):
                    self.send_header('Content-Type', 'text/event-stream')
                    self.end_headers()
                    delta: dict[str, Any] = {'role': 'assistant', 'content': content}
                    if call:
                        delta = {'role': 'assistant', 'content': None,
                                 'tool_calls': [{'index': 0, **call}]}
                    chunk = {
                        'id': 'chatcmpl-test', 'object': 'chat.completion.chunk',
                        'created': 1, 'model': 'gpt-4.1',
                        'choices': [{'index': 0, 'delta': delta, 'finish_reason': None}],
                    }
                    self.wfile.write(('data: ' + json.dumps(chunk) + '\n\n').encode())
                    chunk['choices'][0]['delta'] = {}
                    chunk['choices'][0]['finish_reason'] = finish
                    final = 'data: ' + json.dumps(chunk) + '\n\ndata: [DONE]\n\n'
                    self.wfile.write(final.encode())
                else:
                    body = json.dumps(response).encode()
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)

        with http.server.ThreadingHTTPServer(('127.0.0.1', 0), Provider) as server:
            threading.Thread(target=server.serve_forever, daemon=True).start()
            env = {
                'HOME': directory,
                'PATH': '/usr/local/bin:/usr/bin:/bin',
                'COPILOT_HOME': str(root / 'profile'),
                'COPILOT_OFFLINE': 'true',
                'COPILOT_PROVIDER_BASE_URL': f'http://127.0.0.1:{server.server_port}/v1',
                'COPILOT_MODEL': 'gpt-4.1',
            }
            args = [
                cli, '--no-auto-update', '--no-custom-instructions',
                '--disable-builtin-mcps', '--plugin-dir', str(PACKAGE),
                '--add-dir', str(PACKAGE), '--agent', 'egm:egm',
                '--allow-all-tools', '--output-format', 'json',
                '-p', f'Parent-only marker: {marker}. Invoke the controlled reviewer.',
            ]
            result = subprocess.run(
                args, cwd=root, env=env, text=True, capture_output=True, timeout=90,
            )
            server.shutdown()

        events = [json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
        children = [item for item in observations if item['child']]
        assert result.returncode == 0, result.stderr[-500:]
        assert children, 'Native child did not reach provider'
        assert any(item['marker'] and 'create' in item['tools']
                   for item in observations if not item['child']), 'Parent control missing'
        assert not any(item['marker'] for item in children), 'Marker appeared in child request'
        assert all(item['tools'] == ['view'] for item in children), 'Unexpected child tools'
        assert any(
            event['type'] == 'tool.execution_complete'
            and event['data'].get('toolCallId') == 'call_child'
            and event['data'].get('success')
            and event['data'].get('result', {}).get('content') == 'UNKNOWN'
            for event in events
        ), 'Native foreground child did not return'
        assert any(
            event['type'] == 'tool.execution_complete'
            and event['data'].get('success')
            and event['data'].get('parentToolCallId') == 'call_child'
            and event['data'].get('toolCallId') == 'call_read'
            and 'name: egm-zoom-out' in event['data'].get('result', {}).get('content', '')
            for event in events
        ), 'No successful child persona read'
        assert not (root / 'copilot-forbidden-write').exists(), 'Reviewer created a file'
        assert any(
            item['last_tool_id'] == 'call_forbidden'
            and 'does not exist' in str(item['last_tool_content']).lower()
            for item in children
        ), 'No forbidden-tool failure'
        print('PASS: child context, persona read, and forced write denial')


if __name__ == '__main__':
    main()
