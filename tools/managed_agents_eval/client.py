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

"""Stdlib-only client for Claude Managed Agents on GCP or direct Anthropic API.

Targets either the Google Cloud `claude.googleapis.com` gateway using OAuth
bearer tokens or `api.anthropic.com` directly using `ANTHROPIC_API_KEY`.
Requires zero external packages so the same module runs cleanly in local shells
and GitHub Actions.
"""

from __future__ import annotations

import dataclasses
import http.client
import json
import os
import pathlib
import subprocess
import time
from typing import Any, Callable, Sequence
import urllib.error
import urllib.parse
import urllib.request
import uuid

# Empty by default so callers configure their own project explicitly.
DEFAULT_PROJECT_ID = ""

# Default Managed Agents API backend (`gcp` gateway or direct `anthropic` API).
DEFAULT_BACKEND = "gcp"

GCP_DEFAULT_BASE_ORIGIN = "https://claude.googleapis.com"
ANTHROPIC_DEFAULT_BASE_ORIGIN = "https://api.anthropic.com"
SUPPORTED_BACKENDS = frozenset({"gcp", "anthropic"})

# Global routing endpoint required by claude.googleapis.com Managed Agents.
DEFAULT_LOCATION = "global"

# Stable gateway path (/v1/.../invoke), avoiding older preview defaults.
DEFAULT_API_VERSION = "v1"

# Standard Anthropic API version header expected by both backends.
ANTHROPIC_VERSION = "2023-06-01"

# Beta header enabling environments, agents, sessions, and outcome grading.
BETA_MANAGED_AGENTS = "managed-agents-2026-04-01"

# Beta header enabling custom skill directory uploads (/v1/skills).
BETA_SKILLS = "skills-2025-10-02"

# Beta header enabling multipart file uploads (/v1/files).
BETA_FILES = "files-api-2025-04-14"

# 5-minute per-stream socket timeout accommodating multi-step sandbox tool
# execution and outcome grader passes without premature disconnects.
DEFAULT_HTTP_TIMEOUT_SECONDS = 300

# 32 MiB ceiling guarding Files API uploads against accidental inclusion of
# large build outputs, logs, or vendored binary artifacts in a plugin bundle.
MAX_BUNDLE_BYTES = 32 * 1024 * 1024

# Caps SSE frames per stream to prevent unbounded memory growth if a server
# keeps emitting keepalive events without reaching a terminal session status.
MAX_SSE_EVENTS = 10_000

_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})

_IGNORED_SKILL_PARTS = frozenset(
    {"__pycache__", ".git", ".pytest_cache", ".DS_Store", "eval_results"}
)

# Evaluation rubric and test files excluded from /v1/skills uploads so the
# sandboxed agent cannot read grading criteria or regex patterns at runtime.
_EXCLUDED_SKILL_FILES = frozenset(
    {"test_scenarios.yaml", "EVAL.txtpb", "EVAL.textproto"}
)


class ClaudeManagedAgentsError(RuntimeError):
  """Raised on Managed Agents transport, SSE stream, or API failures."""


class ClaudeApiError(ClaudeManagedAgentsError):
  """Raised when the Managed Agents API returns an HTTP error."""

  def __init__(self, status_code: int, message: str, body: str = "") -> None:
    self.status_code = status_code
    self.body = body
    super().__init__(f"HTTP {status_code}: {message}")


@dataclasses.dataclass
class TokenUsage:
  """Aggregate token counters across model requests and outcome grading."""

  input_tokens: int = 0
  output_tokens: int = 0
  cache_read_input_tokens: int = 0
  cache_creation_input_tokens: int = 0

  @property
  def total_tokens(self) -> int:
    """Returns total tokens billed across input, output, and prompt cache."""
    return (
        self.input_tokens
        + self.output_tokens
        + self.cache_read_input_tokens
        + self.cache_creation_input_tokens
    )

  def add_usage_dict(self, usage: dict[str, Any] | None) -> None:
    """Accumulates token counts from a Managed Agents usage payload."""
    if not isinstance(usage, dict):
      return
    self.input_tokens += int(usage.get("input_tokens", 0) or 0)
    self.output_tokens += int(usage.get("output_tokens", 0) or 0)
    self.cache_read_input_tokens += int(
        usage.get("cache_read_input_tokens", 0) or 0
    )
    self.cache_creation_input_tokens += int(
        usage.get("cache_creation_input_tokens", 0) or 0
    )


