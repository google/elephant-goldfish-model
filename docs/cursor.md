<!--
Copyright 2026 Google LLC.
SPDX-License-Identifier: Apache-2.0
-->

# Cursor integration (experimental)

This adapter targets Cursor local Agent. Installation, workflow, and isolation
remain unverified. Do not add Cursor to the supported-host table yet.
Keep this status until every gate in the [evidence ledger](#evidence-ledger)
passes for one recorded candidate.
See the [design](designs/additional-harnesses.md) and [issue #145](https://github.com/google/elephant-goldfish-model/issues/145).
Grok Bot is a separate assessment; see [below](#grok-bot-assessment).

## Interface and version

The selected CLI reference is `2026.10.01-e373342`, inspected on 2026-10-24.
Its help lists `--plugin-dir`, `--model`, `--workspace`, and `--output-format`.
Help, version, and the native offline loader probe ran. No model or reviewer ran.
This is an inspected version, not a verified minimum version.
No Cursor version is a verified minimum until the live gates pass.

The first version command stopped at a locked macOS keychain.
The launcher's per-command `AGENT_CLI_CREDENTIAL_STORE=file` setting allowed
help and version inspection. No account configuration changed.

Sources: [plugin reference](https://cursor.com/docs/reference/plugins),
[subagent configuration and context](https://cursor.com/docs/subagents), and
[local plugin installation](https://cursor.com/docs/plugins#test-plugins-locally).
These sources describe host capabilities, not EGM verification results.

## Package layout and placement decision

The native manifest is `.cursor-plugin/plugin.json`. The catalog descriptor
`.cursor-plugin/marketplace.json` points to it. The manifest selects:

| Component | Manifest path | Content |
| --- | --- | --- |
| Skills | `./skills/` | Shared skills, referenced directly |
| Agents | `./.cursor-plugin/agents/` | Glue adapters only: frontmatter and a pointer to the shared persona |
| Rules | `./.cursor-plugin/rules/` | One always-applied routing rule |
| Logo | `.cursor-plugin/assets/icon.svg` | Byte-checked mirror of `assets/icon.svg` |

Decision: keep this placement. The pinned loader accepts it (see
[native loader probe](#native-loader-probe)), so neither fallback applies:
no symlinks and no generated mirror of skill or persona text.

- All paths are relative, contain no `..`, and stay inside the plugin
  directory, as the plugin reference requires.
- A specified manifest field replaces default folder discovery. The explicit
  `agents` path therefore excludes the raw shared personas in `agents/`,
  which lack Cursor read-only settings. Registering both would also duplicate
  reviewer names.
- Adapters do not copy persona text. Each one tells the reviewer to read
  `EGM_ROOT/agents/<persona>.md` and follow it.
- The logo is the only copied file. The documented install copy omits the root
  `assets/` folder, so a byte-equality test keeps the mirror from drifting.
  It is a listing asset, not skill or persona content.

Offline tests enforce this decision: an inventory check of `.cursor-plugin/`,
SHA-256 and 10-word overlap checks against `skills/`, `agents/`, and
`resources/`, and path-containment checks on both manifests.

The expected skills and reviewers are derived from the tree: every
`skills/*/SKILL.md`, and every persona in `agents/` except the synthesizer
and bootstrap orchestrator roles. A new persona fails the offline suite until
it has a Cursor adapter. Counts are not written in this guide.

## Read-only fields per surface

Each reviewer declares `readonly: true`, `permissionMode: readonly`,
`model: inherit`, and `is_background: false`. Keep both read-only fields.
They are read by different ingestion surfaces, and evidence from one surface
does not justify removing the other's field.

| Surface | Field it reads | Source and version | Evidence | Result |
| --- | --- | --- | --- | --- |
| Plugin loader (`.cursor-plugin/plugin.json` agents) | `permissionMode` | CLI `2026.10.01-e373342` bundle, pinned by SHA-256 | Native probe and negative control | Registration: see [native loader probe](#native-loader-probe). Runtime enforcement: unverified |
| Custom subagents (`.cursor/agents/`, `~/.cursor/agents/`) | `readonly` | Public [subagent docs](https://cursor.com/docs/subagents), read 2026-11-18 | Documentation only | Not probed; unverified |

The subagent docs say `readonly: true` restricts file edits and state-changing
shell commands. Neither the subagent docs nor the plugin reference document
`permissionMode`; it is a private loader field for the pinned version.
Registration is discovery evidence. It is not runtime enforcement.

## Install a candidate

Use a clean Cursor profile with no other EGM installation.
Local imports must be permitted by the host policy.
Do not disable an organization policy or overwrite an existing package.
Cursor also loads subagents from `.claude/agents/`, `.codex/agents/`, and their
user-level folders. Confirm no EGM copies exist there.

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
4. Record checksums as described in [runbook step 1](#runbook-step-1-installation).
5. Reload Cursor and inspect the plugin in Customize.
6. Confirm every shared skill, every EGM reviewer, and the EGM runtime rule.
   Compare with `ls skills/*/SKILL.md` and `ls .cursor-plugin/agents/` in the
   checkout.

The copy retains all shared runtime directories and their relative layout.
It excludes the portable root manifest to select the Cursor format explicitly.
It contains no symlink to an external checkout.
The shared source files remain unchanged.
This copy is packaging, not content duplication.

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

If the Task tool or a registered read-only reviewer type is unavailable, the
rule stops before dispatch. The stop message names what is missing, the remedy
(enable the package, reload Cursor, confirm the reviewers in Customize), and
the stages and reports completed and verified before the stop.

The parent writes artifacts to the user's working directory.
Honor `EGM artifact directory: <path>` in the user's prompt or instruction file.
Resolve a relative override against the working directory and create it if needed.
Never write reports into the installed plugin. Preserve canonical approval pauses.

## Known limitations

- `egm-lite` Goldfish reviews stop. Its reviewer is defined by the parent's
  prompt, not a registered read-only type, and a generic child is not
  read-only. The rule routes it to that skill's stop path.
- The synthesizer and bootstrap orchestrator have no Cursor adapter.
- Subagents inherit the parent's MCP tools. Read-only mode is not documented to
  restrict MCP, so use a profile with no MCP servers for every live run.
- Read-only mode restricts writes. It is not a filesystem boundary: reviewers
  can read any accessible file.
- The native loader probe is pinned for macOS arm64 and Linux arm64 only.
  Other platforms skip with an audit message.
- No parser for parent Task records is supplied. Completion matching in
  [runbook step 5](#runbook-step-5-completion-records) is a manual inspection.
- The private store schema and loader export are version-specific.

## Verification gates

Offline checks run with `pytest tests/unit/test_cursor.py` or `pytest tests/unit`.
They check metadata, manifest path containment, the zero-duplication inventory,
read-only registration settings for every adapter, and a relocated package with
spaces and Unicode in its path. The optional native check skips without a local
bundle. The read-evidence and canary utility has its own unit tests in
`tests/unit/test_cursor_child_reads.py`.

### Native loader probe

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

The probe asserts that the relocated package registers exactly the derived
skills, exactly the derived reviewers with `permissionMode: readonly` and
`model: inherit`, and one active rule. A negative control removes one field
from every adapter in a scratch copy:

- With `readonly: true` alone, no reviewer registers as read-only.
- With `permissionMode: readonly` alone, every reviewer registers as read-only.

This shows which field the plugin loader honors. It does not show what the
`.cursor/agents` surface reads. These are native parsing results, not
interactive installation or runtime evidence.

Recorded probe run, 2026-11-18:

| Item | Observed |
| --- | --- |
| Environment | Docker `linux/arm64` (`aarch64`) under emulation on an x86_64 host, Python 3.12 |
| Archive SHA-256 | `785c5f6b…245eb5`, matching the pin |
| Bundle SHA-256 | `90ec2382…239c75cd2`, matching the Linux arm64 pin |
| Tree | Branch work based on `70406c4`, before its final commit |
| Skills registered | `egm-bootstrap`, `egm-brainstorm`, `egm-draft`, `egm-drift-report`, `egm-lite`, `egm-resolve`, `egm-review`, `egm-review-loop` |
| Agents registered | `egm-codebase-details`, `egm-comprehension`, `egm-design`, `egm-implementation-readiness`, `egm-inventive-catalyst`, `egm-structural`, `egm-style`, `egm-zoom-out` |
| Candidate adapters | Every agent `permissionMode: readonly`, `model: inherit`; one rule with `alwaysApply: true` |
| `readonly: true` alone | Every agent `permissionMode: default` |
| `permissionMode: readonly` alone | Every agent `permissionMode: readonly` |
| Native tests | `pytest -k native`: passed |

This run is registration evidence for that tree, not for a recorded candidate
commit. Repeat it against the candidate before relying on it, and record the
result in the [evidence ledger](#evidence-ledger). An earlier note recorded
the same `readonly`-alone result before `permissionMode` was added.

## Live verification runbook

You run every step. Each step marked
"Model usage: requires your explicit authorization" starts a Cursor agent and
can incur cost. Do not start it until you have decided to spend that usage.
Steps without that mark inspect files only.

Use a disposable workspace, a clean Cursor profile, no MCP servers, no
memories, and no user rules. Fix the host and model for the whole run: select
the model explicitly and record its identifier from the task records, not from
the picker label. Keep stores, transcripts, and evidence private.

### Runbook step 0: Evidence directory

Create an evidence folder outside both the plugin and the workspace:

```sh
export EGM_EVIDENCE="$HOME/egm-cursor-evidence/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$EGM_EVIDENCE"
agent --version > "$EGM_EVIDENCE/cursor-version.txt"
```

`agent --version` prints the version without starting a model session.
If it stops at a locked keychain, prefix it with
`AGENT_CLI_CREDENTIAL_STORE=file` for that command only.
Expected: `2026.10.01-e373342`. A different version is a new, unaudited
candidate; record it and expect the native probe to refuse it.

### Runbook step 1: Installation

Model usage: none.

1. Install as described in [Install a candidate](#install-a-candidate).
2. Record package checksums from the checkout:

   ```sh
   if command -v sha256sum >/dev/null; then sha="sha256sum"; else sha="shasum -a 256"; fi
   (cd "$egm_candidate" && find . -type f ! -name .egm-source-sha -print0 |
     LC_ALL=C sort -z | xargs -0 $sha) > "$EGM_EVIDENCE/package.sha256"
   $sha "$EGM_EVIDENCE/package.sha256" > "$EGM_EVIDENCE/package-identity.txt"
   (cd "$(git rev-parse --show-toplevel)" && $sha -c "$EGM_EVIDENCE/package.sha256")
   ```

   Expected: every line reports `OK`, so the installed bytes match the
   candidate commit. The manifest must list files under `agents/` and
   `resources/`. The identity is the SHA-256 of the checksum manifest.
3. Reload Cursor. In Customize, confirm the EGM plugin, every shared skill,
   every EGM reviewer, and the runtime rule. Save a screenshot.

Installation also needs actual reads of installed files, which come from
[runbook step 3](#runbook-step-3-read-evidence).

### Runbook step 2: Isolation canary

Model usage: requires your explicit authorization.

1. Generate a fresh marker for this run. Never write it to a file, rule,
   memory, or instruction file:

   ```sh
   python3 -c "import secrets; print('EGM-CANARY-' + secrets.token_hex(16))"
   ```

2. Create a disposable fixture document in the workspace with no marker.
3. In a new Cursor chat, send one message that contains the marker, then ask
   for one Goldfish review of the fixture:

   ```text
   Parent-only marker: <marker>. Keep it in this conversation only.
   EGM_ROOT: <absolute package path>
   Dispatch one egm-structural reviewer Task for <absolute fixture path>.
   Pass only the target, EGM_ROOT, and persona path. Report its findings.
   ```

4. After the child stops, find its store by the child ID in the matched parent
   Task completion. Make a closed snapshot with SQLite's backup API:

   ```sh
   python3 -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close()" \
     /absolute/path/to/child/store.db "$EGM_EVIDENCE/child-structural.db"
   python3 tests/integration/cursor_child_reads.py "$EGM_EVIDENCE/child-structural.db" \
     --required "$egm_candidate/agents/structural.md" --absent <marker>
   ```

5. Save the child's returned text from the parent Task completion as
   `child-structural-output.txt`. Then run
   `grep -c <marker> "$EGM_EVIDENCE/child-structural-output.txt"`.

Pass requires all of these:

- The utility exits 0 and reports `"status": "absent"`.
- `grep` prints `0` on the child output.

Exit 1 with `found` fails isolation. Exit 3 is inconclusive and leaves the
gate unverified. Never establish isolation by asking the reviewer.

Assess each other context channel in a separate run, each with its own marker.
Put these markers only in the channel under test, never with the parent marker:

| Channel | Probe | Record |
| --- | --- | --- |
| Injected rules | A disposable `.cursor/rules/canary.mdc` with `alwaysApply: true` | Marker found or absent in child store |
| Repository instructions | A disposable `AGENTS.md` in the workspace | Marker found or absent in child store |
| Memory | Confirm memories are off and empty; record the setting | Setting and screenshot |
| MCP | Confirm no MCP servers are configured; record the list | Setting and screenshot |
| Shared files | A marker file the task does not name | Whether the child read it (`ReadFile` records) |

These channel probes incur the same model usage as step 2 and also require
your authorization. A found channel marker is a context-channel result. Record
it separately from parent-turn isolation, as for other hosts in the
[harness guide](harnesses.md#support-status--contributing-other-harnesses).

### Runbook step 3: Read evidence

Model usage: none. This uses child stores from steps 2, 4, and 6.

For every child, run the utility on its closed snapshot with each required
path: the persona, and each standard the stage passes. The command exits
nonzero if a required path lacks a matched nonempty successful `ReadFile`
record. The reviewer's own claim that it read a file is not evidence.

### Runbook step 4: Read-only enforcement

Model usage: requires your explicit authorization.

1. Create a disposable fixture and record its hash:

   ```sh
   printf 'egm read-only fixture\n' > /absolute/workspace/readonly-fixture.txt
   $sha /absolute/workspace/readonly-fixture.txt > "$EGM_EVIDENCE/fixture-before.sha256"
   ```

2. Ask the parent to dispatch one EGM reviewer Task that is told to append a
   line to that fixture with its edit tool, then with a shell command.
3. Record each attempt's tool result from the child store, then check:

   ```sh
   $sha -c "$EGM_EVIDENCE/fixture-before.sha256"
   ```

Pass requires `OK`, no successful write or shell result in the child store,
and no new or changed workspace files (`git status --porcelain` in a git
workspace). Record edit-tool and shell results separately.

### Runbook step 5: Completion records

Model usage: none. This uses the parent store from steps 2, 4, and 6.

Make a closed snapshot of the parent store. For every reviewer dispatched,
find its Task call and its completion record, and match the child ID to a
child store. Record the tool name and record types you observed, since the
schema is private. A missing start or completion leaves the gate unverified.
The parent's summary is not evidence.
No complete Cursor workflow trace parser is supplied. Before accepting one, test
missing starts, missing completions, malformed records, and Unicode line
separators. Split JSONL on literal LF only.
Existing Claude and Codex trace tests do not validate Cursor evidence.

### Runbook step 6: End to end

Model usage: requires your explicit authorization. This is the largest run.

In a disposable workspace, at the recorded host and model versions:

1. Run `/egm-brainstorm` for a small feature. Expected: the readiness
   checkpoint and handoff gate wait for your choice, and `concepts_brief.md`
   is written to the workspace or the artifact-directory override.
2. Run `/egm-draft`. Expected: each section approval gate waits, and
   `design_draft.md` is written there.
3. Run `/egm-review` on the draft in interactive mode. Expected: each stage
   checkpoint waits, stage reports such as `zoom_out_report.md`,
   `comprehension_report.md`, and `critic_report.md` appear before the next
   stage's Task starts, and `consolidated_review_report.md` is written last.
4. Repeat step 1 with `EGM artifact directory: <relative path>` in the prompt.
   Expected: artifacts move to that folder.
5. Confirm nothing was written under the installed package. Both commands
   must pass, and the second must print nothing:

   ```sh
   (cd "$(git rev-parse --show-toplevel)" && $sha -c "$EGM_EVIDENCE/package.sha256")
   find "$egm_candidate" -type f -newer "$EGM_EVIDENCE/package.sha256"
   ```

Record each pause you answered and the file each stage wrote. Apply steps 3
and 5 to every reviewer from this run.

## Evidence ledger

Record unknown values as `unverified`. Copy this ledger into the PR or issue.

| Field | Value |
| --- | --- |
| Candidate commit | unverified |
| Package path | unverified |
| Package checksum manifest | unverified (`package.sha256` and its SHA-256) |
| Cursor version | unverified (inspected: `2026.10.01-e373342`) |
| Surface | Cursor local Agent |
| Model identifier | unverified |
| Run date | unverified |

| Gate | Required evidence | Current result |
| --- | --- | --- |
| Installation | Checksummed package, Customize discovery, and actual reads of installed personas and standards | Unverified; offline native discovery only |
| Workflow | Brainstorm, draft, and review artifacts, stage order, and observed human approval pauses | Unverified |
| Isolation | Parent canary absent, required reads, read-only denial, and every reviewer start and completion | Unverified |

A gate passes only when every item in its row has evidence for the same
candidate. Record context-channel results beside the Isolation gate.

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
