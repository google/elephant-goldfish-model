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

"""Managed Agents evaluation runner for EGM behavioral scenario suites.

Packages an EGM plugin repository into a rubric-free tarball, runs
`test_scenarios.yaml` suites against `gcp` or `anthropic` Managed Agents
backends in `multiagent` and/or `single-agent` harness modes, grades outcomes
plus deterministic regex assertions, and writes JSON + Markdown summaries.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import gzip
import importlib
import io
import json
import os
import pathlib
import re
import sys
import tarfile
from typing import Any

import yaml

try:
  from tools.managed_agents_eval import client as ma_client
except ImportError:
  ma_client = importlib.import_module(
      f"{__package__}.client" if __package__ else "client"
  )


# Single-shot outcome grading without retry coaching ensures regressions surface
# on the first agent attempt instead of being masked by multi-turn grader hints.
DEFAULT_MAX_ITERATIONS = 1

# Default Claude model ID supported by both Managed Agents backends.
DEFAULT_MODEL = "claude-sonnet-4-6"

# Default thinking effort level matching standard interactive EGM usage.
DEFAULT_EFFORT = "high"

# Top-level plugin entries included in clean sandbox bundles.
BUNDLE_ROOT_ENTRIES = (
    "skills",
    "agents",
    "rules",
    "resources",
    ".claude-plugin",
    ".plugin",
    "plugin.json",
)

# Directories excluded from plugin bundles to prevent leakage or bloat.
EXCLUDED_DIR_NAMES = frozenset({
    ".git",
    "__pycache__",
    "eval_results",
    ".pytest_cache",
})

# Evaluation rubric and test files strictly excluded so the sandboxed agent
# cannot read grading criteria or regex patterns at runtime.
EXCLUDED_FILE_NAMES = frozenset({
    "test_scenarios.yaml",
    "EVAL.txtpb",
    "EVAL.textproto",
})

_BUNDLE_MOUNT_PATH = "/mnt/session/uploads/egm_plugin.tar.gz"
_MD_LINK_OR_IMAGE_RE = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
_HTML_TAG_RE = re.compile(r"<[^>]+>")


@dataclasses.dataclass
class Assertion:
  """Deterministic assertion matching test_scenarios.yaml schema."""

  type: str
  pattern: str
  message: str = ""


@dataclasses.dataclass
class ScenarioEvalResult:
  """Evaluation outcome for a single scenario and harness mode."""

  scenario_id: str
  skill: str
  description: str
  harness_mode: str
  eval_type: str
  passed: bool
  outcome_verdict: str
  judge_explanation: str
  assertion_passed: bool
  assertion_errors: list[str] = dataclasses.field(default_factory=list)
  input_tokens: int = 0
  output_tokens: int = 0
  cache_read_input_tokens: int = 0
  cache_creation_input_tokens: int = 0
  total_tokens: int = 0
  duration_ms: int = 0
  tool_use_count: int = 0
  tool_error_count: int = 0
  session_id: str = ""
  agent_id: str = ""
  final_response: str = ""


@dataclasses.dataclass
class EvalRunReport:
  """Full evaluation report across scenarios and harness modes."""

  egm_version: str
  backend: str
  model: str
  effort: str
  project_id: str
  workspace_id: str
  max_iterations: int
  dry_run: bool
  timestamp_utc: str
  bundle_bytes: int
  bundle_file_count: int
  results: list[ScenarioEvalResult] = dataclasses.field(default_factory=list)


def detect_egm_version(repo_root: pathlib.Path) -> str:
  """Reads plugin version from standard manifest paths, defaulting to 0.0.0-dev."""
  candidates = (
      repo_root / ".claude-plugin" / "plugin.json",
      repo_root / ".plugin" / "plugin.json",
      repo_root / "plugin.json",
  )
  for manifest in candidates:
    if not manifest.is_file():
      continue
    try:
      data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
      continue
    if isinstance(data, dict):
      version = str(data.get("version", "")).strip()
      if version:
        return version
  return "0.0.0-dev"


def _is_excluded_rel_path(rel_path: pathlib.PurePosixPath) -> bool:
  """Returns True when a bundle candidate path must be excluded."""
  if any(part in EXCLUDED_DIR_NAMES for part in rel_path.parts):
    return True
  if rel_path.name in EXCLUDED_FILE_NAMES:
    return True
  if rel_path.name.endswith(".pyc"):
    return True
  return False


def build_clean_plugin_bundle(
    repo_root: pathlib.Path,
) -> tuple[bytes, list[str]]:
  """Packs plugin assets into deterministic gzipped tar bytes without rubrics.

  Args:
    repo_root: Root directory of the EGM plugin repository.

  Returns:
    Tuple of (gzip_tar_bytes, sorted_included_relative_paths).
  """
  resolved_root = repo_root.resolve()
  candidates: list[tuple[str, pathlib.Path]] = []

  for entry_name in BUNDLE_ROOT_ENTRIES:
    entry_path = resolved_root / entry_name
    if entry_path.is_symlink() or not entry_path.exists():
      continue
    if entry_path.is_file():
      resolved_entry = entry_path.resolve()
      if not resolved_entry.is_relative_to(resolved_root):
        continue
      rel = pathlib.PurePosixPath(entry_name)
      if not _is_excluded_rel_path(rel):
        candidates.append((rel.as_posix(), resolved_entry))
    elif entry_path.is_dir():
      for child in entry_path.rglob("*"):
        if child.is_symlink() or not child.is_file():
          continue
        resolved_child = child.resolve()
        if not resolved_child.is_relative_to(resolved_root):
          continue
        rel = pathlib.PurePosixPath(child.relative_to(resolved_root).as_posix())
        if not _is_excluded_rel_path(rel):
          candidates.append((rel.as_posix(), resolved_child))

  candidates.sort(key=lambda item: item[0])
  included_paths = [rel for rel, _ in candidates]

  buf = io.BytesIO()
  with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as gz:
    with tarfile.open(fileobj=gz, mode="w") as tar:
      for rel_str, abs_path in candidates:
        data = abs_path.read_bytes()
        info = tarfile.TarInfo(name=rel_str)
        info.size = len(data)
        info.mtime = 0
        info.mode = 0o644
        info.uid = 0
        info.gid = 0
        info.uname = ""
        info.gname = ""
        tar.addfile(info, io.BytesIO(data))

  return buf.getvalue(), included_paths


def evaluate_assertions(
    response: str, assertions: list[Assertion]
) -> tuple[bool, list[str]]:
  """Evaluates deterministic assertions against a model response."""
  errors: list[str] = []
  for assertion in assertions:
    if assertion.type == "required_pattern":
      if not re.search(assertion.pattern, response):
        errors.append(
            assertion.message
            or f"Required pattern '{assertion.pattern}' did not match."
        )
    elif assertion.type == "forbidden_pattern":
      if re.search(assertion.pattern, response):
        errors.append(
            assertion.message
            or f"Forbidden pattern '{assertion.pattern}' matched."
        )
    elif assertion.type == "contains":
      if assertion.pattern not in response:
        errors.append(
            assertion.message
            or f"Required substring '{assertion.pattern}' not found."
        )
    elif assertion.type == "not_contains":
      if assertion.pattern in response:
        errors.append(
            assertion.message
            or f"Forbidden substring '{assertion.pattern}' found."
        )
    else:
      errors.append(f"Unknown assertion type: {assertion.type}")
  return len(errors) == 0, errors


def _resolve_repo_relative_file(
    repo_root: pathlib.Path, rel_path: str
) -> pathlib.Path:
  """Resolves skill/rule paths safely inside repo_root without traversal."""
  resolved_root = repo_root.resolve()
  posix_rel = pathlib.PurePosixPath(rel_path)
  if posix_rel.is_absolute() or pathlib.Path(rel_path).is_absolute():
    raise ValueError(f"Configured prompt path must be relative: {rel_path}")

  candidates: list[pathlib.Path] = [resolved_root / rel_path]
  prefix = "plugins/egm/"
  if rel_path.startswith(prefix):
    candidates.append(resolved_root / rel_path[len(prefix) :])

  for candidate in candidates:
    if candidate.is_symlink():
      raise ValueError(
          f"Configured prompt path cannot be a symlink: {rel_path}"
      )
    resolved_candidate = candidate.resolve()
    if not resolved_candidate.is_relative_to(resolved_root):
      raise ValueError(f"Prompt path escapes repo_root: {rel_path}")
    if resolved_candidate.is_file():
      return resolved_candidate

  raise FileNotFoundError(
      f"Configured prompt file not found: {resolved_root / rel_path}"
  )


def assemble_system_prompt(
    repo_root: pathlib.Path, prompt_config: dict[str, Any]
) -> str:
  """Assembles system prompt from relative skill_file and rules entries."""
  parts: list[str] = []
  skill_file = prompt_config.get("skill_file")
  if skill_file:
    parts.append(
        _resolve_repo_relative_file(repo_root, str(skill_file)).read_text(
            encoding="utf-8"
        )
    )
  for rule_file in prompt_config.get("rules", []) or []:
    parts.append(
        _resolve_repo_relative_file(repo_root, str(rule_file)).read_text(
            encoding="utf-8"
        )
    )
  return "\n\n".join(parts)


def load_scenarios(
    repo_root: pathlib.Path, target_skill: str | None = None
) -> list[tuple[pathlib.Path, dict[str, Any]]]:
  """Loads all test_scenarios.yaml suites under repo_root/skills."""
  skills_dir = repo_root / "skills"
  results: list[tuple[pathlib.Path, dict[str, Any]]] = []
  if not skills_dir.is_dir():
    return results

  for skill_dir in sorted(skills_dir.iterdir()):
    if not skill_dir.is_dir():
      continue
    if target_skill and skill_dir.name != target_skill:
      continue
    scenario_file = skill_dir / "test_scenarios.yaml"
    if scenario_file.is_file():
      data = yaml.safe_load(scenario_file.read_text(encoding="utf-8"))
      if isinstance(data, dict):
        results.append((scenario_file, data))
  return results


def _turn_assertions(turn: dict[str, Any]) -> list[Assertion]:
  """Parses deterministic Assertion objects for a single turn."""
  return [
      Assertion(
          type=str(raw.get("type", "")),
          pattern=str(raw.get("pattern", "")),
          message=str(raw.get("message", "")),
      )
      for raw in turn.get("assertions", []) or []
  ]


def _evaluate_turn_assertions(
    turns: list[dict[str, Any]],
    turn_responses: list[str],
) -> tuple[bool, list[str]]:
  """Evaluates each turn's deterministic assertions against its own response."""
  errors: list[str] = []
  for idx, turn in enumerate(turns):
    assertions = _turn_assertions(turn)
    if not assertions:
      continue
    if idx >= len(turn_responses):
      errors.append(
          f"Turn {idx + 1}: no response received for turn assertions."
      )
      continue
    passed, turn_errors = evaluate_assertions(turn_responses[idx], assertions)
    if not passed:
      if len(turns) > 1:
        errors.extend(f"Turn {idx + 1}: {err}" for err in turn_errors)
      else:
        errors.extend(turn_errors)
  return len(errors) == 0, errors


