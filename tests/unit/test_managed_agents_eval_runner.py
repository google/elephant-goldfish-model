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

"""Unit tests for tools.managed_agents_eval.runner."""

from __future__ import annotations

import http.server
import io
import json
import os
import pathlib
import tarfile
import tempfile
import threading
from typing import Any
import unittest
from unittest import mock

from tools.managed_agents_eval import runner

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _create_synthetic_repo(root: pathlib.Path) -> None:
  (root / ".claude-plugin").mkdir(parents=True)
  (root / ".claude-plugin" / "plugin.json").write_text(
      json.dumps({"name": "egm", "version": "2.4.1"}), encoding="utf-8"
  )
  (root / "agents").mkdir()
  (root / "agents" / "goldfish.md").write_text(
      "# Goldfish Reviewer", encoding="utf-8"
  )
  (root / "rules").mkdir()
  (root / "rules" / "anti_sycophancy.md").write_text(
      "# Anti Sycophancy", encoding="utf-8"
  )
  (root / ".git").mkdir()
  (root / ".git" / "HEAD").write_text(
      "ref: refs/heads/main\n", encoding="utf-8"
  )

  skill_dir = root / "skills" / "egm_sample"
  skill_dir.mkdir(parents=True)
  (skill_dir / "SKILL.md").write_text("# Sample Skill", encoding="utf-8")
  (skill_dir / "EVAL.txtpb").write_text("secret_rubric", encoding="utf-8")
  (skill_dir / "__pycache__").mkdir()
  (skill_dir / "__pycache__" / "x.pyc").write_bytes(b"pyc")
  (skill_dir / "test_scenarios.yaml").write_text(
      """skill: "egm_sample"
scenarios:
  - scenario_id: "sample_pass_case"
    description: "Passes both satisfied outcome and regex check."
    eval_type: "deterministic"
    system_prompt:
      skill_file: "skills/egm_sample/SKILL.md"
      rules:
        - "rules/anti_sycophancy.md"
    turns:
      - user_input: "Evaluate cache design."
        assertions:
          - type: "required_pattern"
            pattern: "YAGNI"
          - type: "forbidden_pattern"
            pattern: "FORBIDDEN_PHRASE"
  - scenario_id: "sample_forbidden_regex_case"
    description: "Outcome satisfied, but forbidden regex must fail the scenario."
    eval_type: "deterministic"
    system_prompt:
      skill_file: "skills/egm_sample/SKILL.md"
    turns:
      - user_input: "Evaluate forbidden pattern case."
        assertions:
          - type: "forbidden_pattern"
            pattern: "FORBIDDEN_PHRASE"
  - scenario_id: "sample_needs_revision_case"
    description: "Outcome verdict is needs_revision and must fail."
    eval_type: "llm_judge"
    system_prompt:
      skill_file: "skills/egm_sample/SKILL.md"
    turns:
      - user_input: "Evaluate needs revision case."
        rubric:
          prompt: "Check completeness."
          passing_criteria: "No missing sections."
""",
      encoding="utf-8",
  )


class _RunnerMockState:

  def __init__(self) -> None:
    self.agent_payloads: list[dict[str, Any]] = []
    self.env_payloads: list[dict[str, Any]] = []
    self.request_paths: list[str] = []
    self.request_headers: list[dict[str, str]] = []
    self.session_titles: dict[str, str] = {}
    self.turn_index_by_session: dict[str, int] = {}
    self.counter = 0


