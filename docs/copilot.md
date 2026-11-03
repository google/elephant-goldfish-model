<!-- Copyright 2026 Google LLC. SPDX-License-Identifier: Apache-2.0 -->

# GitHub Copilot CLI integration

Experimental adapter for [issue #147](https://github.com/google/elephant-goldfish-model/issues/147).
Workflow execution and reviewer isolation remain unverified. This guide does
not establish support for Copilot in VS Code or the cloud agent.

## Interface and installation

The offline reference version is GitHub Copilot CLI **1.0.82**.
Use the existing Agent Plugins 1.0 root `plugin.json`. Copilot-specific profiles
live in `com.github.copilot/agents/`. The shared skills, personas, and standards
remain in `skills/`, `agents/`, and `resources/`.

Use a complete checkout at a fixed candidate commit. Keep that checkout while
the session runs. Do not copy only `skills/` or install the profile directory alone.
The root manifest takes precedence over the Claude compatibility manifest.
No Copilot hooks, MCP servers, or replacement manifest are required.

Set `EGM_ROOT` to the absolute path of the candidate checkout:

```sh
EGM_ROOT=/absolute/path/to/elephant-goldfish-model
git -C "$EGM_ROOT" rev-parse HEAD
copilot --version
COPILOT_OFFLINE=true copilot --plugin-dir "$EGM_ROOT" plugin list
```

The last command must list `egm` under external plugins. It checks registration,
not reviewer execution. For a separate profile, set `COPILOT_HOME` to a new
directory. This does not disable every user-level skill or project instruction.
Inspect the host inventories before any live test.

After explicit authorization for model usage, start Copilot from the target project:

```sh
copilot --plugin-dir "$EGM_ROOT" --add-dir "$EGM_ROOT" --agent egm:egm
```

In the first message, supply the absolute package root and requested skill:

```text
EGM package root: /absolute/path/to/elephant-goldfish-model
Read that package's docs/copilot.md and run egm-brainstorm.
EGM artifact directory: .dev/docs
```

Use `egm-draft` or `egm-review` in later requests. Provide the target document
for review. Use the `egm:egm` entry agent so the host mapping loads before a skill.
Selecting a reviewer as the main session does not establish a fresh Goldfish context.
Check `/agent` for name conflicts before use; personal profiles can override package profiles.

The verified offline path uses `--plugin-dir`. Persistent installation through
`copilot plugin install` remains unverified. Version 1.0.82 help does not document
local-path installation, although current GitHub documentation does. Do not infer
that a newer command interface works on this version.

## Resource paths

Resolve the package root from the mounted checkout or the native plugin inventory.
For a discovered `skills/<skill>/SKILL.md`, move three parent directories upward.
Read the guide and canonical skill from that root before delegation.

- Resolve `agents/`, `resources/`, and `docs/` against the package root.
- Resolve a skill's `references/` against that skill's directory.
- Resolve user documents against the project working directory.
- Pass absolute paths to reviewers, including the package root, target, and standards.
- Preserve spaces and Unicode characters in paths. Do not split paths on whitespace.
- Stop if any required resource is unavailable. Never substitute a project file.

`<EGM_ROOT>` in a profile is a task-supplied path, not an environment expansion.
This adapter does not assume that Copilot expands variables inside Markdown bodies.

## Native delegation

Use Copilot's native custom-agent delegation tool. Inspect its exposed schema.
Select the registered profile by its namespaced ID; do not invent tool arguments.
Map each canonical persona name to `egm:<name>` for native delegation.
The entry profile permits `agent` for delegation and `edit` for artifacts.
Each reviewer permits only `read` and `search`. Reviewers cannot delegate or write reports.

| Profile | Canonical persona |
| --- | --- |
| `egm:egm-design` | `agents/design_critic.md` |
| `egm:egm-codebase-details` | `agents/codebase_details.md` |
| `egm:egm-comprehension` | `agents/comprehension.md` |
| `egm:egm-implementation-readiness` | `agents/implementation_readiness.md` |
| `egm:egm-structural` | `agents/structural.md` |
| `egm:egm-style` | `agents/style.md` |
| `egm:egm-zoom-out` | `agents/zoom_out.md` |

Start a new native child for every reviewer invocation, including repeat reviews.
Use a task that contains only the requested mode, target, line ranges, persona,
standards, and explicit reading list. Do not forward the conversation, private
rationale, memory, or answers the target should explain.
Do not retrieve parent history or memory.
Read prior reviewer reports only when explicitly supplied in the reading list
and required by the canonical workflow stage. Do not retrieve other prior findings.
For example, Step 8 (Intermediate Zoom Out) requires the caller to include the
absolute path to `zoom_out_report.md` in the reading list. Do not forward other
previous findings.

Use direct dispatch for the shared skills' synthesizer steps. Read the canonical
`agents/synthesizer.md` for reviewer selection and report format. The main session
collects results and writes artifacts. Do not attempt nested delegation or register
an unrestricted synthesizer. Bootstrap workers are outside this adapter's verified scope.

Keep `include-custom-instructions: false` for reviewers. Current GitHub documentation
describes this setting for delegated children, not agents selected as the main session.
The local version's enforcement is unverified. A separate context window alone
does not prove that instructions, memory, or shared files are isolated.

Wait for each native completion before synthesis. Check required resource reads
in host records where available. A missing child, read failure, timeout, or denied
tool makes that stage incomplete. Stop and report the limitation. Never simulate
a child or treat missing findings as a passing result.

## Human gates and artifacts

Follow the canonical skill's approval steps and stage order. Use one plain-text
question and wait when a structured question tool is unavailable. A missing tool
does not grant approval. Do not enable autopilot to bypass these gates.

Write artifacts to the working directory unless the user supplies
`EGM artifact directory: <path>`. Resolve relative artifact paths against that
working directory. Preserve the skill's filenames and report their final paths.
Keep artifact writes in the main session; reviewers return findings only.

## Validation and remaining limits

Run `pytest tests/unit/test_copilot_adapter.py` and `pytest tests/unit` offline.
The host-specific tests check profiles, path resolution, and canonical resource
preservation in a relocated package. They do not call a model.

With CLI 1.0.82 installed, include its offline native discovery check:

```sh
EGM_COPILOT_OFFLINE=1 pytest tests/unit
```

On 2026-10-24, CLI 1.0.82 loaded all eight profiles and seven skills from the
mounted package. The test uses a disposable `COPILOT_HOME` and `COPILOT_OFFLINE=true`.
It starts the installed CLI with `--headless --stdio`, then calls these native
SDK protocol operations without sending a prompt:

1. `session.create` creates a session with a local rejecting provider.
2. `session.agent.list` returns eight `source: plugin` records with absolute profile paths.
3. `session.skills.list` returns seven enabled skills with absolute canonical paths.
4. `session.destroy` removes the session.

The test checks exact IDs, paths, tool lists, reviewer `userInvocable: false`,
and empty agent MCP definitions. The local provider receives **zero requests**.
The model name `gpt-4.1` is session metadata only; no model executes.
No additional manifest mapping is necessary.

The inspected macOS arm64 CLI binary has SHA-256
`948a5e69d924559fdfb2292d9cd8584b8fba28f8fd0349eeefc18711225e340f`.

Representative native records, with the local root abbreviated as `<package>`:

```json
{"id":"egm:egm-design","source":"plugin","path":"<package>/com.github.copilot/agents/egm-design.agent.md","tools":["read","search"],"userInvocable":false,"mcpServers":{}}
{"name":"egm-review","commandName":"egm:egm-review","source":"plugin","path":"<package>/skills/egm-review/SKILL.md","enabled":true}
```

The standalone `skill list` command omitted mounted skills on this version.
Its output is not a session loader inventory. Local `plugins list --help` also
states that custom-agent inspection requires a session. The native SDK inventory
resolves this discovery gap without a model run.

Discovery does not prove skill execution, write denial, or context isolation.
The RPC inventory does not expose `include-custom-instructions` enforcement.
This historical note does not identify the tested EGM commit or installed package
checksum. Repeat discovery against the pinned candidate before relying on it for
that candidate.

Before a support claim, run the existing brainstorm, draft, and review scenarios
from each skill's `test_scenarios.yaml` with explicit model-use authorization.
Record these outcomes separately:

1. Installation: candidate SHA, package identity, complete resources, and loaded profiles.
2. Workflow: host version, model identifier, date, native child starts and completions,
   required reads, artifact paths, and a real human approval pause.
3. Isolation: a random parent-only marker, actual child context, injected instructions,
   memory and MCP exposure, and attempted writes to a disposable fixture.

Inspect tool records to verify write denial. A reviewer promise is not enforcement.
If records are unavailable, retain an unverified result. Read access to shared files
can expose prior findings; fresh context is not a filesystem sandbox.

## Official references

- [Plugin format and precedence](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference)
- [Custom agents and instruction inheritance](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli)
- [Agent tools and aliases](https://docs.github.com/en/copilot/reference/custom-agents-configuration)
- [CLI command reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference)
- [Official SDK protocol operations](https://github.com/github/copilot-sdk/blob/main/python/copilot/generated/rpc.py)

These references describe capabilities. They are not EGM runtime test evidence.
