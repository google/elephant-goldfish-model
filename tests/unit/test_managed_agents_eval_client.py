# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for tools.managed_agents_eval.client using loopback HTTP mock."""

from __future__ import annotations

import email.message
import email.parser
import http.server
import json
import os
import pathlib
import tempfile
import threading
from typing import Any
import unittest
from unittest import mock

from tools.managed_agents_eval import client as ma_client


class _MockGatewayState:

  def __init__(self) -> None:
    self.requests: list[dict[str, Any]] = []
    self.workspaces_payload: Any = {
        "data": [{"id": "wrkspc_test01", "name": "EGM Test Workspace"}]
    }
    self.sse_streams: list[list[tuple[str, str]]] = []
    self.default_events: list[tuple[str, dict[str, Any]]] = [
        ("agent.thinking", {"type": "agent.thinking", "id": "ev_1"}),
        (
            "agent.tool_use",
            {"type": "agent.tool_use", "id": "tu_1", "name": "bash"},
        ),
        (
            "agent.tool_result",
            {
                "type": "agent.tool_result",
                "id": "tr_1",
                "tool_use_id": "tu_1",
                "is_error": False,
            },
        ),
        (
            "agent.message",
            {
                "type": "agent.message",
                "id": "msg_1",
                "content": [{"type": "text", "text": "Verified output."}],
            },
        ),
        (
            "span.model_request_end",
            {
                "type": "span.model_request_end",
                "id": "sp_1",
                "model_usage": {
                    "input_tokens": 120,
                    "output_tokens": 45,
                    "cache_read_input_tokens": 30,
                    "cache_creation_input_tokens": 10,
                },
            },
        ),
        (
            "span.outcome_evaluation_end",
            {
                "type": "span.outcome_evaluation_end",
                "id": "oe_1",
                "outcome_id": "outc_test01",
                "result": "satisfied",
                "explanation": "All criteria met cleanly.",
                "iteration": 0,
                "usage": {
                    "input_tokens": 50,
                    "output_tokens": 20,
                    "cache_read_input_tokens": 0,
                    "cache_creation_input_tokens": 0,
                },
            },
        ),
        (
            "session.status_idle",
            {
                "type": "session.status_idle",
                "id": "idle_1",
                "stop_reason": {"type": "end_turn"},
            },
        ),
    ]


def _make_handler(state: _MockGatewayState):
  class _MockHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format: str, *args: Any) -> None:
      return

    def _record_and_read(self) -> tuple[bytes, dict[str, str]]:
      length = int(self.headers.get("Content-Length", "0") or "0")
      body = self.rfile.read(length) if length > 0 else b""
      headers_lower = {k.lower(): v for k, v in self.headers.items()}
      state.requests.append({
          "method": self.command,
          "path": self.path,
          "headers": headers_lower,
          "body": body,
      })
      return body, headers_lower

    def _send_json(self, status: int, obj: Any) -> None:
      raw = json.dumps(obj).encode("utf-8")
      self.send_response(status)
      self.send_header("Content-Type", "application/json")
      self.send_header("Content-Length", str(len(raw)))
      self.end_headers()
      self.wfile.write(raw)

    def do_GET(self) -> None:
      _, _ = self._record_and_read()
      if self.path == (
          "/v1/projects/test-project-123/locations/global/"
          "claudeOrganization/invoke/v1/organizations/workspaces"
      ):
        self._send_json(200, state.workspaces_payload)
        return
      if self.path.endswith("/v1/sessions/sess_test01/events/stream?beta=true"):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        if state.sse_streams:
          raw_frames = state.sse_streams.pop(0)
          for ev_name, data_text in raw_frames:
            if ev_name == ":comment":
              frame = f": {data_text}\n\n"
            else:
              frame = f"event: {ev_name}\ndata: {data_text}\n\n"
            self.wfile.write(frame.encode("utf-8"))
            self.wfile.flush()
        else:
          for ev_name, payload in state.default_events:
            frame = (
                f"event: {ev_name}\ndata: {json.dumps(payload)}\n\n"
            ).encode("utf-8")
            self.wfile.write(frame)
            self.wfile.flush()
        return
      self._send_json(404, {"error": "not_found", "path": self.path})

    def do_POST(self) -> None:
      body, _ = self._record_and_read()
      if self.path.endswith("/v1/environments?beta=true"):
        self._send_json(200, {"id": "env_test01", "name": "test-env"})
        return
      if self.path.endswith("/v1/files?beta=true"):
        self._send_json(200, {"id": "file_test01", "bytes": len(body)})
        return
      if self.path.endswith("/v1/skills?beta=true"):
        self._send_json(200, {"id": "skill_test01"})
        return
      if self.path.endswith("/v1/agents?beta=true"):
        parsed = json.loads(body.decode("utf-8"))
        self._send_json(
            200,
            {
                "id": "agent_test01",
                "has_multiagent": "multiagent" in parsed,
            },
        )
        return
      if self.path.endswith("/v1/sessions?beta=true"):
        self._send_json(200, {"id": "sess_test01"})
        return
      if self.path.endswith("/v1/sessions/sess_test01/events?beta=true"):
        self._send_json(200, {"accepted": True})
        return
      self._send_json(404, {"error": "not_found", "path": self.path})

  return _MockHandler