def _make_runner_handler(state: _RunnerMockState):
  class _Handler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format: str, *args: Any) -> None:
      return

    def _read_body(self) -> bytes:
      state.request_paths.append(self.path)
      state.request_headers.append(
          {k.lower(): v for k, v in self.headers.items()}
      )
      length = int(self.headers.get("Content-Length", "0") or "0")
      return self.rfile.read(length) if length > 0 else b""

    def _send_json(self, status: int, obj: dict[str, Any]) -> None:
      raw = json.dumps(obj).encode("utf-8")
      self.send_response(status)
      self.send_header("Content-Type", "application/json")
      self.send_header("Content-Length", str(len(raw)))
      self.end_headers()
      self.wfile.write(raw)

    def do_GET(self) -> None:
      _ = self._read_body()
      if self.path.endswith("/v1/organizations/workspaces"):
        self._send_json(200, {"data": [{"id": "wrkspc_test01"}]})
        return
      if "/events/stream" in self.path:
        session_id = self.path.split("/v1/sessions/")[1].split("/")[0]
        title = state.session_titles.get(session_id, "")
        turn_idx = state.turn_index_by_session.get(session_id, 0)
        state.turn_index_by_session[session_id] = turn_idx + 1

        if "sample_empty_deterministic" in title:
          events = [
              (
                  "session.status_terminated",
                  {"type": "session.status_terminated", "id": "term1"},
              ),
          ]
        elif "sample_multiturn_case" in title:
          if turn_idx == 0:
            events = [
                (
                    "agent.message",
                    {
                        "type": "agent.message",
                        "id": "m1",
                        "content": [{"type": "text", "text": "HALT_TURN_1"}],
                    },
                ),
                (
                    "session.status_idle",
                    {
                        "type": "session.status_idle",
                        "id": "i1",
                        "stop_reason": {"type": "end_turn"},
                    },
                ),
            ]
          else:
            events = [
                (
                    "agent.message",
                    {
                        "type": "agent.message",
                        "id": "m2",
                        "content": [{"type": "text", "text": "EXEC_TURN_2"}],
                    },
                ),
                (
                    "span.outcome_evaluation_end",
                    {
                        "type": "span.outcome_evaluation_end",
                        "id": "oe2",
                        "outcome_id": "outc_mt",
                        "result": "satisfied",
                        "explanation": "Sequential turns verified.",
                        "iteration": 0,
                        "usage": {
                            "input_tokens": 10,
                            "output_tokens": 5,
                            "cache_read_input_tokens": 0,
                            "cache_creation_input_tokens": 0,
                        },
                    },
                ),
                (
                    "session.status_idle",
                    {
                        "type": "session.status_idle",
                        "id": "i2",
                        "stop_reason": {"type": "end_turn"},
                    },
                ),
            ]
        else:
          if "sample_forbidden_regex_case" in title:
            msg_text = "YAGNI applies, but FORBIDDEN_PHRASE leaked."
            verdict = "satisfied"
            explanation = "Grader thought it passed."
          elif "sample_needs_revision_case" in title:
            msg_text = "Draft missing sections."
            verdict = "needs_revision"
            explanation = "Missing Verification Plan."
          else:
            msg_text = "Flagged YAGNI over-engineering cleanly."
            verdict = "satisfied"
            explanation = "All criteria met."

          events = [
              (
                  "agent.message",
                  {
                      "type": "agent.message",
                      "id": "m1",
                      "content": [{"type": "text", "text": msg_text}],
                  },
              ),
              (
                  "span.model_request_end",
                  {
                      "type": "span.model_request_end",
                      "id": "mr1",
                      "model_usage": {
                          "input_tokens": 100,
                          "output_tokens": 50,
                          "cache_read_input_tokens": 0,
                          "cache_creation_input_tokens": 0,
                      },
                  },
              ),
              (
                  "span.outcome_evaluation_end",
                  {
                      "type": "span.outcome_evaluation_end",
                      "id": "oe1",
                      "outcome_id": "outc_1",
                      "result": verdict,
                      "explanation": explanation,
                      "iteration": 0,
                      "usage": {
                          "input_tokens": 25,
                          "output_tokens": 10,
                          "cache_read_input_tokens": 0,
                          "cache_creation_input_tokens": 0,
                      },
                  },
              ),
              (
                  "session.status_idle",
                  {
                      "type": "session.status_idle",
                      "id": "i1",
                      "stop_reason": {"type": "end_turn"},
                  },
              ),
          ]

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for name, payload in events:
          self.wfile.write(
              f"event: {name}\ndata: {json.dumps(payload)}\n\n".encode("utf-8")
          )
          self.wfile.flush()
        return
      self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:
      body = self._read_body()
      if "/v1/environments" in self.path:
        state.env_payloads.append(json.loads(body.decode("utf-8")))
        self._send_json(200, {"id": "env_test01"})
        return
      if "/v1/files" in self.path:
        self._send_json(200, {"id": "file_test01"})
        return
      if "/v1/skills" in self.path:
        self._send_json(200, {"id": "skill_test01"})
        return
      if "/v1/agents" in self.path:
        state.counter += 1
        state.agent_payloads.append(json.loads(body.decode("utf-8")))
        self._send_json(200, {"id": f"agent_{state.counter}"})
        return
      if self.path.endswith("/events?beta=true"):
        self._send_json(200, {"accepted": True})
        return
      if "/v1/sessions" in self.path:
        state.counter += 1
        sid = f"sess_{state.counter}"
        parsed = json.loads(body.decode("utf-8"))
        state.session_titles[sid] = str(parsed.get("title", ""))
        self._send_json(200, {"id": sid})
        return
      self._send_json(404, {"error": "not_found"})

  return _Handler