@dataclasses.dataclass
class OutcomeEvaluation:
  """Verdict emitted by the built-in user.define_outcome evaluator."""

  outcome_id: str
  result: str
  explanation: str
  iteration: int


@dataclasses.dataclass
class SessionEvalOutcome:
  """Aggregated transcript, tool counts, verdict, usage, and timing."""

  session_id: str
  agent_id: str
  environment_id: str
  assistant_messages: list[str]
  final_response: str
  tool_use_count: int
  tool_error_count: int
  thinking_events: int
  trajectory_events: list[dict[str, Any]]
  outcome_evaluation: OutcomeEvaluation | None
  stop_reason: str
  usage: TokenUsage
  duration_ms: int
  turn_responses: list[str] = dataclasses.field(default_factory=list)
  error_message: str | None = None


def resolve_gcloud_access_token(gcloud_bin: str = "gcloud") -> str:
  """Resolves a GCP OAuth access token without logging secret material.

  Resolution order:
    1. CLOUDSDK_AUTH_ACCESS_TOKEN_FILE (OAuth token file path).
    2. GOOGLE_OAUTH_ACCESS_TOKEN environment variable.
    3. `gcloud auth application-default print-access-token`, falling back to
       `gcloud auth print-access-token`.

  Args:
    gcloud_bin: Path or binary name for the gcloud CLI.

  Returns:
    Stripped OAuth bearer token string.

  Raises:
    RuntimeError: If no valid non-empty access token can be resolved.
  """
  token_file = os.environ.get("CLOUDSDK_AUTH_ACCESS_TOKEN_FILE", "").strip()
  if token_file:
    try:
      token = pathlib.Path(token_file).read_text(encoding="utf-8").strip()
    except OSError as exc:
      raise RuntimeError(
          "Failed to read CLOUDSDK_AUTH_ACCESS_TOKEN_FILE."
      ) from exc
    if not token:
      raise RuntimeError("CLOUDSDK_AUTH_ACCESS_TOKEN_FILE is empty.")
    return token

  env_token = os.environ.get("GOOGLE_OAUTH_ACCESS_TOKEN", "").strip()
  if env_token:
    return env_token

  commands = (
      [gcloud_bin, "auth", "application-default", "print-access-token"],
      [gcloud_bin, "auth", "print-access-token"],
  )
  failures: list[str] = []
  for cmd in commands:
    try:
      proc = subprocess.run(
          cmd,
          capture_output=True,
          text=True,
          timeout=15,
          check=False,
      )
    except (OSError, subprocess.SubprocessError) as exc:
      failures.append(f"{' '.join(cmd[:3])}: {type(exc).__name__}")
      continue
    if proc.returncode == 0:
      candidate = proc.stdout.strip()
      if candidate:
        return candidate
      failures.append(f"{' '.join(cmd[:3])}: empty output")
    else:
      failures.append(f"{' '.join(cmd[:3])}: exit {proc.returncode}")

  raise RuntimeError(
      "Unable to resolve GCP OAuth access token (" + "; ".join(failures) + ")."
  )


def resolve_anthropic_api_key() -> str:
  """Resolves an Anthropic API key from ANTHROPIC_API_KEY without leaking it."""
  api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
  if not api_key:
    raise RuntimeError(
        "ANTHROPIC_API_KEY environment variable is unset or empty."
    )
  return api_key


def _default_base_origin_for_backend(backend: str) -> str:
  """Returns the default HTTPS origin for a validated backend."""
  if backend == "anthropic":
    return ANTHROPIC_DEFAULT_BASE_ORIGIN
  return GCP_DEFAULT_BASE_ORIGIN


