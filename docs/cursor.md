<!--
Copyright 2026 Google LLC.
SPDX-License-Identifier: Apache-2.0
-->

# Cursor integration (experimental)

This adapter targets Cursor local Agent. Installation, workflow, and isolation
remain unverified. Do not add Cursor to the supported-host table yet.
See the [design](designs/additional-harnesses.md) and [issue #145](https://github.com/google/elephant-goldfish-model/issues/145).

## Interface and version

The selected CLI reference is `2026.10.01-e373342`, inspected on 2026-10-24.
Its help lists `--plugin-dir`, `--model`, `--workspace`, and `--output-format`.
Help, version, and the native offline loader probe ran. No model or reviewer ran.
This is an inspected version, not a verified minimum version.

The first version command stopped at a locked macOS keychain.
The launcher's per-command `AGENT_CLI_CREDENTIAL_STORE=file` setting allowed
help and version inspection. No account configuration changed.

The native manifest is `.cursor-plugin/plugin.json`. It selects shared
`skills/`, Cursor adapters in `.cursor-plugin/agents/`, and the Cursor rule in
`.cursor-plugin/rules/`. The explicit agent path excludes raw shared personas.
Each reviewer declares `readonly: true`, `permissionMode: readonly`,
`model: inherit`, and `is_background: false`.
The selected CLI's plugin loader reads `permissionMode`, not `readonly`.
The documented `readonly` field remains for the local Agent interface.
The native loader probe confirms all seven reviewers register as read-only.
This does not prove runtime enforcement or foreground behavior.
Select a model explicitly for a future live run and
record its actual identifier from the task records.

Sources: [plugin reference](https://cursor.com/docs/reference/plugins),
[subagent configuration and context](https://cursor.com/docs/subagents), and
[local plugin installation](https://cursor.com/docs/plugins#test-plugins-locally).
These sources describe host capabilities, not EGM verification results.

## Install a candidate

Use a clean Cursor profile with no other EGM installation.
Local imports must be permitted by the host policy.
Do not disable an organization policy or overwrite an existing package.

1. Check out the candidate commit in a clean EGM checkout.
2. Run these commands from that checkout:

   ```sh
   git diff --exit-code HEAD
   egm_candidate="$HOME/.cursor/plugins/local/egm"
   mkdir -p "$(dirname "$egm_candidate")"
   mkdir "$egm_candidate" && {
     cp -R .cursor-plugin skills agents resources docs LICENSE "$egm_candidate/" &&
     git rev-parse HEAD > "$egm_candidate/.egm-source-sha"
   }
   ```

3. Stop if a command fails. Inspect any partial copy before retrying.
4. Reload Cursor and inspect the plugin in Customize.
5. Confirm seven skills, seven EGM reviewers, and the EGM runtime rule.
6. Record the absolute package path and installed file checksums.

The copy retains all shared runtime directories and their relative layout.
It excludes the portable root manifest to select the Cursor format explicitly.
It contains no symlink to an external checkout.
The shared source files remain unchanged.

The inspected CLI also accepts a temporary candidate through
`agent --plugin-dir /absolute/path/to/cursor-package`.
That command starts an agent and can incur model usage. Run it only after
explicit authorization for live tests. Do not use force or automatic MCP approval.

## Invoke the workflow

Before the first skill, provide the installed root to the local Agent:

```text
EGM_ROOT: /absolute/path/to/cursor-package
Read /absolute/path/to/cursor-package/docs/cursor.md.
Run /egm-brainstorm for the requested feature.
```

Select the installed EGM skill from Cursor's slash menu.
If a skill is not exposed, read its absolute `skills/<directory>/SKILL.md`
and follow it in the parent context. Do not invent a slash-command namespace.
Use the same process for `egm-draft`, `egm-review`, and workflow subskills.
The adapter rule must be active before execution.

Resolve `agents/`, `resources/`, and `docs/` against the selected package root.
Resolve a skill's `references/` against that skill's directory.
Do not assume Markdown expands `${CURSOR_PLUGIN_ROOT}` or `${CLAUDE_PLUGIN_ROOT}`.
Host-specific instructions for Claude and Codex do not select the Cursor runtime.

Keep the synthesizer's orchestration in the parent and dispatch reviewers directly.
Read `agents/synthesizer.md` for its canonical synthesis instructions when needed.
Do not create an unrestricted synthesizer child. Bootstrap child delegation is
outside this experimental adapter; stop if the requested operation requires it.

For each review, start a new native Task of the registered persona type.
Pass the absolute package root, persona, target, scope, and required standards.
Pass only explicit Goldfish context, without parent deliberation or history.
Include previous reports only when the canonical stage explicitly requires them.
Collect each completion before the next stage. Never reuse a reviewer context.
Write each completed stage report before dispatching the next stage.
For Step 8, pass the absolute path of the existing `zoom_out_report.md` to the
reviewer. Stop if that report is missing.
If dispatch, required reads, or completion fails, report an incomplete stage and stop.
Do not replace native reviewers with an in-thread simulation.

The parent writes artifacts to the user's working directory.
Honor `EGM artifact directory: <path>` in the user's prompt or instruction file.
Resolve a relative override against the working directory and create it if needed.
Never write reports into the installed plugin. Preserve canonical approval pauses.

## Verification gates

Offline checks run with `pytest tests/unit/test_cursor.py` or `pytest tests/unit`.
They check metadata, native configuration, and a relocated package with spaces
and Unicode in its path. The optional native check skips without a local bundle.

Run the native loader probe against the inspected arm64 CLI bundle on macOS or Linux:

```sh
EGM_CURSOR_BUNDLE="$HOME/.local/share/cursor-agent/versions/2026.10.01-e373342/index.js" \
  pytest tests/unit/test_cursor.py
```

The probe pins Cursor CLI `2026.10.01-e373342` by platform and bundle SHA-256:

- macOS arm64: `f6bd8dece34b56431ee74f1ac827e032d054381085e7da7088e85abdd1008330`.
- Linux arm64: `90ec23826cd3089232b0b243b8954ac72fab0454dd86d7d71ddae29d39c75cd2`.

The Linux bundle comes from Cursor's [versioned package](https://downloads.cursor.com/lab/2026.10.01-e373342/linux/arm64/agent-cli-package.tar.gz).
Its downloaded archive SHA-256 was `785c5f6bf2a60eb1121e27ed8c14f5ee07ed1b5b6692324f2d9a997238245eb5`.
These hashes identify the inspected files. They are not vendor signatures.
It invokes the installed plugin loader without the CLI entry point.
It blocks network connections and subprocess launches within the probe.
It does not patch the installed CLI or start a model session.
The private loader export is version-specific. Re-audit it before changing the pin.

The probe discovers seven skills, seven read-only reviewer registrations, and
one active rule in the relocated package. Initially, `readonly: true` alone
registered default permissions. The added `permissionMode` field corrects that result.
These are native parsing results, not interactive installation or runtime evidence.
This historical note does not identify the tested EGM commit or installed package
checksum. Repeat discovery against the pinned candidate before relying on it for
that candidate.

Before a live run, obtain explicit approval for model usage.
Use a clean workspace and profile without unrelated MCP services or memory.
Record the candidate SHA, package checksums, host version, surface, model, and date.
Keep these results separate:

| Gate | Required evidence | Current result |
| --- | --- | --- |
| Installation | Interactive discovery and actual reads of installed personas, standards, and guides | Unverified; offline native discovery passed |
| Workflow | Brainstorm, draft, review, artifacts, and an actual human approval pause | Unverified |
| Isolation | Fresh child records, required reads, read-only denial, and every reviewer completion | Unverified |

For isolation, place a random marker only in the parent conversation.
Inspect the child input and tool records as well as its answer.
Probe write denial against a disposable fixture and verify its bytes remain unchanged.
The native read-only mode restricts writes; it is not a filesystem boundary.
The prompt also forbids shell and MCP use, but these are not proven tool allowlists.
Assess injected rules, repository instructions, memory, MCP access, and shared files
separately. A fresh task does not remove those possible sources of information.

Record native reviewer starts and completions, not only the parent's summary.
Missing records leave the corresponding gate unverified.
For CLI `2026.10.01-e373342`, `tests/integration/cursor_child_reads.py` checks
one child's SQLite store for matching `ReadFile` calls and successful results:

```sh
python tests/integration/cursor_child_reads.py /absolute/path/to/child/store.db \
  --required /absolute/path/to/persona.md
```

Select the store using the child ID from its matched parent Task completion.
After the child stops, use SQLite's backup API to create a closed snapshot.
The command rejects a snapshot with a WAL file or a changing main file.
The command exits nonzero if a required path lacks a matched nonempty success.
The store and output may contain private paths. Keep them private.
The command checks reads only. It does not validate dispatch, approvals, stage
order, isolation, or artifacts. The store schema is private and version-specific.
It counts opaque binary blobs but cannot interpret their contents.
No complete Cursor workflow trace parser is supplied. Before accepting one, test
missing starts, missing completions, malformed records, and Unicode line
separators. Split JSONL on literal LF only.
Existing Claude and Codex trace tests do not validate Cursor evidence.

## Grok Bot assessment

Grok Bot remains a separate, unverified surface. No Grok Bot adapter is included.
Its [work guide](https://cursor.com/docs/grok-bot/work) describes retained memory
and a shared computer. These can expose previous findings to another reviewer.
Local Cursor results cannot establish Grok Bot compatibility.

| Requirement | Assessment |
| --- | --- |
| Full package import and resource reads | Not tested |
| Fresh reviewer context | Not tested; retained memory requires a separate probe |
| Read-only enforcement | Not tested |
| Native starts and completions | Not tested |
| Human approval pauses | Not tested |
| Prior findings in memory and shared files | Not tested; inspect both independently |

Propose any Grok Bot implementation separately after these checks.

## Remove the candidate

Disable the local EGM plugin in Cursor.
Remove only the candidate folder that you created, then reload Cursor.
Retain workspace artifacts and verification evidence.