class RunnerTest(unittest.TestCase):

  def test_clean_bundle_excludes_rubrics_symlinks_and_detects_version(
      self,
  ) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
      tmp_path = pathlib.Path(tmp_dir)
      outside = tmp_path / "outside_secret.txt"
      outside.write_text("TOP_SECRET", encoding="utf-8")
      root = tmp_path / "repo"
      _create_synthetic_repo(root)
      (root / "rules" / "escape.md").symlink_to(outside)

      self.assertEqual(runner.detect_egm_version(root), "2.4.1")
      (root / ".claude-plugin" / "plugin.json").unlink()
      self.assertEqual(runner.detect_egm_version(root), "0.0.0-dev")

      (root / "rules" / "z_rule.md").write_text("# Z", encoding="utf-8")
      (root / "rules" / "a_rule.md").write_text("# A", encoding="utf-8")

      bundle_bytes, included = runner.build_clean_plugin_bundle(root)
      with tarfile.open(fileobj=io.BytesIO(bundle_bytes), mode="r:gz") as tar:
        names = tar.getnames()

      self.assertEqual(names, included)
      self.assertEqual(included, sorted(included))
      self.assertLess(
          included.index("rules/a_rule.md"),
          included.index("rules/z_rule.md"),
      )
      self.assertIn("skills/egm_sample/SKILL.md", names)
      self.assertIn("agents/goldfish.md", names)
      self.assertNotIn("rules/escape.md", names)
      self.assertNotIn("skills/egm_sample/test_scenarios.yaml", names)
      self.assertNotIn("skills/egm_sample/EVAL.txtpb", names)
      self.assertFalse(any(".git" in n for n in names))
      self.assertFalse(any("__pycache__" in n for n in names))

      with self.assertRaises(ValueError):
        runner.assemble_system_prompt(root, {"skill_file": "/etc/passwd"})
      with self.assertRaises(ValueError):
        runner.assemble_system_prompt(
            root, {"skill_file": "../outside_secret.txt"}
        )
      with self.assertRaises(ValueError):
        runner.assemble_system_prompt(
            root,
            {
                "skill_file": "skills/egm_sample/SKILL.md",
                "rules": ["rules/escape.md"],
            },
        )

  def test_end_to_end_both_modes_and_dry_run_and_summary(self) -> None:
    state = _RunnerMockState()
    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), _make_runner_handler(state)
    )
    port = server.server_address[1]
    base_origin = f"http://127.0.0.1:{port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
      with tempfile.TemporaryDirectory() as tmp_dir:
        root = pathlib.Path(tmp_dir) / "repo"
        out_dir = pathlib.Path(tmp_dir) / "out"
        _create_synthetic_repo(root)

        with mock.patch.dict(
            os.environ, {"GOOGLE_OAUTH_ACCESS_TOKEN": "tok_test_jdoe"}
        ):
          report = runner.run_eval_suite(
              repo_root=root,
              harness_mode="both",
              backend="gcp",
              project_id="test-project-123",
              workspace_id=None,
              base_origin=base_origin,
          )

        self.assertEqual(report.egm_version, "2.4.1")
        self.assertEqual(report.backend, "gcp")
        self.assertEqual(report.workspace_id, "wrkspc_test01")
        self.assertEqual(len(report.results), 6)
        self.assertEqual(
            state.env_payloads[0]["config"]["networking"]["type"], "limited"
        )
        self.assertEqual(
            state.env_payloads[0]["config"]["networking"]["allowed_hosts"], []
        )

        multi_agents = [p for p in state.agent_payloads if "multiagent" in p]
        single_agents = [
            p for p in state.agent_payloads if "multiagent" not in p
        ]
        self.assertEqual(len(multi_agents), 3)
        self.assertEqual(len(single_agents), 3)

        by_key = {(r.scenario_id, r.harness_mode): r for r in report.results}
        self.assertTrue(by_key[("sample_pass_case", "multiagent")].passed)
        self.assertTrue(by_key[("sample_pass_case", "single-agent")].passed)
        self.assertFalse(
            by_key[("sample_forbidden_regex_case", "multiagent")].passed
        )
        self.assertEqual(
            by_key[
                ("sample_forbidden_regex_case", "multiagent")
            ].outcome_verdict,
            "satisfied",
        )
        self.assertFalse(
            by_key[
                ("sample_forbidden_regex_case", "multiagent")
            ].assertion_passed
        )
        self.assertFalse(
            by_key[("sample_needs_revision_case", "single-agent")].passed
        )
        self.assertEqual(
            by_key[
                ("sample_needs_revision_case", "single-agent")
            ].outcome_verdict,
            "needs_revision",
        )

        summary_md = runner.render_markdown_summary(report)
        self.assertIn("- **Backend:** `gcp`", summary_md)
        self.assertIn("- **Project:** `test-project-123`", summary_md)
        self.assertIn("## Version 2.4.1", summary_md)
        self.assertIn("### Harness Mode: multiagent", summary_md)
        self.assertIn("### Harness Mode: single-agent", summary_md)
        self.assertIn("Pass rate is 1/3", summary_md)

        exit_code = runner.main([
            "--repo-root",
            str(root),
            "--harness-mode",
            "both",
            "--dry-run",
            "--output-dir",
            str(out_dir),
        ])
        self.assertEqual(exit_code, 0)
        self.assertTrue((out_dir / "report.json").is_file())
        self.assertTrue((out_dir / "summary.md").is_file())
    finally:
      server.shutdown()
      server.server_close()

  def test_anthropic_backend_skips_workspace_discovery_and_validation(
      self,
  ) -> None:
    state = _RunnerMockState()
    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), _make_runner_handler(state)
    )
    port = server.server_address[1]
    base_origin = f"http://127.0.0.1:{port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
      with tempfile.TemporaryDirectory() as tmp_dir:
        root = pathlib.Path(tmp_dir) / "repo"
        _create_synthetic_repo(root)

        with self.assertRaises(ValueError):
          runner.run_eval_suite(
              repo_root=root,
              backend="bogus",
              dry_run=True,
          )

        with self.assertRaises(ValueError):
          runner.run_eval_suite(
              repo_root=root,
              backend="gcp",
              project_id="",
              dry_run=False,
          )

        with mock.patch.dict(
            os.environ, {"ANTHROPIC_API_KEY": "sk-ant-runner-test"}
        ):
          ant_report = runner.run_eval_suite(
              repo_root=root,
              harness_mode="single-agent",
              backend="anthropic",
              target_scenario="sample_pass_case",
              base_origin=base_origin,
          )

        self.assertEqual(ant_report.backend, "anthropic")
        self.assertEqual(ant_report.project_id, "")
        self.assertEqual(ant_report.workspace_id, "")
        self.assertEqual(len(ant_report.results), 1)
        self.assertTrue(ant_report.results[0].passed)
        self.assertFalse(
            any("/organizations/workspaces" in p for p in state.request_paths)
        )
        self.assertTrue(
            all(
                h.get("x-api-key") == "sk-ant-runner-test"
                and "authorization" not in h
                for h in state.request_headers
            )
        )
        ant_summary = runner.render_markdown_summary(ant_report)
        self.assertIn("- **Backend:** `anthropic`", ant_summary)
        self.assertNotIn("- **Project:**", ant_summary)
    finally:
      server.shutdown()
      server.server_close()

  def test_real_repo_dry_run_smoke(self) -> None:
    bundle_bytes, included = runner.build_clean_plugin_bundle(REPO_ROOT)
    with tarfile.open(fileobj=io.BytesIO(bundle_bytes), mode="r:gz") as tar:
      tar_names = set(tar.getnames())

    self.assertEqual(tar_names, set(included))
    self.assertFalse(
        any(name.endswith("test_scenarios.yaml") for name in tar_names)
    )
    self.assertFalse(any(name.endswith("EVAL.txtpb") for name in tar_names))

    report = runner.run_eval_suite(
        repo_root=REPO_ROOT,
        harness_mode="both",
        dry_run=True,
    )
    skills = {r.skill for r in report.results}
    self.assertEqual(len(skills), 8)
    # 71 scenarios x 2 harness modes = 142 dry-run results.
    self.assertEqual(len(report.results), 142)
    self.assertTrue(all(r.passed for r in report.results))

  def test_multiturn_empty_fail_unmatched_scenario_and_sanitization(
      self,
  ) -> None:
    assertions = [
        runner.Assertion(type="required_pattern", pattern="MUST_EXIST"),
        runner.Assertion(type="contains", pattern="SUBSTR"),
        runner.Assertion(type="not_contains", pattern="BAD_TOKEN"),
        runner.Assertion(type="invalid_kind", pattern="x"),
    ]
    passed, errors = runner.evaluate_assertions(
        "Has BAD_TOKEN only", assertions
    )
    self.assertFalse(passed)
    self.assertEqual(len(errors), 4)

    ok, ok_errors = runner.evaluate_assertions(
        "MUST_EXIST SUBSTR", assertions[:3]
    )
    self.assertTrue(ok)
    self.assertEqual(ok_errors, [])

    fallback_desc, fallback_rubric = runner.build_outcome_rubric(
        {"scenario_id": "no_desc_case", "description": "", "turns": []}
    )
    self.assertEqual(fallback_desc, "Complete scenario no_desc_case cleanly.")
    self.assertIn(
        "Goal: Complete scenario no_desc_case cleanly.", fallback_rubric
    )

    explicit_desc, indexed_rubric = runner.build_outcome_rubric({
        "scenario_id": "rubric_idx",
        "description": "Check turns.",
        "turns": [{
            "rubric": {"prompt": "P1", "passing_criteria": "C1"},
            "assertions": [{"type": "contains", "pattern": "OK"}],
        }],
    })
    self.assertEqual(explicit_desc, "Check turns.")
    self.assertIn("Turn 1 evaluation focus:\nP1", indexed_rubric)
    self.assertIn("Turn 1 passing criteria: C1", indexed_rubric)
    self.assertIn("Turn 1 deterministic requirements:", indexed_rubric)

    state = _RunnerMockState()
    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), _make_runner_handler(state)
    )
    port = server.server_address[1]
    base_origin = f"http://127.0.0.1:{port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
      with tempfile.TemporaryDirectory() as tmp_dir:
        root = pathlib.Path(tmp_dir) / "repo"
        _create_synthetic_repo(root)
        (root / "plugin.json").write_text("{bad json", encoding="utf-8")
        (root / ".claude-plugin" / "plugin.json").write_text(
            "{bad json", encoding="utf-8"
        )
        self.assertEqual(runner.detect_egm_version(root), "0.0.0-dev")

        _, included = runner.build_clean_plugin_bundle(root)
        self.assertIn("plugin.json", included)

        prompt_text = runner.assemble_system_prompt(
            root,
            {"skill_file": "plugins/egm/skills/egm_sample/SKILL.md"},
        )
        self.assertIn("# Sample Skill", prompt_text)
        with self.assertRaises(FileNotFoundError):
          runner.assemble_system_prompt(root, {"skill_file": "missing.md"})

        # Add multi-turn and empty-terminated deterministic scenarios.
        (root / "skills" / "egm_sample" / "test_scenarios.yaml").write_text(
            """skill: "egm_sample"
scenarios:
  - scenario_id: "sample_multiturn_case"
    description: "Executes turns sequentially and checks turn-scoped assertions."
    eval_type: "deterministic"
    system_prompt:
      skill_file: "skills/egm_sample/SKILL.md"
    turns:
      - user_input: "Turn 1"
        assertions:
          - type: "contains"
            pattern: "HALT_TURN_1"
          - type: "not_contains"
            pattern: "EXEC_TURN_2"
      - user_input: "Turn 2"
        assertions:
          - type: "contains"
            pattern: "EXEC_TURN_2"
  - scenario_id: "sample_empty_deterministic"
    description: "Terminated deterministic session must fail even with forbidden_pattern."
    eval_type: "deterministic"
    system_prompt:
      skill_file: "skills/egm_sample/SKILL.md"
    turns:
      - user_input: "Fail early"
        assertions:
          - type: "forbidden_pattern"
            pattern: "BAD"
  - scenario_id: "sample_needs_revision_case"
    description: "Outcome verdict is needs_revision and must fail."
    eval_type: "llm_judge"
    system_prompt:
      skill_file: "skills/egm_sample/SKILL.md"
    turns:
      - user_input: "Evaluate needs revision case."
        rubric:
          prompt: "Check completeness."
          passing_criteria: "No missing sections."
""",
            encoding="utf-8",
        )

        self.assertEqual(
            runner.load_scenarios(pathlib.Path(tmp_dir) / "none"), []
        )
        with self.assertRaises(FileNotFoundError):
          runner.run_eval_suite(repo_root=root, target_skill="missing_skill")

        with mock.patch.dict(
            os.environ, {"GOOGLE_OAUTH_ACCESS_TOKEN": "tok_test_jdoe"}
        ):
          with self.assertRaises(ValueError):
            runner.run_eval_suite(
                repo_root=root,
                target_scenario="nonexistent_scenario",
                project_id="test-project-123",
                workspace_id="wrkspc_test01",
                base_origin=base_origin,
            )
          self.assertEqual(state.env_payloads, [])

          mt_report = runner.run_eval_suite(
              repo_root=root,
              harness_mode="multiagent",
              target_scenario="sample_multiturn_case",
              project_id="test-project-123",
              workspace_id="wrkspc_test01",
              base_origin=base_origin,
          )
          self.assertTrue(mt_report.results[0].passed)
          self.assertTrue(mt_report.results[0].assertion_passed)

          empty_report = runner.run_eval_suite(
              repo_root=root,
              harness_mode="multiagent",
              target_scenario="sample_empty_deterministic",
              project_id="test-project-123",
              workspace_id="wrkspc_test01",
              base_origin=base_origin,
          )
          self.assertFalse(empty_report.results[0].passed)

          custom_md = pathlib.Path(tmp_dir) / "custom" / "summary.md"
          exit_code = runner.main([
              "--repo-root",
              str(root),
              "--harness-mode",
              "multiagent",
              "--project-id",
              "test-project-123",
              "--workspace-id",
              "wrkspc_test01",
              "--base-origin",
              base_origin,
              "--skill",
              "egm_sample",
              "--scenario",
              "sample_needs_revision_case",
              "--upload-skill",
              "--output-dir",
              str(pathlib.Path(tmp_dir) / "out_live"),
              "--markdown-summary",
              str(custom_md),
          ])
        self.assertEqual(exit_code, 1)
        self.assertTrue(custom_md.is_file())
        self.assertTrue(any("skills" in p for p in state.agent_payloads))

        unsafe_explanation = (
            "<script>alert(1)</script>See ![img](https://evil.example/a.png) "
            "and [click](https://evil.example/b) | pipe "
            + ("A" * 150)
        )
        long_report = runner.EvalRunReport(
            egm_version="1.0.0",
            backend="gcp",
            model="claude-sonnet-4-6",
            effort="high",
            project_id="test-project-123",
            workspace_id="wrkspc_test01",
            max_iterations=1,
            dry_run=False,
            timestamp_utc="2026-11-24T00:00:00Z",
            bundle_bytes=10,
            bundle_file_count=1,
            results=[
                runner.ScenarioEvalResult(
                    scenario_id="long_exp",
                    skill="egm_sample",
                    description="desc",
                    harness_mode="multiagent",
                    eval_type="llm_judge",
                    passed=True,
                    outcome_verdict="satisfied",
                    judge_explanation=unsafe_explanation,
                    assertion_passed=True,
                )
            ],
        )
        rendered = runner.render_markdown_summary(long_report)
        self.assertNotIn("<script>", rendered)
        self.assertNotIn("https://evil.example", rendered)
        self.assertIn("...", rendered)
    finally:
      server.shutdown()
      server.server_close()


if __name__ == "__main__":
  unittest.main()