def _sanitize_header_token(value: str) -> str:
  """Removes quotes and CR/LF characters to prevent multipart header injection."""
  return value.replace('"', "").replace("\r", "").replace("\n", "")


def _encode_multipart(
    fields: list[tuple[str, str]],
    files: list[tuple[str, str, bytes, str]],
) -> tuple[bytes, str]:
  """Encodes RFC 7578 multipart/form-data payload using stdlib only."""
  boundary = f"----EgmManagedAgents{uuid.uuid4().hex}"
  chunks: list[bytes] = []

  for name, value in fields:
    safe_name = _sanitize_header_token(name)
    chunks.append(
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{safe_name}"\r\n\r\n'
            f"{value}\r\n"
        ).encode("utf-8")
    )

  for field_name, filename, content, content_type in files:
    safe_field = _sanitize_header_token(field_name)
    safe_filename = _sanitize_header_token(filename)
    safe_ctype = _sanitize_header_token(content_type)
    chunks.append(
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{safe_field}"; '
            f'filename="{safe_filename}"\r\n'
            f"Content-Type: {safe_ctype}\r\n\r\n"
        ).encode("utf-8")
    )
    chunks.append(content)
    chunks.append(b"\r\n")

  chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
  body = b"".join(chunks)
  return body, f"multipart/form-data; boundary={boundary}"


def _extract_text_from_blocks(blocks: Any) -> str:
  """Extracts concatenated text from Anthropic message content blocks."""
  if not isinstance(blocks, list):
    return ""
  parts: list[str] = []
  for block in blocks:
    if isinstance(block, dict) and block.get("type") == "text":
      text = block.get("text")
      if isinstance(text, str) and text:
        parts.append(text)
  return "".join(parts)


def _validate_base_origin(base_origin: str) -> str:
  """Enforces https:// for non-loopback origins so credentials stay encrypted."""
  cleaned = base_origin.rstrip("/")
  parsed = urllib.parse.urlparse(cleaned)
  if not parsed.netloc:
    raise ValueError(f"Invalid base_origin (missing host): {base_origin!r}")
  if parsed.scheme == "https":
    return cleaned
  if parsed.scheme == "http" and parsed.hostname in _LOOPBACK_HOSTS:
    return cleaned
  raise ValueError(
      f"Insecure or unsupported base_origin scheme for {base_origin!r}: "
      "must use https:// (or http:// on loopback)."
  )