def _parse_multipart_parts(
    content_type: str, body: bytes
) -> list[tuple[str, str | None, bytes]]:
  raw_msg = (
      f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode(
          "utf-8"
      )
      + body
  )
  msg = email.parser.BytesParser().parsebytes(raw_msg)
  parts: list[tuple[str, str | None, bytes]] = []
  raw_parts = msg.get_payload()
  if not isinstance(raw_parts, list):
    return parts
  for part in raw_parts:
    if not isinstance(part, email.message.Message):
      continue
    raw_name = part.get_param("name", header="content-disposition")
    name = raw_name if isinstance(raw_name, str) else ""
    filename = part.get_filename()
    decoded = part.get_payload(decode=True)
    payload = decoded if isinstance(decoded, bytes) else b""
    parts.append((name, filename, payload))
  return parts


class ClientTest(unittest.TestCase):

  def setUp(self) -> None:
    super().setUp()
    self.state = _MockGatewayState()
    self.server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), _make_handler(self.state)
    )
    port = self.server.server_address[1]
    self.base_origin = f"http://127.0.0.1:{port}"
    self.thread = threading.Thread(
        target=self.server.serve_forever, daemon=True
    )
    self.thread.start()

  def tearDown(self) -> None:
    self.server.shutdown()
    self.server.server_close()
    super().tearDown()

  def test_token_resolution_and_origin_validation(self) -> None:
    secret_token = "tok_synthetic_secret_value_do_not_leak"
    with tempfile.TemporaryDirectory() as tmp_dir:
      token_file = pathlib.Path(tmp_dir) / "agent_oauth_token"
      token_file.write_text(f"  {secret_token}\n", encoding="utf-8")
      with mock.patch.dict(
          os.environ,
          {
              "CLOUDSDK_AUTH_ACCESS_TOKEN_FILE": str(token_file),
              "GOOGLE_OAUTH_ACCESS_TOKEN": "should_not_be_used",
          },
      ):
        resolved = ma_client.resolve_gcloud_access_token()
        self.assertEqual(resolved, secret_token)

        client = ma_client.ClaudeManagedAgentsClient(
            project_id="test-project-123",
            workspace_id="wrkspc_test01",
            base_origin=self.base_origin,
        )
        self.assertNotIn(secret_token, repr(client))

        token_file.write_text("   \n", encoding="utf-8")
        with self.assertRaises(RuntimeError) as ctx:
          ma_client.resolve_gcloud_access_token()
        self.assertNotIn(secret_token, str(ctx.exception))

    with self.assertRaises(ValueError):
      ma_client.ClaudeManagedAgentsClient(
          project_id="test-project-123",
          base_origin="http://claude.googleapis.com",
      )
    with self.assertRaises(ValueError):
      ma_client.ClaudeManagedAgentsClient(
          project_id="test-project-123",
          base_origin="file:///etc/passwd",
      )
    with self.assertRaises(ValueError):
      ma_client.ClaudeManagedAgentsClient(
          project_id="test-project-123",
          base_origin="ftp://127.0.0.1:8080",
      )
    with self.assertRaises(ValueError):
      ma_client.ClaudeManagedAgentsClient(
          project_id="test-project-123",
          base_origin="ws://localhost:8080",
      )
    with self.assertRaises(ValueError):
      ma_client.ClaudeManagedAgentsClient(backend="invalid_backend")

    self.assertEqual(ma_client._extract_text_from_blocks(None), "")

    encoded_client = ma_client.ClaudeManagedAgentsClient(
        project_id="proj/a b",
        workspace_id="ws/1",
        location="us/east",
        base_origin="https://claude.googleapis.com",
        token_provider=lambda: "tok",
    )
    self.assertIn("proj%2Fa%20b", encoded_client.workspace_invoke_url)
    self.assertIn("ws%2F1", encoded_client.workspace_invoke_url)

    empty_proj = ma_client.ClaudeManagedAgentsClient(
        project_id="",
        workspace_id="wrkspc_test01",
        token_provider=lambda: "tok",
    )
    with self.assertRaises(ValueError):
      _ = empty_proj.org_invoke_url
    with self.assertRaises(ValueError):
      _ = empty_proj.workspace_invoke_url

  def test_anthropic_backend_headers_routing_and_key_errors(self) -> None:
    default_ant = ma_client.ClaudeManagedAgentsClient(backend="anthropic")
    self.assertEqual(
        default_ant.base_origin, ma_client.ANTHROPIC_DEFAULT_BASE_ORIGIN
    )
    self.assertEqual(
        default_ant.workspace_invoke_url, "https://api.anthropic.com"
    )
    with self.assertRaises(ValueError):
      _ = default_ant.org_invoke_url
    with self.assertRaises(ValueError):
      default_ant.list_workspaces()

    with mock.patch.dict(os.environ, {}, clear=True):
      with self.assertRaises(RuntimeError):
        ma_client.resolve_anthropic_api_key()

    with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "   "}, clear=True):
      with self.assertRaises(RuntimeError):
        ma_client.resolve_anthropic_api_key()

    api_key = "sk-ant-synthetic-test-key"
    with mock.patch.dict(
        os.environ, {"ANTHROPIC_API_KEY": f" {api_key} "}, clear=True
    ):
      self.assertEqual(ma_client.resolve_anthropic_api_key(), api_key)
      ant_client = ma_client.ClaudeManagedAgentsClient(
          backend="anthropic",
          base_origin=self.base_origin,
      )
      self.assertNotIn(api_key, repr(ant_client))

      env = ant_client.create_environment(name="ant-env", allowed_hosts=[])
      self.assertEqual(env["id"], "env_test01")
      outcome = ant_client.run_eval_session(
          agent_id="agent_test01",
          environment_id="env_test01",
          user_prompt="Hello direct API.",
      )
      self.assertEqual(outcome.final_response, "Verified output.")

    paths = [r["path"] for r in self.state.requests]
    self.assertEqual(
        paths,
        [
            "/v1/environments?beta=true",
            "/v1/sessions?beta=true",
            "/v1/sessions/sess_test01/events/stream?beta=true",
        ],
    )
    for req in self.state.requests:
      self.assertEqual(req["headers"].get("x-api-key"), api_key)
      self.assertNotIn("authorization", req["headers"])

  def test_end_to_end_gateway_endpoints_and_security_hardening(self) -> None:
    client = ma_client.ClaudeManagedAgentsClient(
        project_id="test-project-123",
        workspace_id="wrkspc_test01",
        base_origin=self.base_origin,
        token_provider=lambda: "tok_test_jdoe",
    )

    workspaces = client.list_workspaces()
    self.assertEqual(len(workspaces), 1)
    self.assertEqual(workspaces[0]["id"], "wrkspc_test01")

    self.state.workspaces_payload = [{"id": "wrkspc_list01"}]
    self.assertEqual(client.list_workspaces(), [{"id": "wrkspc_list01"}])
    self.state.workspaces_payload = {
        "data": [{"id": "wrkspc_test01", "name": "EGM Test Workspace"}]
    }

    env = client.create_environment(
        name="egm-eval-env",
        pip_packages=["pyyaml"],
        allowed_hosts=["api.github.com"],
    )
    self.assertEqual(env["id"], "env_test01")
    env_req = self.state.requests[-1]
    self.assertEqual(
        env_req["headers"]["anthropic-beta"], ma_client.BETA_MANAGED_AGENTS
    )
    env_body = json.loads(env_req["body"].decode("utf-8"))
    self.assertEqual(env_body["config"]["networking"]["type"], "limited")
    self.assertTrue(env_body["config"]["networking"]["allow_package_managers"])
    self.assertEqual(
        env_body["config"]["packages"],
        {"type": "packages", "pip": ["pyyaml"]},
    )

    body_mp, ctype_mp = ma_client._encode_multipart(
        fields=[('evil"\r\nX-Inject: 1', "val")],
        files=[('f"\r\n', 'a"\r\n.txt', b"x", "text/plain\r\nX-Bad: 1")],
    )
    self.assertNotIn(b"\r\nX-Inject:", body_mp)
    self.assertNotIn(b"\r\nX-Bad:", body_mp)
    self.assertIn(b'name="evilX-Inject: 1"', body_mp)
    self.assertTrue(ctype_mp.startswith("multipart/form-data; boundary="))
    boundary = ctype_mp.split("boundary=", 1)[1]
    self.assertTrue(body_mp.endswith(f"--{boundary}--\r\n".encode("utf-8")))

    bundle_resp = client.upload_bundle(b"fake-targz-payload")
    self.assertEqual(bundle_resp["id"], "file_test01")
    file_req = self.state.requests[-1]
    self.assertEqual(
        file_req["headers"]["anthropic-beta"], ma_client.BETA_FILES
    )
    parts = _parse_multipart_parts(
        file_req["headers"]["content-type"], file_req["body"]
    )
    self.assertEqual(
        parts, [("file", "egm_plugin.tar.gz", b"fake-targz-payload")]
    )

    with self.assertRaises(ValueError):
      client.upload_bundle(b"x" * (ma_client.MAX_BUNDLE_BYTES + 1))

    with tempfile.TemporaryDirectory() as tmp_dir:
      tmp_path = pathlib.Path(tmp_dir)
      outside = tmp_path / "secret.txt"
      outside.write_text("SECRET", encoding="utf-8")

      skill_dir = tmp_path / "egm_zoom_out"
      skill_dir.mkdir()
      (skill_dir / "SKILL.md").write_text("# Zoom Out\n", encoding="utf-8")
      (skill_dir / "notes.md").write_text("helper", encoding="utf-8")
      (skill_dir / "test_scenarios.yaml").write_text("rubric", encoding="utf-8")
      (skill_dir / "EVAL.txtpb").write_text("rubric", encoding="utf-8")
      (skill_dir / "EVAL.textproto").write_text("rubric", encoding="utf-8")
      (skill_dir / "eval_results").mkdir()
      (skill_dir / "eval_results" / "out.json").write_text(
          "{}", encoding="utf-8"
      )
      (skill_dir / "leak.txt").symlink_to(outside)

      skill_resp = client.upload_skill_dir(
          skill_dir, display_title="EGM Zoom Out"
      )
      self.assertEqual(skill_resp["id"], "skill_test01")
      skill_req = self.state.requests[-1]
      self.assertEqual(
          skill_req["headers"]["anthropic-beta"], ma_client.BETA_SKILLS
      )
      skill_parts = _parse_multipart_parts(
          skill_req["headers"]["content-type"], skill_req["body"]
      )
      filenames = [p[1] for p in skill_parts if p[0] == "files"]
      self.assertEqual(
          filenames, ["egm_zoom_out/SKILL.md", "egm_zoom_out/notes.md"]
      )

    multi_agent = client.create_agent(
        name="egm-multi",
        model="claude-sonnet-4-6",
        system="You are a coordinator.",
        enable_multiagent=True,
    )
    self.assertTrue(multi_agent["has_multiagent"])
    multi_body = json.loads(self.state.requests[-1]["body"].decode("utf-8"))
    self.assertEqual(
        multi_body["tools"][0]["default_config"], {"enabled": False}
    )
    self.assertEqual(
        multi_body["multiagent"],
        {"type": "coordinator", "agents": [{"type": "self"}]},
    )

    single_agent = client.create_agent(
        name="egm-single",
        model="claude-sonnet-4-6",
        system="You are a single agent.",
        enable_multiagent=False,
    )
    self.assertFalse(single_agent["has_multiagent"])
    single_body = json.loads(self.state.requests[-1]["body"].decode("utf-8"))
    self.assertNotIn("multiagent", single_body)

    outcome = client.run_eval_session(
        agent_id="agent_test01",
        environment_id="env_test01",
        user_prompt="Run zoom out review.",
        outcome_description="Flag over-engineering.",
        rubric_text="- Identify YAGNI violation",
        bundle_file_id="file_test01",
        max_iterations=1,
    )
    self.assertEqual(outcome.session_id, "sess_test01")
    self.assertEqual(outcome.final_response, "Verified output.")
    self.assertEqual(outcome.turn_responses, ["Verified output."])
    self.assertIsNone(outcome.error_message)
    self.assertEqual(outcome.tool_use_count, 1)
    self.assertEqual(outcome.tool_error_count, 0)
    self.assertEqual(outcome.thinking_events, 1)
    self.assertIsNotNone(outcome.outcome_evaluation)
    assert outcome.outcome_evaluation is not None
    self.assertEqual(outcome.outcome_evaluation.result, "satisfied")
    self.assertEqual(
        outcome.outcome_evaluation.explanation, "All criteria met cleanly."
    )
    self.assertEqual(outcome.stop_reason, "end_turn")
    self.assertEqual(outcome.usage.total_tokens, 275)
    self.assertGreaterEqual(outcome.duration_ms, 0)

  def test_multiturn_and_sse_error_and_eof_handling(self) -> None:
    client = ma_client.ClaudeManagedAgentsClient(
        project_id="test-project-123",
        workspace_id="wrkspc_test01",
        base_origin=self.base_origin,
        token_provider=lambda: "tok_test_jdoe",
    )

    self.state.sse_streams = [
        [
            (":comment", "keepalive"),
            ("ping", "ping"),
            (
                "agent.message",
                json.dumps({
                    "type": "agent.message",
                    "id": "m1",
                    "content": [{"type": "text", "text": "Turn one reply?"}],
                }),
            ),
            (
                "session.status_idle",
                json.dumps({
                    "type": "session.status_idle",
                    "id": "i1",
                    "stop_reason": {"type": "end_turn"},
                }),
            ),
        ],
        [
            (
                "agent.message",
                json.dumps({
                    "type": "agent.message",
                    "id": "m2",
                    "content": [{"type": "text", "text": "Turn two reply."}],
                }),
            ),
            (
                "session.status_idle",
                json.dumps({
                    "type": "session.status_idle",
                    "id": "i2",
                    "stop_reason": {"type": "end_turn"},
                }),
            ),
        ],
    ]
    multi_outcome = client.run_eval_session(
        agent_id="agent_test01",
        environment_id="env_test01",
        turns=["Turn 1 prompt", "Turn 2 prompt"],
    )
    self.assertEqual(
        multi_outcome.turn_responses, ["Turn one reply?", "Turn two reply."]
    )
    self.assertIsNone(multi_outcome.error_message)
    event_posts = [
        r
        for r in self.state.requests
        if r["path"].endswith("/events?beta=true")
    ]
    self.assertEqual(len(event_posts), 1)

    self.state.sse_streams = [
        [
            (
                "session.status_terminated",
                json.dumps({"type": "session.status_terminated", "id": "t1"}),
            ),
        ],
    ]
    term_multi = client.run_eval_session(
        agent_id="agent_test01",
        environment_id="env_test01",
        turns=["Turn 1", "Turn 2"],
    )
    self.assertEqual(term_multi.stop_reason, "terminated")
    self.assertIn("before turn 2", term_multi.error_message or "")
    self.assertEqual(len(term_multi.turn_responses), 1)

    self.state.sse_streams = [
        [("error", "gateway overloaded")],
    ]
    err_outcome = client.run_eval_session(
        agent_id="agent_test01",
        environment_id="env_test01",
        turns=["Hello"],
    )
    self.assertIsNotNone(err_outcome.error_message)
    self.assertIn("gateway overloaded", err_outcome.error_message or "")

    self.state.sse_streams = [
        [
            (
                "agent.message",
                json.dumps({
                    "type": "agent.message",
                    "id": "m_eof",
                    "content": [{"type": "text", "text": "partial"}],
                }),
            ),
        ],
    ]
    eof_outcome = client.run_eval_session(
        agent_id="agent_test01",
        environment_id="env_test01",
        turns=["Hello"],
    )
    self.assertIsNotNone(eof_outcome.error_message)
    self.assertIn("prematurely", eof_outcome.error_message or "")

  def test_gcloud_fallback_and_error_branches(self) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
      tmp_path = pathlib.Path(tmp_dir)
      missing_file = tmp_path / "does_not_exist"
      fake_gcloud = tmp_path / "fake_gcloud.sh"
      fake_gcloud.write_text(
          "#!/usr/bin/env bash\n"
          'if [[ "$2" == "application-default" ]]; then exit 1; fi\n'
          'echo "tok_from_gcloud_fallback"\n',
          encoding="utf-8",
      )
      fake_gcloud.chmod(0o755)

      failing_gcloud = tmp_path / "fail_gcloud.sh"
      failing_gcloud.write_text(
          "#!/usr/bin/env bash\nexit 1\n", encoding="utf-8"
      )
      failing_gcloud.chmod(0o755)

      with mock.patch.dict(
          os.environ,
          {"CLOUDSDK_AUTH_ACCESS_TOKEN_FILE": str(missing_file)},
          clear=False,
      ):
        with self.assertRaises(RuntimeError):
          ma_client.resolve_gcloud_access_token()

      env_only = {k: v for k, v in os.environ.items()}
      env_only.pop("CLOUDSDK_AUTH_ACCESS_TOKEN_FILE", None)
      env_only["GOOGLE_OAUTH_ACCESS_TOKEN"] = "tok_from_env"
      with mock.patch.dict(os.environ, env_only, clear=True):
        self.assertEqual(
            ma_client.resolve_gcloud_access_token(), "tok_from_env"
        )

      clean_env = {
          k: v
          for k, v in os.environ.items()
          if k not in (
              "CLOUDSDK_AUTH_ACCESS_TOKEN_FILE",
              "GOOGLE_OAUTH_ACCESS_TOKEN",
          )
      }
      with mock.patch.dict(os.environ, clean_env, clear=True):
        self.assertEqual(
            ma_client.resolve_gcloud_access_token(str(fake_gcloud)),
            "tok_from_gcloud_fallback",
        )
        with self.assertRaises(RuntimeError):
          ma_client.resolve_gcloud_access_token(str(failing_gcloud))

    no_ws = ma_client.ClaudeManagedAgentsClient(
        project_id="test-project-123",
        workspace_id=None,
        base_origin=self.base_origin,
        token_provider=lambda: "",
    )
    with self.assertRaises(ValueError):
      _ = no_ws.workspace_invoke_url
    with self.assertRaises(RuntimeError):
      no_ws.list_workspaces()

    client = ma_client.ClaudeManagedAgentsClient(
        project_id="test-project-123",
        workspace_id="wrkspc_test01",
        base_origin=self.base_origin,
        token_provider=lambda: "tok_test_jdoe",
    )

    env = client.create_environment(
        name="unrestricted-env", metadata={"suite": "egm"}
    )
    self.assertEqual(env["id"], "env_test01")
    env_body = json.loads(self.state.requests[-1]["body"].decode("utf-8"))
    self.assertEqual(env_body["config"]["networking"]["type"], "unrestricted")
    self.assertEqual(env_body["metadata"], {"suite": "egm"})

    agent = client.create_agent(
        name="web-agent",
        model="claude-opus-4-6",
        system="Sys",
        skill_ids=["skill_test01"],
        enable_web=True,
        effort="",
        metadata={"k": "v"},
    )
    self.assertEqual(agent["id"], "agent_test01")
    agent_body = json.loads(self.state.requests[-1]["body"].decode("utf-8"))
    self.assertEqual(agent_body["model"], "claude-opus-4-6")
    self.assertEqual(
        agent_body["skills"], [{"type": "custom", "skill_id": "skill_test01"}]
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
      bad_skill = pathlib.Path(tmp_dir) / "bad_skill"
      bad_skill.mkdir()
      with self.assertRaises(ValueError):
        client.upload_skill_dir(bad_skill)

      good_skill = pathlib.Path(tmp_dir) / "good_skill"
      good_skill.mkdir()
      (good_skill / "SKILL.md").write_text("# Good", encoding="utf-8")
      (good_skill / "__pycache__").mkdir()
      (good_skill / "__pycache__" / "a.pyc").write_bytes(b"0")
      (good_skill / "extra.pyc").write_bytes(b"0")
      self.assertEqual(
          client.upload_skill_dir(good_skill)["id"], "skill_test01"
      )

    self.state.sse_streams = [[
        (
            "agent.tool_result",
            json.dumps({
                "type": "agent.tool_result",
                "id": "tr_err",
                "tool_use_id": "tu_1",
                "is_error": True,
            }),
        ),
        (
            "session.status_terminated",
            json.dumps({"type": "session.status_terminated", "id": "term_1"}),
        ),
    ]]
    term_outcome = client.run_eval_session(
        agent_id="agent_test01",
        environment_id="env_test01",
        user_prompt="Prompt",
        outcome_description="Desc",
        rubric_text="Rubric",
        title="Term test",
        metadata={"run": "1"},
    )
    self.assertEqual(term_outcome.tool_error_count, 1)
    self.assertEqual(term_outcome.stop_reason, "terminated")

    with self.assertRaises(ma_client.ClaudeApiError) as err_ctx:
      client._request_json("GET", f"{self.base_origin}/nonexistent")
    self.assertEqual(err_ctx.exception.status_code, 404)


if __name__ == "__main__":
  unittest.main()
