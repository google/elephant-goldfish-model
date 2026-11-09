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

"""Unit tests for .github/scripts/review_pr.py, workflow hardening, and CODEOWNERS."""

from __future__ import annotations

import importlib.util
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / ".github" / "scripts" / "review_pr.py"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "pr-triage-review.yml"
CODEOWNERS_PATH = ROOT / ".github" / "CODEOWNERS"
CONFIG_PATH = ROOT / ".gemini" / "config.yaml"

_SPEC = importlib.util.spec_from_file_location("egm_review_pr", SCRIPT_PATH)
assert _SPEC and _SPEC.loader
review_pr = importlib.util.module_from_spec(_SPEC)
sys.modules["egm_review_pr"] = review_pr
_SPEC.loader.exec_module(review_pr)


def test_workflow_enforces_zizmor_default_model_and_two_job_boundary() -> None:
  raw = WORKFLOW_PATH.read_text(encoding="utf-8")
  data = yaml.safe_load(raw)

  assert data["permissions"] == {}
  assert "zizmor: ignore[dangerous-triggers]" in raw
  assert "gemini-3.8-flash" in raw
  assert review_pr.DEFAULT_MODEL == "gemini-3.8-flash"

  review_job = data["jobs"]["review"]
  assert review_job["permissions"] == {
      "contents": "read",
      "pull-requests": "read",
  }
  post_job = data["jobs"]["post"]
  assert post_job["permissions"] == {
      "pull-requests": "write",
      "issues": "write",
  }
  assert post_job["needs"] == "review"

  for step in post_job["steps"]:
    uses = step.get("uses", "")
    assert not uses.startswith("actions/checkout@")
    env = step.get("env") or {}
    assert "GEMINI_API_KEY" not in str(env)

  for job in data["jobs"].values():
    for step in job["steps"]:
      if "uses" in step:
        assert re.match(r"^[^@]+@[0-9a-f]{40}$", step["uses"]), step["uses"]
      if "run" in step:
        assert "${{" not in step["run"], "Untrusted expressions must use env:"


def test_codeowners_scopes_auto_review_to_workflow_paths_only() -> None:
  lines = [
      line.strip()
      for line in CODEOWNERS_PATH.read_text(encoding="utf-8").splitlines()
      if line.strip() and not line.strip().startswith("#")
  ]
  assert "* @google/egm-maintainers" not in lines
  assert ".github/** @google/egm-maintainers" in lines


def test_config_loader_matches_stdlib_fallback() -> None:
  repo_cfg = review_pr.load_repo_config(CONFIG_PATH)
  stdlib_cfg = review_pr._parse_config_stdlib(CONFIG_PATH.read_text(encoding="utf-8"))
  assert repo_cfg == stdlib_cfg
  assert repo_cfg.max_review_comments == 5
  assert review_pr.is_ignored_path("site/package-lock.json", repo_cfg.ignore_patterns)
  assert review_pr.is_ignored_path("site/public/og.png", repo_cfg.ignore_patterns)
  assert not review_pr.is_ignored_path(".github/scripts/review_pr.py", repo_cfg.ignore_patterns)


def test_evaluate_sweep_gate_uses_author_association_dynamically() -> None:
  draft = review_pr.evaluate_sweep_gate(
      {"state": "open", "draft": True, "user": {"login": "alice"}},
      reviews=[],
      issue_comments=[],
      files=[],
  )
  assert not draft.should_review
  assert draft.reason == "SKIP_DRAFT"

  bot = review_pr.evaluate_sweep_gate(
      {"state": "open", "draft": False, "user": {"login": "custom-ci", "type": "Bot"}},
      reviews=[],
      issue_comments=[],
      files=[],
  )
  assert not bot.should_review
  assert bot.reason == "SKIP_BOT_AUTHOR:custom-ci"

  human_member = review_pr.evaluate_sweep_gate(
      {
          "state": "open",
          "draft": False,
          "user": {"login": "alice"},
          "head": {"sha": "1111111"},
      },
      reviews=[{
          "user": {"login": "any-maintainer", "type": "User"},
          "author_association": "MEMBER",
          "body": "Looking now",
      }],
      issue_comments=[],
      files=[{"filename": "README.md", "changes": 4}],
  )
  assert not human_member.should_review
  assert human_member.reason == "SKIP_ALREADY_REVIEWED_BY_HUMAN:any-maintainer"

  # Non-trusted contributor reviews and bot reviews do not block Stage-1 triage.
  external_commenter = review_pr.evaluate_sweep_gate(
      {
          "state": "open",
          "draft": False,
          "user": {"login": "alice"},
          "head": {"sha": "2222222"},
      },
      reviews=[
          {
              "user": {"login": "external-fan", "type": "User"},
              "author_association": "CONTRIBUTOR",
              "body": "Nice!",
          },
          {
              "user": {"login": "github-actions[bot]", "type": "Bot"},
              "author_association": "NONE",
              "body": "<!-- egm-triage-review:sha=1111111 -->\nOld SHA",
          },
      ],
      issue_comments=[],
      files=[{"filename": "README.md", "changes": 4}],
  )
  assert external_commenter.should_review

  same_sha = review_pr.evaluate_sweep_gate(
      {
          "state": "open",
          "draft": False,
          "user": {"login": "alice"},
          "head": {"sha": "deadbeef"},
      },
      reviews=[{
          "user": {"login": "github-actions[bot]", "type": "Bot"},
          "author_association": "NONE",
          "body": "<!-- egm-triage-review:sha=deadbeef -->\nClean pass.",
      }],
      issue_comments=[],
      files=[{"filename": "README.md", "changes": 4}],
  )
  assert not same_sha.should_review
  assert same_sha.reason == "SKIP_SHA_ALREADY_REVIEWED:deadbeef"