def build_outcome_rubric(scenario_data: dict[str, Any]) -> tuple[str, str]:
  """Synthesizes Managed Agents outcome description and rubric text."""
  scenario_id = str(scenario_data.get("scenario_id", "unnamed_scenario"))
  description = str(
      scenario_data.get("description", "")
      or f"Complete scenario {scenario_id} cleanly."
  )
  rubric_lines: list[str] = [f"Scenario: {scenario_id}", f"Goal: {description}"]

  for idx, turn in enumerate(scenario_data.get("turns", []) or [], start=1):
    rubric = turn.get("rubric")
    if isinstance(rubric, dict):
      prompt_text = str(rubric.get("prompt", "")).strip()
      criteria_text = str(rubric.get("passing_criteria", "")).strip()
      if prompt_text:
        rubric_lines.append(f"Turn {idx} evaluation focus:\n{prompt_text}")
      if criteria_text:
        rubric_lines.append(f"Turn {idx} passing criteria: {criteria_text}")

    assertions = turn.get("assertions", []) or []
    if assertions:
      rubric_lines.append(f"Turn {idx} deterministic requirements:")
      for raw in assertions:
        a_type = str(raw.get("type", ""))
        pattern = str(raw.get("pattern", ""))
        msg = str(raw.get("message", "")).strip()
        detail = f" ({msg})" if msg else ""
        rubric_lines.append(f"- {a_type}: `{pattern}`{detail}")

  return description, "\n\n".join(rubric_lines)


