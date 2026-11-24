# Automated Managed Agents Evaluation Harness

Status: Proposed (Refs #558, Refs #559, Refs #494).
Author: @n3wth. Date: 2026-11-24.

## Problem and scope

The repository stores 71 behavioral scenarios across eight `skills/egm-*/test_scenarios.yaml` files. Offline unit tests check scenario structure, not live model behavior. Maintainers need a reproducible harness to run these suites inside isolated Claude Managed Agents sandboxes.

### Goals

- Package clean plugin archives without evaluation rubrics or symlinks.
- Support both Google Cloud Managed Agents (`gcp`) and direct Anthropic API (`anthropic`) backends.
- Evaluate `multiagent` coordinator mode and `single-agent` mode from the same scenario suite.
- Pair single-shot outcome grading (`user.define_outcome`, `max_iterations=1`) with deterministic per-turn regex and substring assertions.
- Run offline bundle and prompt checks (`--dry-run`) on every pull request without live API spend.

### Non-goals

- Do not block pull request merges or release publishing on live evaluation results. Live runs remain advisory.
- Do not spend API credits on pull requests opened from forks.
- Do not add Python runtime dependencies beyond Python standard library and `pyyaml`.

## Clean archive bundling and rubric stripping

The runner builds a deterministic gzipped tar archive in memory before creating cloud resources. It reads top-level `skills/`, `agents/`, `rules/`, `resources/`, and plugin manifest files.

The packager excludes `.git`, `__pycache__`, `.pytest_cache`, `eval_results`, `.pyc` files, and all symlinks. It also strips `test_scenarios.yaml`, `EVAL.txtpb`, and `EVAL.textproto` from mounted bundles and `/v1/skills` uploads. Sandboxed agents cannot inspect grading criteria or expected regex patterns at runtime.

Tar entries sort lexically with zeroed timestamps, zeroed owners, and uniform `0o644` permissions. Any bundle larger than 32 MiB fails before upload.

## Dual Managed Agents API backends

The client requires `https://` for every non-loopback origin and defaults `base_origin` from the selected backend.

### GCP backend (`gcp`, default)

The `gcp` backend targets `https://claude.googleapis.com`. It routes organization workspace discovery to `/v1/projects/{project}/locations/{location}/claudeOrganization/invoke/v1/organizations/workspaces`. Session calls route to `/v1/projects/{project}/locations/{location}/workspaces/{workspace}/invoke/v1/...`.

Bearer token resolution checks `CLOUDSDK_AUTH_ACCESS_TOKEN_FILE`, then `GOOGLE_OAUTH_ACCESS_TOKEN`, then `gcloud` CLI output. Error messages never print token strings. Live `gcp` runs require a non-empty `project_id`.

### Direct Anthropic backend (`anthropic`, optional)

The `anthropic` backend targets `https://api.anthropic.com` for maintainers without a Google Cloud project. It sends requests directly to `/v1/...?beta=true` with an `x-api-key` header read solely from `ANTHROPIC_API_KEY`. It never sends an `Authorization` header and rejects `list_workspaces()` calls.

## Harness parity modes

The runner supports `multiagent`, `single-agent`, and `both` harness modes. In `multiagent` mode, agent payloads set `multiagent` to `{"type": "coordinator", "agents": [{"type": "self"}]}`. In `single-agent` mode, the payload omits `multiagent`. Comparing both modes detects regressions in subagent delegation versus single-context execution.

## Single-shot outcome grading and deterministic assertions

Each live scenario opens a session with a `user.define_outcome` event (`max_iterations=1`) and sequential `user.message` turns. Single-shot grading surfaces first-attempt failures without retry coaching.

The client reads SSE frames up to a 300-second deadline and a 10,000-event ceiling. It rejects premature EOF or `error` frames. After session completion, the runner evaluates each turn response against its `required_pattern`, `forbidden_pattern`, `contains`, and `not_contains` rules.

A scenario passes only when both the outcome verdict and every deterministic turn assertion succeed. Markdown summaries sanitize untrusted model output by stripping links, images, HTML tags, and pipes.

## Workflow security boundaries

The GitHub Actions workflow sets top-level `permissions: contents: read`. Every action uses a pinned commit SHA, and checkout steps set `persist-credentials: false`.

Sandbox environments default to network isolation (`networking.type = "limited"` with `allowed_hosts = []`) unless the caller enables web tools. Agent toolsets set `default_config: {"enabled": false}` and explicitly enable only core file and shell tools.

Pull requests from forks and unconfigured repositories automatically run in `--dry-run` mode with zero secret access. Optional pull request summary comments run in a separate checkout-free job with `pull-requests: write`.

## Numeric constants rationale

| Constant | Value | Rationale |
| :--- | :--- | :--- |
| `DEFAULT_HTTP_TIMEOUT_SECONDS` | `300` | Allows five minutes per SSE stream for sandbox tool execution and grading. |
| `MAX_BUNDLE_BYTES` | `33554432` | Sets a 32 MiB ceiling to block accidental upload of large artifacts. |
| `MAX_SSE_EVENTS` | `10000` | Caps SSE frames per stream to bound memory on stalled loops. |
| `DEFAULT_MAX_ITERATIONS` | `1` | Enforces single-shot outcome grading so regressions surface on the first attempt. |
| `DEFAULT_API_VERSION` | `v1` | Targets the stable gateway path for Managed Agents calls. |
| `DEFAULT_EFFORT` | `high` | Matches standard interactive EGM reasoning effort during behavioral runs. |