def test_parse_valid_right_lines_and_anchor_filtering() -> None:
  files = [{
      "filename": "scripts/example.py",
      "patch": (
          "@@ -10,4 +10,5 @@ def run():\n"
          " unchanged()\n"
          "-old_call()\n"
          "+new_call()\n"
          "+added_check()\n"
          " trailing()\n"
      ),
  }]
  valid = review_pr.parse_valid_right_lines(files)
  assert valid == {"scripts/example.py": {10, 11, 12, 13}}

  payload = review_pr.build_review_payload(
      "abc1234",
      [
          {
              "severity": "Blocker",
              "path": "scripts/example.py",
              "line": 12,
              "summary": "BLUF: Missing guard on added_check",
              "fix": "Validate inputs first",
              "suggestion": "if value:\n  added_check()",
          },
          {
              "severity": "Major",
              "path": "scripts/example.py",
              "line": 999,
              "summary": "Summary: Out-of-hunk finding falls back cleanly",
              "fix": "Move validation above",
          },
          {
              "severity": "Major",
              "path": "untouched/other.py",
              "line": 5,
              "summary": "Should be dropped because file is not in PR",
              "fix": "Drop it",
          },
      ],
      valid_right_lines=valid,
      changed_paths={"scripts/example.py"},
  )
  assert len(payload["comments"]) == 1
  assert payload["comments"][0]["line"] == 12
  assert "BLUF" not in payload["comments"][0]["body"].upper()
  assert "Out-of-hunk finding falls back cleanly" in payload["body"]
  assert "untouched/other.py" not in payload["body"]


def test_plan_pr_review_runs_single_call_when_clean_and_two_calls_to_disprove(
    tmp_path: pathlib.Path, monkeypatch
) -> None:
  styleguide = tmp_path / "styleguide.md"
  styleguide.write_text("# Style\nKeep checks crisp.\n", encoding="utf-8")

  pr_payload = {
      "number": 501,
      "state": "open",
      "draft": False,
      "title": "Fix skill frontmatter check",
      "body": "## Summary\nSmall fix.",
      "user": {"login": "contributor"},
      "base": {"ref": "main"},
      "head": {"sha": "abc12345"},
      "requested_reviewers": [],
      "requested_teams": [],
      "labels": [{"name": "triage: passed"}],
  }
  files_payload = [{
      "filename": "scripts/check.py",
      "status": "modified",
      "additions": 2,
      "deletions": 0,
      "changes": 2,
      "patch": "@@ -1,2 +1,4 @@\n def ok():\n+  x = 1\n+  return x\n   pass\n",
  }]

  monkeypatch.setattr(
      review_pr,
      "_github_request_json",
      lambda url, token, **_kw: (
          (pr_payload, {}) if url.endswith("/pulls/501") else ({}, {})
      ),
  )
  monkeypatch.setattr(
      review_pr,
      "_github_paginate",
      lambda endpoint, token, **_kw: files_payload if endpoint.endswith("/files") else [],
  )

  # Clean Pass 1 short-circuits without paying for a Pass 2 disproof call.
  clean_calls: list[str] = []
  clean_plan = review_pr.plan_pr_review(
      repo="google/elephant-goldfish-model",
      pr_number=501,
      head_sha="abc12345",
      github_token="tok",
      gemini_api_key="key",
      styleguide_path=styleguide,
      config_path=CONFIG_PATH,
      llm_caller=lambda prompt: clean_calls.append(prompt) or {"findings": []},
  )
  assert len(clean_calls) == 1
  assert clean_plan["action"] == "clean_handoff"
  assert clean_plan["add_labels"] == ["triage: passed"]
  assert clean_plan["team_reviewers"] == ["egm-maintainers"]

  # Candidate findings trigger an independent stateless Pass 2 disproof call.
  disproved_calls = 0

  def disprove_all(_prompt: str):
    nonlocal disproved_calls
    disproved_calls += 1
    if disproved_calls == 1:
      return {
          "findings": [{
              "severity": "Major",
              "path": "scripts/check.py",
              "line": 2,
              "summary": "False positive nit",
              "fix": "Ignore",
          }]
      }
    return {"findings": [], "dropped_reasons": ["False positive in Pass 2"]}

  disproved_plan = review_pr.plan_pr_review(
      repo="google/elephant-goldfish-model",
      pr_number=501,
      head_sha="abc12345",
      github_token="tok",
      gemini_api_key="key",
      styleguide_path=styleguide,
      config_path=CONFIG_PATH,
      llm_caller=disprove_all,
  )
  assert disproved_calls == 2
  assert disproved_plan["action"] == "clean_handoff"

  # Verified surviving finding transitions to post_findings and strips stale label.
  surviving_calls = 0

  def keep_one(_prompt: str):
    nonlocal surviving_calls
    surviving_calls += 1
    return {
        "findings": [{
            "severity": "Blocker",
            "path": "scripts/check.py",
            "line": 2,
            "summary": "Unused assignment returns wrong constant",
            "fix": "Validate value before returning",
            "suggestion": "",
        }]
    }

  findings_plan = review_pr.plan_pr_review(
      repo="google/elephant-goldfish-model",
      pr_number=501,
      head_sha="abc12345",
      github_token="tok",
      gemini_api_key="key",
      styleguide_path=styleguide,
      config_path=CONFIG_PATH,
      llm_caller=keep_one,
  )
  assert surviving_calls == 2
  assert findings_plan["action"] == "post_findings"
  assert findings_plan["remove_labels"] == ["triage: passed"]
  assert findings_plan["team_reviewers"] == []
  assert len(findings_plan["review_payload"]["comments"]) == 1