def _extract_turn_prompts(scenario_data: dict[str, Any]) -> list[str]:
  """Extracts ordered user prompts for sequential turn execution."""
  turns = scenario_data.get("turns", []) or []
  return [str(t.get("user_input", "")).strip() for t in turns]


def _build_agent_system_prompt(
    base_system_prompt: str, harness_mode: str, has_bundle: bool
) -> str:
  """Formats runtime instructions around the assembled skill/rule prompt."""
  sections: list[str] = []
  if base_system_prompt:
    sections.append(base_system_prompt)
  runtime_notes = [
      f"Harness mode: {harness_mode}.",
  ]
  if has_bundle:
    runtime_notes.append(
        "The clean EGM plugin repository bundle is mounted at "
        f"`{_BUNDLE_MOUNT_PATH}` if you need to inspect reference files."
    )
  sections.append("\n".join(runtime_notes))
  return "\n\n".join(sections)


def _expand_harness_modes(harness_mode: str) -> list[str]:
  """Expands CLI harness mode selector into ordered execution modes."""
  if harness_mode == "both":
    return ["multiagent", "single-agent"]
  return [harness_mode]


def _sanitize_markdown_cell(text: str) -> str:
  """Sanitizes untrusted LLM output before embedding inside Markdown tables."""
  cleaned = _MD_LINK_OR_IMAGE_RE.sub(r"\1", text)
  cleaned = _HTML_TAG_RE.sub("", cleaned)
  cleaned = cleaned.replace("\r", " ").replace("\n", " ").replace("|", "\\|")
  cleaned = re.sub(r"\s+", " ", cleaned).strip()
  if len(cleaned) > 120:
    return cleaned[:117] + "..."
  return cleaned


