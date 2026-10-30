<!-- Copyright 2026 Google LLC. SPDX-License-Identifier: Apache-2.0 -->

# OpenCode V1 integration (experimental)

This adapter targets OpenCode CLI **1.18.29**, with V1 `task` and `permission` interfaces.
It does not target V2 `subagent` or `permissions` interfaces.
Installation checks do not establish workflow or isolation support.
Maintainer approval, live workflows, and isolation verification remain pending under [#146](https://github.com/google/elephant-goldfish-model/issues/146).
The proposed architecture is in [the additional harness design](designs/additional-harnesses.md).

## Install

Use Python 3.10+ and a POSIX filesystem with symbolic links.
Select a fixed candidate commit before installation. Keep the installation at its original path.
The installer copies the complete canonical resource trees. It does not change global or project configuration.
It refuses an existing destination. Use a new destination for each candidate.

```sh
git rev-parse HEAD
python3 adapters/opencode/install.py /absolute/egm-opencode-candidate
opencode --version
```

Require version `1.18.29` before launch. Install that exact version if necessary:

```sh
npm install --prefix /absolute/opencode-v1 opencode-ai@1.18.29
/absolute/opencode-v1/node_modules/.bin/opencode --version
```

Inspect the generated `opencode.json` and `installation.json` before use.
The latter records package identity and SHA-256 hashes of all bundled files.
The native configuration contains seven commands, seven reviewers, and the `egm` primary agent.
Native skill aliases use the canonical frontmatter names and link to the unchanged skill directories.

Start OpenCode from the project directory with the candidate configuration:

```sh
OPENCODE_CONFIG=/absolute/egm-opencode-candidate/opencode.json opencode --agent egm
```

Model calls require separate user authorization. Installation and version checks do not require model calls.
Select `egm` before native skill use. Other primary agents do not receive this adapter's dispatch instructions.
For review text, use an ordinary message rather than a slash command. For example:

```text
Use the egm-review skill to review /absolute/path/design.md.
```

Paste material into that ordinary message, or save it in a file for the agent to read.
The generated `/egm-brainstorm`, `/egm-draft`, and `/egm-review` commands retain
OpenCode's native command syntax. Their arguments are not literal text: OpenCode
evaluates shell markers (an exclamation mark followed by a command in backticks)
before agent tool permissions apply. Do not paste untrusted review material into
slash-command arguments. Markdown fences do not disable this preprocessing.

To uninstall, stop sessions and remove only this candidate directory. Remove its environment override.

## Paths and dispatch

Use the absolute bundle root in the generated prompt.
Resolve `agents/`, `resources/`, and `docs/` against that root.
Resolve `references/` against the canonical skill directory, after resolving its alias.
Resolve user files against the project directory. Never substitute project files for bundled personas.

Dispatch reviewers directly from `egm` with the V1 `task` tool.
Set `subagent_type` to the persona's canonical frontmatter name.
Supply `description` and `prompt`. Omit `task_id` to create a fresh session.
Use foreground tasks. Do not enable background dispatch or reuse a reviewer session.
The primary agent performs synthesis and writes reports; no nested synthesizer adapter is installed.
Bootstrap worker and scout delegation is outside this adapter's scope. Although
all seven skills are discoverable, the task allowlist contains only the seven
reviewer types. Stop if bootstrap requires an orchestrator or scout; do not
substitute a reviewer or simulate the missing worker.

Pass absolute paths for the persona, target, standards, and selected sources.
Do not pass parent history, private reasoning, or memory.
Supply prior report paths only when the canonical stage requires them, such as
`zoom_out_report.md` for Step 8 (Intermediate Zoom Out).
Read prior reports only when explicitly supplied and required by the canonical stage.
Do not retrieve unsolicited history, memory, or earlier reviewer findings.
Require all specified reads and actual task completion before synthesis.
Report a missing start, completion, required read, or malformed result as incomplete.
Stop if native delegation is unavailable. Never simulate Goldfish reviewers in the parent conversation.

When brainstorm precedes draft, complete all six brainstorm reviewers first.
Synthesize their findings into `concepts_brief.md` before drafting.
For review, write each completed stage report before starting the next stage.
Before Step 8, verify `zoom_out_report.md` exists in the artifact directory.
Pass its absolute path to the reviewer. Stop if the report is missing.

Reviewers deny every tool except `read`, `glob`, and `grep`.
V1 maps MCP resource reads and resource lists to the `read` permission.
The reviewer `read` rules allow local reads, then deny `mcp:*`.
This denies `mcp:<server>:<uri>` reads and `mcp:<server>:*` resource or template lists.
MCP resource tool names can remain visible. Their resource access is denied at the permission check.
The adapter's external-directory exception covers only the installed bundle.
OpenCode also adds access to its tool-output directory in the resolved agent configuration.
Shell commands, edits, network tools, MCP tools, skills, and delegation remain denied.
The primary agent requests permission for other tools, including writes.
For an external target, move a fixture into the project or review a narrow permission change separately.

Honor `EGM artifact directory: <path>` in the user's prompt or loaded instructions.
Resolve a relative output directory against the project directory. Otherwise retain the canonical output filenames and working-directory default.
Preserve each readiness, section, and stage approval gate. Ask one plain-text question when the native question tool is unavailable.
Wait for the user's answer. Missing tools and elapsed time do not constitute approval.

## Verification limits

OpenCode merges custom, global, project, and managed configuration.
Inspect the effective configuration before a run; later settings can override these permissions.
Use a clean profile and a disposable project for verification.
Inspect inherited instructions, plugins, MCP services, memory, and shared files separately.
Read-only tool configuration is not process or filesystem isolation.
A fresh child session alone does not prove Goldfish isolation.

Run the offline checks:

```sh
pytest tests/unit/test_opencode_adapter.py
pytest tests/unit
```

These tests check installation, resource identity, native configuration, and refusal to overwrite files.
They do not simulate host completion records or prove enforcement by the host.
No live model test runs in ordinary CI.

The scoped OpenCode native probe uses a scripted local model, not a live model.
It checks native child dispatch, one parent marker, and denial of a synthetic
`.env` read. It requires the pinned OpenCode 1.18.29 Linux x64 executable.

```sh
npm ci --ignore-scripts --prefix tests/integration/opencode-ci
python tests/integration/opencode_native_probe.py \
  --source . \
  --opencode tests/integration/opencode-ci/node_modules/opencode-linux-x64/bin/opencode \
  --output /tmp/egm-opencode-probe-new
```

Choose an output path that does not exist. A passing probe does not establish
live model behavior, full workflows, or general reviewer isolation.

On 2026-10-24, OpenCode `1.18.29` accepted the generated configuration through `debug config` and `debug agent egm-style`.
The resolved reviewer toolset enabled only `read`, `glob`, and `grep`.
The `debug skill` command discovered all seven skills from the installed candidate paths.
These commands made no model calls. This result does not prove task execution or runtime permission enforcement.
Separate XDG directories did not prevent discovery of home-directory skills. A clean verification profile must account for those locations too.
This historical note does not identify the tested EGM commit or installed bundle
checksum. Repeat discovery against the pinned candidate before relying on it for
that candidate.

Before a support claim, explicitly authorize and complete these checks:

1. Record the candidate SHA, installed hashes, host version, model identifier, surface, and date.
2. Run brainstorm, draft, and review with an actual human approval pause.
3. Retain native reviewer starts, completions, required reads, and produced artifacts.
4. Probe write denial against a disposable file and inspect the effective child permissions.
5. Place a random marker only in the parent conversation and inspect child context and output.
6. Report installation, workflow, and isolation outcomes separately. Mark missing evidence as unverified.

For OpenCode 1.18.29, the offline verifier checks one exported child session
against its parent JSONL trace. Supply each required absolute POSIX file path:

```sh
opencode export <child-session-id> > child.json
python tests/integration/opencode_trace_verifier.py \
  --parent-trace parent.jsonl --child-export child.json \
  --require /absolute/path/to/agents/zoom_out.md \
  --require /absolute/path/to/target.md \
  --require /absolute/path/to/standard.md
```

The verifier matches native child and parent session identities, the task
completion and time window, reviewer type, and each tool call's message and
session IDs. It requires a new task without `task_id`. It
requires a nonempty, successful file read for every supplied path before the
child's final response. It matches that response to the parent task result.
Missing, conflicting, malformed, or unsupported evidence
fails. Parent JSONL records are split on literal LF, not Unicode separators.
This does not verify every required path unless the caller supplies it. It does
not prove whole-file coverage, transcript authenticity, context isolation, or
that a running workflow stopped on missing evidence. Do not treat a parent
summary or an absent marker as sufficient isolation evidence.

## Interface sources

Reviewed on 2026-10-24. The versioned sources define this adapter's interface:

- [V1 agent configuration](https://github.com/anomalyco/opencode/blob/v1.18.29/packages/web/src/content/docs/agents.mdx)
- [V1 config and merge order](https://github.com/anomalyco/opencode/blob/v1.18.29/packages/web/src/content/docs/config.mdx)
- [V1 skill discovery](https://github.com/anomalyco/opencode/blob/v1.18.29/packages/web/src/content/docs/skills.mdx)
- [V1 command syntax](https://github.com/anomalyco/opencode/blob/v1.18.29/packages/web/src/content/docs/commands.mdx)
- [V1 command preprocessing](https://github.com/anomalyco/opencode/blob/v1.18.29/packages/opencode/src/session/prompt.ts)
- [V1 task implementation](https://github.com/anomalyco/opencode/blob/v1.18.29/packages/opencode/src/tool/task.ts)
- [V1 permission evaluator](https://github.com/anomalyco/opencode/blob/v1.18.29/packages/opencode/src/permission/index.ts)
- [V1 MCP resource permission paths](https://github.com/anomalyco/opencode/blob/v1.18.29/packages/opencode/src/session/tools.ts)
- [Current official agent guide](https://opencode.ai/docs/agents/)