class ClaudeManagedAgentsClient:
  """Typed stdlib client for Claude Managed Agents (`gcp` or `anthropic`)."""

  def __init__(
      self,
      project_id: str = DEFAULT_PROJECT_ID,
      workspace_id: str | None = None,
      location: str = DEFAULT_LOCATION,
      api_version: str = DEFAULT_API_VERSION,
      base_origin: str | None = None,
      token_provider: Callable[[], str] | None = None,
      timeout_seconds: int = DEFAULT_HTTP_TIMEOUT_SECONDS,
      backend: str = DEFAULT_BACKEND,
  ) -> None:
    if backend not in SUPPORTED_BACKENDS:
      supported = ", ".join(sorted(SUPPORTED_BACKENDS))
      raise ValueError(
          f"Unsupported backend {backend!r}; expected one of: {supported}."
      )
    self.backend = backend
    self.project_id = project_id
    self.workspace_id = workspace_id
    self.location = location
    self.api_version = api_version.strip("/")
    effective_origin = (
        base_origin
        if base_origin is not None
        else _default_base_origin_for_backend(backend)
    )
    self.base_origin = _validate_base_origin(effective_origin)
    if token_provider is not None:
      self._token_provider = token_provider
    elif backend == "anthropic":
      self._token_provider = resolve_anthropic_api_key
    else:
      self._token_provider = resolve_gcloud_access_token
    self.timeout_seconds = timeout_seconds

  def __repr__(self) -> str:
    return (
        f"ClaudeManagedAgentsClient(backend={self.backend!r}, "
        f"project_id={self.project_id!r}, "
        f"workspace_id={self.workspace_id!r}, location={self.location!r}, "
        f"api_version={self.api_version!r}, base_origin={self.base_origin!r})"
    )

  @property
  def org_invoke_url(self) -> str:
    """Returns organization-level invoke base URL for the `gcp` backend."""
    if self.backend != "gcp":
      raise ValueError(
          "Organization workspace URLs are only supported on the 'gcp' backend."
      )
    if not self.project_id.strip():
      raise ValueError(
          "project_id is required for GCP Managed Agents organization calls."
      )
    proj = urllib.parse.quote(self.project_id, safe="")
    loc = urllib.parse.quote(self.location, safe="")
    ver = urllib.parse.quote(self.api_version, safe="")
    return (
        f"{self.base_origin}/{ver}/projects/{proj}"
        f"/locations/{loc}/claudeOrganization/invoke"
    )

  @property
  def workspace_invoke_url(self) -> str:
    """Returns base URL for workspace-scoped Managed Agents endpoints."""
    if self.backend == "anthropic":
      return self.base_origin
    if not self.project_id.strip():
      raise ValueError(
          "project_id is required for GCP Managed Agents calls."
      )
    if not self.workspace_id:
      raise ValueError(
          "workspace_id is required for workspace-scoped Managed Agents calls."
      )
    proj = urllib.parse.quote(self.project_id, safe="")
    loc = urllib.parse.quote(self.location, safe="")
    ws = urllib.parse.quote(self.workspace_id, safe="")
    ver = urllib.parse.quote(self.api_version, safe="")
    return (
        f"{self.base_origin}/{ver}/projects/{proj}"
        f"/locations/{loc}/workspaces/{ws}/invoke"
    )

  def _auth_headers(
      self,
      *,
      beta: str | None = None,
      content_type: str | None = "application/json",
      accept: str = "application/json",
  ) -> dict[str, str]:
    """Builds authenticated HTTP headers for the configured backend."""
    credential = self._token_provider().strip()
    if not credential:
      raise RuntimeError("Credential provider returned an empty secret.")
    headers: dict[str, str] = {
        "anthropic-version": ANTHROPIC_VERSION,
        "Accept": accept,
    }
    if self.backend == "anthropic":
      headers["x-api-key"] = credential
    else:
      headers["Authorization"] = f"Bearer {credential}"
    if beta:
      headers["anthropic-beta"] = beta
    if content_type:
      headers["Content-Type"] = content_type
    return headers

  def _request_json(
      self,
      method: str,
      url: str,
      *,
      payload: dict[str, Any] | None = None,
      raw_body: bytes | None = None,
      content_type: str | None = "application/json",
      beta: str | None = None,
  ) -> dict[str, Any]:
    """Sends an HTTP request and parses the JSON response body."""
    body_bytes = raw_body
    if payload is not None:
      body_bytes = json.dumps(payload).encode("utf-8")
    elif body_bytes is None and method in ("GET", "DELETE"):
      content_type = None

    headers = self._auth_headers(beta=beta, content_type=content_type)
    req = urllib.request.Request(
        url=url,
        data=body_bytes,
        headers=headers,
        method=method,
    )
    try:
      with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
      err_body = exc.read().decode("utf-8", errors="replace")
      raise ClaudeApiError(exc.code, exc.reason, err_body) from exc
    except (
        urllib.error.URLError,
        http.client.HTTPException,
        TimeoutError,
        OSError,
    ) as exc:
      raise ClaudeManagedAgentsError(f"Request to {url} failed: {exc}") from exc

  def list_workspaces(self) -> list[dict[str, Any]]:
    """Lists Anthropic workspaces accessible to the caller on the `gcp` backend."""
    if self.backend != "gcp":
      raise ValueError(
          "list_workspaces() is only supported on backend='gcp'."
      )
    url = f"{self.org_invoke_url}/v1/organizations/workspaces"
    response = self._request_json("GET", url)
    if isinstance(response, dict):
      data = response.get("data", [])
      return list(data) if isinstance(data, list) else []
    return list(response) if isinstance(response, list) else []

  def create_environment(
      self,
      name: str,
      pip_packages: list[str] | None = None,
      allowed_hosts: list[str] | None = None,
      metadata: dict[str, str] | None = None,
  ) -> dict[str, Any]:
    """Creates a cloud sandbox environment via POST /v1/environments."""
    if allowed_hosts is None:
      networking: dict[str, Any] = {"type": "unrestricted"}
    else:
      networking = {
          "type": "limited",
          "allowed_hosts": list(allowed_hosts),
          "allow_mcp_servers": False,
          "allow_package_managers": True,
      }

    config: dict[str, Any] = {
        "type": "cloud",
        "networking": networking,
    }
    if pip_packages:
      config["packages"] = {
          "type": "packages",
          "pip": list(pip_packages),
      }

    payload: dict[str, Any] = {
        "name": name,
        "config": config,
    }
    if metadata:
      payload["metadata"] = dict(metadata)

    url = f"{self.workspace_invoke_url}/v1/environments?beta=true"
    return self._request_json(
        "POST", url, payload=payload, beta=BETA_MANAGED_AGENTS
    )

  def upload_bundle(
      self,
      bundle_bytes: bytes,
      filename: str = "egm_plugin.tar.gz",
  ) -> dict[str, Any]:
    """Uploads a plugin archive via POST /v1/files?beta=true."""
    if len(bundle_bytes) > MAX_BUNDLE_BYTES:
      raise ValueError(
          f"Bundle size {len(bundle_bytes)} bytes exceeds MAX_BUNDLE_BYTES "
          f"({MAX_BUNDLE_BYTES} bytes)."
      )
    body, content_type = _encode_multipart(
        fields=[],
        files=[("file", filename, bundle_bytes, "application/gzip")],
    )
    url = f"{self.workspace_invoke_url}/v1/files?beta=true"
    return self._request_json(
        "POST",
        url,
        raw_body=body,
        content_type=content_type,
        beta=BETA_FILES,
    )

  def upload_skill_dir(
      self,
      skill_dir: pathlib.Path,
      display_title: str | None = None,
  ) -> dict[str, Any]:
    """Uploads a custom skill directory via POST /v1/skills?beta=true."""
    resolved_dir = skill_dir.resolve()
    if not (resolved_dir / "SKILL.md").is_file():
      raise ValueError(
          f"Skill directory {resolved_dir} must contain SKILL.md at its root."
      )

    file_parts: list[tuple[str, str, bytes, str]] = []
    for file_path in sorted(resolved_dir.rglob("*")):
      if file_path.is_symlink() or not file_path.is_file():
        continue
      resolved_file = file_path.resolve()
      if not resolved_file.is_relative_to(resolved_dir):
        continue
      rel = file_path.relative_to(resolved_dir)
      if any(part in _IGNORED_SKILL_PARTS for part in rel.parts):
        continue
      if rel.name in _EXCLUDED_SKILL_FILES:
        continue
      if file_path.suffix == ".pyc":
        continue
      multipart_name = f"{resolved_dir.name}/{rel.as_posix()}"
      ctype = "text/markdown" if file_path.suffix == ".md" else "text/plain"
      file_parts.append(
          ("files", multipart_name, resolved_file.read_bytes(), ctype)
      )

    fields: list[tuple[str, str]] = []
    if display_title:
      fields.append(("display_title", display_title))

    body, content_type = _encode_multipart(fields=fields, files=file_parts)
    url = f"{self.workspace_invoke_url}/v1/skills?beta=true"
    return self._request_json(
        "POST",
        url,
        raw_body=body,
        content_type=content_type,
        beta=BETA_SKILLS,
    )

  def create_agent(
      self,
      name: str,
      model: str,
      system: str,
      enable_multiagent: bool = True,
      subagent_refs: list[Any] | None = None,
      skill_ids: list[str] | None = None,
      effort: str = "high",
      enable_web: bool = False,
      metadata: dict[str, str] | None = None,
  ) -> dict[str, Any]:
    """Creates a Managed Agent via POST /v1/agents?beta=true."""
    web_policy = (
        {"enabled": True, "permission_policy": {"type": "always_allow"}}
        if enable_web
        else {"enabled": False}
    )
    tool_configs: list[dict[str, Any]] = [
        {
            "name": tool_name,
            "enabled": True,
            "permission_policy": {"type": "always_allow"},
        }
        for tool_name in ("bash", "read", "write", "edit", "glob", "grep")
    ]
    tool_configs.extend([
        {"name": "web_fetch", **web_policy},
        {"name": "web_search", **web_policy},
    ])

    payload: dict[str, Any] = {
        "name": name,
        "model": {"id": model, "effort": effort} if effort else model,
        "system": system,
        "tools": [{
            "type": "agent_toolset_20260401",
            "default_config": {"enabled": False},
            "configs": tool_configs,
        }],
    }
    if skill_ids:
      payload["skills"] = [
          {"type": "custom", "skill_id": sid} for sid in skill_ids
      ]
    if enable_multiagent:
      payload["multiagent"] = {
          "type": "coordinator",
          "agents": (
              list(subagent_refs)
              if subagent_refs is not None
              else [{"type": "self"}]
          ),
      }
    if metadata:
      payload["metadata"] = dict(metadata)

    url = f"{self.workspace_invoke_url}/v1/agents?beta=true"
    return self._request_json(
        "POST", url, payload=payload, beta=BETA_MANAGED_AGENTS
    )

  def send_session_events(
      self, session_id: str, events: list[dict[str, Any]]
  ) -> dict[str, Any]:
    """Sends follow-up events to an active session."""
    quoted_sid = urllib.parse.quote(session_id, safe="")
    url = (
        f"{self.workspace_invoke_url}/v1/sessions/{quoted_sid}/events?beta=true"
    )
    return self._request_json(
        "POST",
        url,
        payload={"events": events},
        beta=BETA_MANAGED_AGENTS,
    )

  def _iter_sse_events(
      self, session_id: str, deadline: float | None = None
  ) -> list[tuple[str, dict[str, Any]]]:
    """Connects to SSE stream and yields events until idle or terminated."""
    quoted_sid = urllib.parse.quote(session_id, safe="")
    url = (
        f"{self.workspace_invoke_url}/v1/sessions/{quoted_sid}"
        "/events/stream?beta=true"
    )
    headers = self._auth_headers(
        beta=BETA_MANAGED_AGENTS,
        content_type=None,
        accept="text/event-stream",
    )
    req = urllib.request.Request(url=url, headers=headers, method="GET")
    collected: list[tuple[str, dict[str, Any]]] = []
    effective_deadline = (
        deadline
        if deadline is not None
        else time.monotonic() + self.timeout_seconds
    )
    saw_terminal = False

    def _dispatch_frame(
        ev_name: str, data_lines: list[str]
    ) -> tuple[bool, tuple[str, dict[str, Any]] | None]:
      payload_str = "\n".join(data_lines)
      if ev_name == "ping" and not payload_str.strip().startswith("{"):
        return False, None
      try:
        parsed = json.loads(payload_str)
      except json.JSONDecodeError as exc:
        if ev_name == "error":
          raise ClaudeManagedAgentsError(
              f"SSE error frame for {session_id}: {payload_str}"
          ) from exc
        if payload_str.strip() in ("", "ping"):
          return False, None
        return False, None

      if not isinstance(parsed, dict):
        return False, None

      ev_type = str(parsed.get("type") or ev_name)
      if ev_name == "error" or ev_type in ("error", "session.error"):
        err_detail = parsed.get("error") or parsed.get("message") or parsed
        raise ClaudeManagedAgentsError(
            f"SSE session error for {session_id}: {err_detail}"
        )
      terminal = ev_type in ("session.status_idle", "session.status_terminated")
      return terminal, (ev_name, parsed)

    try:
      remaining = max(0.1, effective_deadline - time.monotonic())
      with urllib.request.urlopen(req, timeout=remaining) as resp:
        event_name = ""
        data_lines: list[str] = []
        while True:
          if time.monotonic() > effective_deadline:
            raise ClaudeManagedAgentsError(
                "SSE stream exceeded overall deadline"
                f" ({self.timeout_seconds}s) for {session_id}."
            )
          raw_line = resp.readline()
          if not raw_line:
            if data_lines:
              terminal, item = _dispatch_frame(event_name, data_lines)
              if item is not None:
                if len(collected) >= MAX_SSE_EVENTS:
                  raise ClaudeManagedAgentsError(
                      f"SSE stream exceeded {MAX_SSE_EVENTS} events for"
                      f" {session_id}."
                  )
                collected.append(item)
              if terminal:
                saw_terminal = True
            break
          line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
          if not line:
            if data_lines:
              terminal, item = _dispatch_frame(event_name, data_lines)
              event_name = ""
              data_lines = []
              if item is not None:
                if len(collected) >= MAX_SSE_EVENTS:
                  raise ClaudeManagedAgentsError(
                      f"SSE stream exceeded {MAX_SSE_EVENTS} events for"
                      f" {session_id}."
                  )
                collected.append(item)
              if terminal:
                saw_terminal = True
                break
            else:
              event_name = ""
            continue
          if line.startswith(":"):
            continue
          if line.startswith("event:"):
            event_name = (
                line[7:] if line.startswith("event: ") else line[6:]
            ).strip()
          elif line.startswith("data:"):
            data_lines.append(
                line[6:] if line.startswith("data: ") else line[5:]
            )
    except urllib.error.HTTPError as exc:
      err_body = exc.read().decode("utf-8", errors="replace")
      raise ClaudeApiError(exc.code, exc.reason, err_body) from exc
    except (
        urllib.error.URLError,
        http.client.HTTPException,
        TimeoutError,
        OSError,
    ) as exc:
      raise ClaudeManagedAgentsError(
          f"SSE stream failed for {session_id}: {exc}"
      ) from exc

    if not saw_terminal:
      raise ClaudeManagedAgentsError(
          "SSE stream ended prematurely before session.status_idle or"
          f" session.status_terminated for {session_id}."
      )

    return collected

  def run_eval_session(
      self,
      agent_id: str,
      environment_id: str,
      user_prompt: str = "",
      outcome_description: str = "",
      rubric_text: str = "",
      bundle_file_id: str | None = None,
      bundle_mount_path: str = "/mnt/session/uploads/egm_plugin.tar.gz",
      max_iterations: int = 1,
      title: str | None = None,
      metadata: dict[str, str] | None = None,
      turns: Sequence[str] | None = None,
  ) -> SessionEvalOutcome:
    """Runs a single- or multi-turn Managed Agents session and parses SSE."""
    turn_prompts = (
        list(turns)
        if turns is not None
        else ([user_prompt] if user_prompt else [])
    )
    if not turn_prompts:
      raise ValueError("At least one user turn prompt is required.")

    start = time.monotonic()
    deadline = start + self.timeout_seconds

    initial_events: list[dict[str, Any]] = []
    if outcome_description or rubric_text:
      initial_events.append({
          "type": "user.define_outcome",
          "description": outcome_description,
          "rubric": {"type": "text", "content": rubric_text},
          "max_iterations": max_iterations,
      })
    initial_events.append({
        "type": "user.message",
        "content": [{"type": "text", "text": turn_prompts[0]}],
    })

    payload: dict[str, Any] = {
        "agent": agent_id,
        "environment_id": environment_id,
        "initial_events": initial_events,
    }
    if bundle_file_id:
      payload["resources"] = [{
          "type": "file",
          "file_id": bundle_file_id,
          "mount_path": bundle_mount_path,
      }]
    if title:
      payload["title"] = title
    if metadata:
      payload["metadata"] = dict(metadata)

    create_url = f"{self.workspace_invoke_url}/v1/sessions?beta=true"
    session = self._request_json(
        "POST", create_url, payload=payload, beta=BETA_MANAGED_AGENTS
    )
    session_id = str(session["id"])

    assistant_messages: list[str] = []
    turn_responses: list[str] = []
    tool_use_count = 0
    tool_error_count = 0
    thinking_events = 0
    trajectory_events: list[dict[str, Any]] = []
    outcome_evaluation: OutcomeEvaluation | None = None
    stop_reason = ""
    error_message: str | None = None
    usage = TokenUsage()

    for turn_idx, turn_text in enumerate(turn_prompts):
      if turn_idx > 0:
        if stop_reason != "end_turn":
          error_message = (
              f"Session stopped with {stop_reason!r} before turn"
              f" {turn_idx + 1}."
          )
          break
        self.send_session_events(
            session_id,
            [{
                "type": "user.message",
                "content": [{"type": "text", "text": turn_text}],
            }],
        )

      try:
        events = self._iter_sse_events(session_id, deadline=deadline)
      except ClaudeManagedAgentsError as exc:
        error_message = str(exc)
        break

      turn_messages: list[str] = []
      for sse_name, ev in events:
        ev_type = str(ev.get("type") or sse_name)
        if ev_type == "agent.thinking":
          thinking_events += 1
          trajectory_events.append({"type": ev_type})
        elif ev_type == "agent.tool_use":
          tool_use_count += 1
          trajectory_events.append({
              "type": ev_type,
              "name": ev.get("name", ""),
              "id": ev.get("id", ""),
          })
        elif ev_type == "agent.tool_result":
          is_err = bool(ev.get("is_error", False))
          if is_err:
            tool_error_count += 1
          trajectory_events.append({
              "type": ev_type,
              "tool_use_id": ev.get("tool_use_id", ""),
              "is_error": is_err,
          })
        elif ev_type == "agent.message":
          text = _extract_text_from_blocks(ev.get("content"))
          if text:
            assistant_messages.append(text)
            turn_messages.append(text)
          trajectory_events.append({"type": ev_type, "chars": len(text)})
        elif ev_type == "span.model_request_end":
          usage.add_usage_dict(ev.get("model_usage"))
          trajectory_events.append({"type": ev_type})
        elif ev_type == "span.outcome_evaluation_end":
          usage.add_usage_dict(ev.get("usage"))
          outcome_evaluation = OutcomeEvaluation(
              outcome_id=str(ev.get("outcome_id", "")),
              result=str(ev.get("result", "")),
              explanation=str(ev.get("explanation", "")),
              iteration=int(ev.get("iteration", 0) or 0),
          )
          trajectory_events.append({
              "type": ev_type,
              "result": outcome_evaluation.result,
              "iteration": outcome_evaluation.iteration,
          })
        elif ev_type == "session.status_idle":
          raw_stop = ev.get("stop_reason")
          if isinstance(raw_stop, dict):
            stop_reason = str(raw_stop.get("type", ""))
          elif raw_stop is not None:
            stop_reason = str(raw_stop)
          trajectory_events.append(
              {"type": ev_type, "stop_reason": stop_reason}
          )
        elif ev_type == "session.status_terminated":
          stop_reason = "terminated"
          trajectory_events.append({"type": ev_type})

      turn_responses.append("\n\n".join(msg for msg in turn_messages if msg))

    duration_ms = int((time.monotonic() - start) * 1000)
    final_response = "\n\n".join(msg for msg in assistant_messages if msg)

    return SessionEvalOutcome(
        session_id=session_id,
        agent_id=agent_id,
        environment_id=environment_id,
        assistant_messages=assistant_messages,
        final_response=final_response,
        tool_use_count=tool_use_count,
        tool_error_count=tool_error_count,
        thinking_events=thinking_events,
        trajectory_events=trajectory_events,
        outcome_evaluation=outcome_evaluation,
        stop_reason=stop_reason,
        usage=usage,
        duration_ms=duration_ms,
        turn_responses=turn_responses,
        error_message=error_message,
    )