def render_markdown_summary(report: EvalRunReport) -> str:
  """Renders a regression summary grouped by egm_version and harness_mode."""
  lines: list[str] = [
      "# Managed Agents Evaluation Summary",
      "",
      f"- **EGM Version:** `{report.egm_version}`",
      f"- **Backend:** `{report.backend}`",
      f"- **Model:** `{report.model}` (effort: `{report.effort}`)",
  ]
  if report.project_id:
    lines.append(f"- **Project:** `{report.project_id}`")
  lines.extend([
      f"- **Max Iterations:** `{report.max_iterations}`",
      f"- **Mode:** `{'dry-run' if report.dry_run else 'live'}`",
      (
          f"- **Bundle:** `{report.bundle_file_count}` files "
          f"(`{report.bundle_bytes}` bytes)"
      ),
      "",
  ])

  modes_seen: list[str] = []
  for res in report.results:
    if res.harness_mode not in modes_seen:
      modes_seen.append(res.harness_mode)

  lines.append(f"## Version {report.egm_version}")
  lines.append("")
  for mode in modes_seen:
    mode_results = [r for r in report.results if r.harness_mode == mode]
    total = len(mode_results)
    passed_count = sum(1 for r in mode_results if r.passed)
    pass_rate = (passed_count / total * 100.0) if total else 0.0
    total_tokens = sum(r.total_tokens for r in mode_results)
    mean_duration_s = (
        sum(r.duration_ms for r in mode_results) / total / 1000.0
        if total
        else 0.0
    )
    lines.append(f"### Harness Mode: {mode}")
    lines.append("")
    lines.append(
        f"Pass rate is {passed_count}/{total} ({pass_rate:.1f}%), "
        f"total tokens is {total_tokens}, and "
        f"mean round duration is {mean_duration_s:.2f}s."
    )
    lines.append("")
    lines.append(
        "| Scenario | Mode | Outcome Verdict | Assertions | Tokens | "
        "Duration | Judge Explanation |"
    )
    lines.append("| :--- | :--- | :--- | :--- | ---: | ---: | :--- |")
    for r in mode_results:
      assertion_cell = "PASS" if r.assertion_passed else "FAIL"
      duration_cell = f"{r.duration_ms / 1000.0:.2f}s"
      explanation = _sanitize_markdown_cell(r.judge_explanation or "")
      lines.append(
          f"| `{r.scenario_id}` | `{r.harness_mode}` | "
          f"`{r.outcome_verdict}` | {assertion_cell} | {r.total_tokens} | "
          f"{duration_cell} | {explanation} |"
      )
    lines.append("")

  return "\n".join(lines).rstrip() + "\n"


