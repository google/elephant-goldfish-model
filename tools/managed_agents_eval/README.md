# EGM Managed Agents Evaluation Harness

This package runs Elephant-Goldfish Model (EGM) behavioral evaluations through Claude Managed Agents. It uses Python standard library and `pyyaml` only so the same code runs locally and in GitHub Actions.

## Architecture Overview

The runner packages the repository into a clean archive without evaluation rubrics, executes scenarios inside isolated sandboxes, and combines single-shot outcome grading with deterministic per-turn assertions.

### Backends and Authentication

- `gcp` (default): Targets `https://claude.googleapis.com` over `/v1/projects/{project}/locations/{location}/workspaces/{workspace}/invoke/v1/...`. Resolves OAuth bearer tokens from `CLOUDSDK_AUTH_ACCESS_TOKEN_FILE`, `GOOGLE_OAUTH_ACCESS_TOKEN`, or `gcloud` without printing secret values.
- `anthropic`: Targets `https://api.anthropic.com` directly over `/v1/...?beta=true` using `x-api-key` read solely from `ANTHROPIC_API_KEY`.

### Clean Bundle Isolation

`build_clean_plugin_bundle` archives `skills/`, `agents/`, `rules/`, `resources/`, and plugin manifest files into a deterministic gzipped tarball. It excludes `.git`, `__pycache__`, `eval_results`, `.pytest_cache`, `.pyc` files, symlinks, `test_scenarios.yaml`, `EVAL.txtpb`, and `EVAL.textproto` so sandboxed agents cannot read grading criteria.

## Constants and Thresholds

| Constant | Value | Rationale |
| :--- | :--- | :--- |
| `DEFAULT_HTTP_TIMEOUT_SECONDS` | `300` | Allows 5 minutes per SSE stream for multi-step sandbox tool execution and grading. |
| `MAX_BUNDLE_BYTES` | `33554432` | Sets a 32 MiB ceiling to block accidental upload of large artifacts to Files API. |
| `MAX_SSE_EVENTS` | `10000` | Caps SSE frames per stream to bound memory on stalled loops. |
| `DEFAULT_MAX_ITERATIONS` | `1` | Enforces single-shot outcome grading so regressions surface without retry coaching. |
| `DEFAULT_API_VERSION` | `v1` | Targets the stable gateway path instead of older preview paths. |
| `DEFAULT_EFFORT` | `high` | Matches standard interactive EGM reasoning effort during behavioral runs. |

## Usage

### Dry-Run Validation (Offline)

Validate the clean bundle, system prompts, and all scenario rubrics with zero API calls:

```bash
python3 tools/managed_agents_eval/runner.py \
  --repo-root=. \
  --dry-run \
  --output-dir=/tmp/egm_eval_dryrun
```

### Live Run on Google Cloud (`--backend=gcp`)

```bash
export GCP_PROJECT_ID="your-gcp-project-id"
export ANTHROPIC_WORKSPACE_ID="wrkspc_..."
python3 tools/managed_agents_eval/runner.py \
  --repo-root=. \
  --backend=gcp \
  --harness-mode=both \
  --output-dir=/tmp/egm_eval_gcp
```

### Live Run on Direct Anthropic API (`--backend=anthropic`)

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python3 tools/managed_agents_eval/runner.py \
  --repo-root=. \
  --backend=anthropic \
  --harness-mode=both \
  --output-dir=/tmp/egm_eval_anthropic
```

## GitHub Actions Integration

See [the Managed Agents evaluation workflow](../../.github/workflows/managed-agents-eval.yml). Pull requests from forks and repositories without configured credentials automatically run in `--dry-run` mode with zero secret access.