def _filter_suites(
    scenario_suites: list[tuple[pathlib.Path, dict[str, Any]]],
    target_scenario: str | None,
) -> list[tuple[pathlib.Path, str, list[dict[str, Any]]]]:
  """Filters discovered suites before creating any cloud resources."""
  filtered: list[tuple[pathlib.Path, str, list[dict[str, Any]]]] = []
  for scenario_file, suite in scenario_suites:
    skill_name = str(suite.get("skill", scenario_file.parent.name))
    scenarios = list(suite.get("scenarios", []) or [])
    if target_scenario:
      scenarios = [
          s for s in scenarios if s.get("scenario_id") == target_scenario
      ]
    if scenarios:
      filtered.append((scenario_file, skill_name, scenarios))

  if not filtered:
    if target_scenario:
      raise ValueError(f"No scenario matched --scenario={target_scenario!r}.")
    raise ValueError(
        "No scenarios found in matching test_scenarios.yaml files."
    )
  return filtered


def run_eval_suite(
    *,
    repo_root: pathlib.Path,
    harness_mode: str = "both",
    backend: str = ma_client.DEFAULT_BACKEND,
    project_id: str = ma_client.DEFAULT_PROJECT_ID,
    workspace_id: str | None = None,
    location: str = ma_client.DEFAULT_LOCATION,
    base_origin: str | None = None,
    model: str = DEFAULT_MODEL,
    effort: str = DEFAULT_EFFORT,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    target_skill: str | None = None,
    target_scenario: str | None = None,
    egm_version: str | None = None,
    dry_run: bool = False,
    enable_web: bool = False,
    allowed_hosts: list[str] | None = None,
    upload_skill: bool = False,
    client_instance: ma_client.ClaudeManagedAgentsClient | None = None,
) -> EvalRunReport:
  """Executes matching scenario suites and returns an EvalRunReport."""
  if backend not in ma_client.SUPPORTED_BACKENDS:
    supported = ", ".join(sorted(ma_client.SUPPORTED_BACKENDS))
    raise ValueError(
        f"Unsupported backend {backend!r}; expected one of: {supported}."
    )

  resolved_root = repo_root.resolve()
  resolved_version = egm_version or detect_egm_version(resolved_root)
  bundle_bytes, included_paths = build_clean_plugin_bundle(resolved_root)
  if len(bundle_bytes) > ma_client.MAX_BUNDLE_BYTES:
    raise ValueError(
        f"Clean plugin bundle exceeds {ma_client.MAX_BUNDLE_BYTES} bytes."
    )

  scenario_suites = load_scenarios(resolved_root, target_skill=target_skill)
  if not scenario_suites:
    raise FileNotFoundError(
        "No matching test_scenarios.yaml suites under"
        f" {resolved_root / 'skills'}"
    )
  filtered_suites = _filter_suites(scenario_suites, target_scenario)

  modes = _expand_harness_modes(harness_mode)
  timestamp_utc = datetime.datetime.now(datetime.timezone.utc).strftime(
      "%Y-%m-%dT%H:%M:%SZ"
  )

  env_id = ""
  bundle_file_id: str | None = None
  uploaded_skill_ids: dict[str, str] = {}
  effective_backend = (
      client_instance.backend if client_instance is not None else backend
  )

  if not dry_run:
    if client_instance is None:
      if backend == "gcp" and not project_id.strip():
        raise ValueError(
            "project_id is required for live runs on backend='gcp'. "
            "Pass --project-id or set GCP_PROJECT_ID."
        )
      client_instance = ma_client.ClaudeManagedAgentsClient(
          project_id=project_id,
          workspace_id=workspace_id,
          location=location,
          base_origin=base_origin,
          backend=backend,
      )
    effective_backend = client_instance.backend
    if effective_backend == "gcp" and not client_instance.workspace_id:
      workspaces = client_instance.list_workspaces()
      if not workspaces:
        raise RuntimeError(
            "No Anthropic workspaces found for project. Pass --workspace-id."
        )
      first_ws = workspaces[0]
      discovered_id = str(
          first_ws.get("id") or first_ws.get("workspace_id") or ""
      )
      if not discovered_id:
        raise RuntimeError(
            "Workspace discovery response did not include an 'id' field."
        )
      client_instance.workspace_id = discovered_id
    workspace_id = client_instance.workspace_id or ""

    effective_allowed_hosts = (
        allowed_hosts
        if allowed_hosts is not None
        else (None if enable_web else [])
    )
    env_resp = client_instance.create_environment(
        name=f"egm-eval-{resolved_version}",
        pip_packages=["pyyaml"],
        allowed_hosts=effective_allowed_hosts,
        metadata={"egm_version": resolved_version},
    )
    env_id = str(env_resp["id"])

    bundle_resp = client_instance.upload_bundle(bundle_bytes)
    bundle_file_id = str(bundle_resp["id"])

  report = EvalRunReport(
      egm_version=resolved_version,
      backend=effective_backend,
      model=model,
      effort=effort,
      project_id=project_id,
      workspace_id=workspace_id or "",
      max_iterations=max_iterations,
      dry_run=dry_run,
      timestamp_utc=timestamp_utc,
      bundle_bytes=len(bundle_bytes),
      bundle_file_count=len(included_paths),
  )

  for scenario_file, skill_name, scenarios in filtered_suites:
    skill_ids: list[str] = []
    if not dry_run and upload_skill and client_instance is not None:
      if skill_name not in uploaded_skill_ids:
        skill_resp = client_instance.upload_skill_dir(
            scenario_file.parent, display_title=skill_name
        )
        uploaded_skill_ids[skill_name] = str(skill_resp["id"])
      skill_ids = [uploaded_skill_ids[skill_name]]

    for sc in scenarios:
      scenario_id = str(sc.get("scenario_id", "unnamed_scenario"))
      description = str(sc.get("description", ""))
      eval_type = str(sc.get("eval_type", "deterministic"))
      base_system = assemble_system_prompt(
          resolved_root, sc.get("system_prompt", {}) or {}
      )
      turns_list = list(sc.get("turns", []) or [])
      turn_prompts = _extract_turn_prompts(sc)
      outcome_desc, rubric_text = build_outcome_rubric(sc)

      for mode in modes:
        if dry_run:
          report.results.append(
              ScenarioEvalResult(
                  scenario_id=scenario_id,
                  skill=skill_name,
                  description=description,
                  harness_mode=mode,
                  eval_type=eval_type,
                  passed=True,
                  outcome_verdict="dry_run",
                  judge_explanation=(
                      "Dry run: validated bundle, prompt, and rubric."
                  ),
                  assertion_passed=True,
              )
          )
          continue

        assert client_instance is not None
        system_prompt = _build_agent_system_prompt(
            base_system, mode, has_bundle=bundle_file_id is not None
        )
        agent_resp = client_instance.create_agent(
            name=f"egm-{skill_name}-{mode}",
            model=model,
            system=system_prompt,
            enable_multiagent=(mode == "multiagent"),
            skill_ids=skill_ids or None,
            effort=effort,
            enable_web=enable_web,
            metadata={"egm_version": resolved_version, "harness_mode": mode},
        )
        agent_id = str(agent_resp["id"])

        session_outcome = client_instance.run_eval_session(
            agent_id=agent_id,
            environment_id=env_id,
            outcome_description=outcome_desc,
            rubric_text=rubric_text,
            bundle_file_id=bundle_file_id,
            bundle_mount_path=_BUNDLE_MOUNT_PATH,
            max_iterations=max_iterations,
            title=f"{skill_name}:{scenario_id}:{mode}",
            metadata={"scenario_id": scenario_id, "harness_mode": mode},
            turns=turn_prompts,
        )

        assertion_passed, assertion_errors = _evaluate_turn_assertions(
            turns_list, session_outcome.turn_responses
        )

        outcome_eval = session_outcome.outcome_evaluation
        if session_outcome.error_message:
          verdict = outcome_eval.result if outcome_eval else "error"
          explanation = session_outcome.error_message
          outcome_passed = False
        elif outcome_eval is not None:
          verdict = outcome_eval.result
          explanation = outcome_eval.explanation
          outcome_passed = verdict == "satisfied"
        else:
          verdict = "missing"
          explanation = "No span.outcome_evaluation_end event received."
          if eval_type == "deterministic":
            outcome_passed = session_outcome.stop_reason == "end_turn" and bool(
                session_outcome.final_response.strip()
            )
          else:
            outcome_passed = False

        if not assertion_passed and explanation:
          explanation = f"{explanation} | Assertion errors: " + "; ".join(
              assertion_errors
          )
        elif not assertion_passed:
          explanation = "Assertion errors: " + "; ".join(assertion_errors)

        overall_passed = outcome_passed and assertion_passed

        report.results.append(
            ScenarioEvalResult(
                scenario_id=scenario_id,
                skill=skill_name,
                description=description,
                harness_mode=mode,
                eval_type=eval_type,
                passed=overall_passed,
                outcome_verdict=verdict,
                judge_explanation=explanation,
                assertion_passed=assertion_passed,
                assertion_errors=assertion_errors,
                input_tokens=session_outcome.usage.input_tokens,
                output_tokens=session_outcome.usage.output_tokens,
                cache_read_input_tokens=(
                    session_outcome.usage.cache_read_input_tokens
                ),
                cache_creation_input_tokens=(
                    session_outcome.usage.cache_creation_input_tokens
                ),
                total_tokens=session_outcome.usage.total_tokens,
                duration_ms=session_outcome.duration_ms,
                tool_use_count=session_outcome.tool_use_count,
                tool_error_count=session_outcome.tool_error_count,
                session_id=session_outcome.session_id,
                agent_id=agent_id,
                final_response=session_outcome.final_response,
            )
        )

  return report


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
  """Parses command-line flags for the Managed Agents evaluation runner."""
  parser = argparse.ArgumentParser(
      description="Run EGM Managed Agents behavioral evaluations."
  )
  parser.add_argument(
      "--repo-root",
      required=True,
      help="Path to EGM plugin repository root containing skills/ and rules/.",
  )
  parser.add_argument(
      "--harness-mode",
      choices=["multiagent", "single-agent", "both"],
      default="both",
      help="Agent orchestration mode to evaluate.",
  )
  parser.add_argument(
      "--backend",
      choices=sorted(ma_client.SUPPORTED_BACKENDS),
      default=ma_client.DEFAULT_BACKEND,
      help="Managed Agents API backend ('gcp' or 'anthropic').",
  )
  parser.add_argument(
      "--project-id",
      default=os.environ.get("GCP_PROJECT_ID", ma_client.DEFAULT_PROJECT_ID),
      help=(
          "GCP project ID hosting claude.googleapis.com "
          "(required for live 'gcp' runs)."
      ),
  )
  parser.add_argument(
      "--workspace-id",
      default=(
          os.environ.get("ANTHROPIC_WORKSPACE_ID")
          or os.environ.get("ANTHROPIC_GOOGLE_CLOUD_WORKSPACE_ID")
          or None
      ),
      help=(
          "Anthropic Managed Agents workspace ID (auto-discovered if omitted"
          " on 'gcp')."
      ),
  )
  parser.add_argument(
      "--location",
      default=ma_client.DEFAULT_LOCATION,
      help="GCP location for claude.googleapis.com gateway.",
  )
  parser.add_argument(
      "--base-origin",
      default=None,
      help="Optional gateway origin URL override (defaults from --backend).",
  )
  parser.add_argument(
      "--model",
      default=DEFAULT_MODEL,
      help="Claude model ID.",
  )
  parser.add_argument(
      "--effort",
      default=DEFAULT_EFFORT,
      help="Reasoning effort level (low, medium, high, xhigh, max).",
  )
  parser.add_argument(
      "--max-iterations",
      type=int,
      default=DEFAULT_MAX_ITERATIONS,
      help="Max outcome evaluation iterations (default 1 for single-shot).",
  )
  parser.add_argument(
      "--skill",
      default=None,
      help="Filter to a single skill directory name.",
  )
  parser.add_argument(
      "--scenario",
      default=None,
      help="Filter to a single scenario_id.",
  )
  parser.add_argument(
      "--egm-version",
      default=None,
      help="Override detected EGM plugin version.",
  )
  parser.add_argument(
      "--dry-run",
      action="store_true",
      help="Validate bundle, prompts, and rubrics without calling the API.",
  )
  parser.add_argument(
      "--enable-web",
      action="store_true",
      help="Allow web_fetch and web_search tools inside the sandbox.",
  )
  parser.add_argument(
      "--allowed-hosts",
      default=None,
      help=(
          "Optional comma-separated outbound host allowlist for limited"
          " sandbox networking."
      ),
  )
  parser.add_argument(
      "--upload-skill",
      action="store_true",
      help="Upload selected skills via /v1/skills in addition to bundle mount.",
  )
  parser.add_argument(
      "--output-dir",
      default="eval_results",
      help="Directory for JSON report and summary output.",
  )
  parser.add_argument(
      "--markdown-summary",
      default=None,
      help=(
          "Optional path to write Markdown summary (defaults to"
          " output_dir/summary.md)."
      ),
  )
  return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
  args = _parse_args(argv)
  parsed_allowed_hosts = (
      [h.strip() for h in args.allowed_hosts.split(",") if h.strip()]
      if args.allowed_hosts is not None
      else None
  )
  report = run_eval_suite(
      repo_root=pathlib.Path(args.repo_root),
      harness_mode=args.harness_mode,
      backend=args.backend,
      project_id=args.project_id,
      workspace_id=args.workspace_id,
      location=args.location,
      base_origin=args.base_origin,
      model=args.model,
      effort=args.effort,
      max_iterations=args.max_iterations,
      target_skill=args.skill,
      target_scenario=args.scenario,
      egm_version=args.egm_version,
      dry_run=args.dry_run,
      enable_web=args.enable_web,
      allowed_hosts=parsed_allowed_hosts,
      upload_skill=args.upload_skill,
  )

  output_dir = pathlib.Path(args.output_dir)
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / "report.json"
  json_path.write_text(
      json.dumps(dataclasses.asdict(report), indent=2) + "\n",
      encoding="utf-8",
  )

  markdown = render_markdown_summary(report)
  summary_path = (
      pathlib.Path(args.markdown_summary)
      if args.markdown_summary
      else output_dir / "summary.md"
  )
  summary_path.parent.mkdir(parents=True, exist_ok=True)
  summary_path.write_text(markdown, encoding="utf-8")

  print(markdown)
  all_passed = bool(report.results) and all(r.passed for r in report.results)
  return 0 if all_passed else 1


if __name__ == "__main__":
  sys.exit(main())
