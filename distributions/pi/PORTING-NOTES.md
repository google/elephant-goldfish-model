# Porting notes: Pi distribution

Status: candidate. Installation path documented, native workflow evidence
missing. Pi is not a supported harness yet; see
[Harnesses](https://github.com/google/elephant-goldfish-model/blob/main/docs/harnesses.md#support-status--contributing-other-harnesses).

This file records why the Pi package looks the way it does. It is not runtime
content: Pi never loads it, and the offline check ignores it.

## What this package is

`distributions/pi/` is a Pi package: a directory with a `package.json`
`pi` manifest, the seven EGM skills, the nine canonical reviewer personas,
the five document standards, and the Pi agent definitions that turn those
personas into host-enforced read-only reviewers.

EGM's canonical text stays at the repository root. This package carries
byte-identical copies of `skills/`, `agents/`, `resources/`, and `docs/`
because Pi reads package resources from inside the package root. Replace the
copies by running `python3 scripts/check_pi_distribution.py --write`; the
script refuses to rewrite the hand-written Pi files.

## Contract sources

Read before writing any of this, in this order:

1. [Multi-harness support](../../docs/designs/multi_harness_support.md): reuse the
   shared bundle, add a thin host adapter, copy canonical metadata, verify
   parity, use host-enforced read-only reviewer permissions, and claim no
   support without native evidence.
2. [Harnesses](../../docs/harnesses.md): where install steps, manifest mapping,
   and delegation mechanics for a new harness belong.
3. `scripts/pack_plugin.py` and `plugin.json`: how the Claude and OpenAI
   runtimes are built, and which metadata is canonical.
4. `distributions/claude/.claude-plugin/agents/*.md`: the two-layer adapter
   pattern. A thin adapter declares host tool restrictions and context rules
   and points at the canonical persona in `agents/`.
5. `TESTING.md`: offline unit tests, plus a native record for any harness
   claimed as supported.

## What Pi provides, and what it does not

Cited against Pi's documentation as shipped in `@earendil-works/pi-coding-agent`
1.4.0 (`docs/packages.md`, `docs/skills.md`, `docs/extensions.md`,
`docs/cli.md`, `docs/prompt-templates.md`, `docs/settings.md`):

| Pi behaviour | Source | Consequence here |
| --- | --- | --- |
| A package is a directory that discovers `skills/`, `prompts/`, `extensions/`, and `themes/`, and may declare explicit paths under the `pi` key of `package.json` | `packages.md`, "Create a package" | `package.json` declares `pi.skills` explicitly; no extension, prompt template, or theme is needed |
| `pi install ./local-package` loads from the resolved path without copying | `packages.md`, "Choose a source" | The checked-in folder is installed in place; no ZIP is built |
| Skills are `SKILL.md` directories; frontmatter follows the Agent Skills specification and supports `disable-model-invocation` | `skills.md`, "Create a skill" and "Write portable frontmatter" | EGM's existing skills load unchanged; they stay out of automatic discovery and are invoked as `/skill:egm-<name>` |
| Pi tells the model where a skill lives so it can resolve files relative to the skill directory | `skills.md`, "Create a skill" | Root resolution is derived from the discovered `SKILL.md` path (the rule Codex already uses); Pi has no `${CLAUDE_PLUGIN_ROOT}` substitution |
| Built-in tool names are `read`, `bash`, `powershell`, `edit`, `write`, `grep`, `find`, `ls` | `cli.md`, "Tool options" | Claude's `Read`/`Grep`/`Glob` map to `read`/`grep`/`find`, plus `ls` |
| `--tools <list>` selects the tools declared to the model | `cli.md`, "Tool options" | The subagent extension passes an agent definition's `tools` list to the child, which is host-enforced rather than prompted |
| Tools run with the permissions of the Pi process; project trust does not sandbox tool calls | `index.md`, "Work safely"; `how-pi-works.md`, "Trust and permissions" | Read-only reviewers are enforced by removing mutating and shell tools, which is not a filesystem sandbox |
| Pi ships no subagent tool; extensions register tools, and one can spawn a child session | `extensions.md`, "Tools"; `how-pi-works.md` | Goldfish reviews need a subagent extension. Without one the review skills stop, as the shared text requires |
| Context files (`AGENTS.md`, `CLAUDE.md`) load from the agent directory and the working directory, without project trust | `configuration.md`, "Context files" | A child session in the same working directory still sees project instructions |

## Reviewer delegation, precisely

Pi core ships no subagent tool, so Goldfish reviews require a third-party Pi
subagent extension — EGM has checked only Gentle Agents in `gentle-pi` 4.5.1,
tests no other, and the review skills stop when no such tool is present. EGM
does not test, pin, or license-review that package, and the extension, not Pi,
owns everything below. The details are recorded as an inspection point, not as
Pi behaviour: a different extension can name its tool, its definition format,
and its directories differently, so read the schema the session exposes.

The working example is the `subagent_*` tool family in `gentle-pi` 4.5.1, whose
source was read at `~/.pi/agent/npm/node_modules/gentle-pi`:

* `subagent_run` takes `agent`, `task`, and optionally `label`, `context`, and
  `mode` (`extensions/gentle-agents.ts`, and `docs/gentle-shell.md` in that
  package).
* Agent definitions are Markdown files with `name`, `description`, and `tools`
  frontmatter, discovered from `<agent-dir>/agents/`, `<agent-dir>/subagents/`,
  `.pi/agents/`, and `.pi/subagents/` (`lib/agents-config.ts`,
  `discoverAgents` and `agentDirectories`).
* A child is a new `pi --mode rpc --session-dir <fresh>` process with the
  definition body appended to its system prompt and its `tools` list passed as
  `--tools` (`lib/agents-runner.ts`, `childArguments`). A new session
  directory means no parent conversation history.

So the Pi adapters are agent definitions, not Pi package resources: the package
ships them under `subagents/`, and installation copies or links them into the
directory that extension reads (`~/.pi/agent/agents/` in 4.5.1).

## Per-file decisions

| File | Decision | Why |
| --- | --- | --- |
| `package.json` | New Pi manifest | Pi packages identify themselves here; metadata is copied field for field from root `plugin.json` |
| `subagents/*.md` | Nine thin adapter definitions | Same two-layer split as `.claude-plugin/agents/`, which exists so Claude tool names never enter shared persona frontmatter |
| `agents/*.md`, `skills/**`, `resources/**`, `docs/*.md`, `LICENSE` | Copies of canonical files | Pi resolves them inside the package root; copying is what `distributions/claude` already does |
| `README.md` | Hand-written package README | The canonical README installs EGM into a harness and uses skill and page artwork that this package does not carry; a copy would send a reader to paths that are not there |

## Per-persona decision

| Persona | Adapter | Why |
| --- | --- | --- |
| `egm-comprehension` | Needed | Read-only tool list differs from the host default |
| `egm-design` (`design_critic.md`) | Needed | Read-only tool list differs from the host default |
| `egm-structural` | Needed | Read-only tool list differs from the host default |
| `egm-style` | Needed | Read-only tool list differs from the host default |
| `egm-zoom-out` | Needed | Read-only tool list differs from the host default |
| `egm-implementation-readiness` | Needed | Read-only tool list differs from the host default |
| `egm-codebase-details` | Needed | Read-only tool list differs from the host default |
| `egm-synthesizer` | Needed | Writes reports and cannot delegate, so it must be told to hand dispatch back to the main context |
| `egm-bootstrap-orchestrator` | Needed | Needs shell and edit tools and must run discovery workers inline instead of nesting them |

No canonical persona was edited. `agents/*.md` at the repository root is
unchanged; every difference lives in `subagents/`.

## Per-skill decision

| Skill | Decision | Why |
| --- | --- | --- |
| `egm-brainstorm` | Copied, unchanged | The skill text names Claude and Codex only; the Pi preamble lives in `docs/harnesses.md` |
| `egm-draft` | Copied, unchanged | Same reason |
| `egm-review` | Copied, unchanged | Same reason |
| `egm-review-loop` | Copied, unchanged | Same reason |
| `egm-resolve` | Copied, unchanged | Same reason |
| `egm-drift-report` | Copied, unchanged | Same reason |
| `egm-bootstrap` | Copied, unchanged | Same reason |

## Known limits

1. **No native subagent tool.** Pi core ships no subagent tool, so Goldfish
   reviews require a third-party Pi subagent extension — EGM has checked only
   Gentle Agents in `gentle-pi` 4.5.1, tests no other, and the review skills stop
   when no such tool is present. EGM does not test, pin, or license-review that
   package, so Pi support is conditional on it.
2. **Project context reaches reviewer children.** A child session is fresh but
   still loads `AGENTS.md` and `CLAUDE.md` from the working directory. Pi has no
   per-agent equivalent of Claude's `omitClaudeMd`. This matches the posture
   already documented for Codex: fresh conversation is not filesystem,
   instruction, or memory isolation.
3. **No reviewer nesting.** Children cannot be relied on to spawn further
   children, so a Pi synthesizer child cannot dispatch reviewers. The main
   context dispatches them, which the shared skills already allow for harnesses
   without nesting.
4. **The shared skill preamble never names Pi.** All seven skills open with a
   line that points Claude, Codex, and ChatGPT Work at their guides. A Pi
   session has no equivalent in-skill pointer, so the harness guide says to read
   its Pi section before the first EGM skill. Adding one sentence to each
   `skills/*/SKILL.md` needs `skills/` write access, which this change did not
   have.
5. **No native evidence.** No Pi installation, workflow, isolation, or
   permission probe was run for this change. Offline checks cannot substitute
   for those probes, so the harness guide keeps Pi out of the supported list.
6. **The Claude runtime needs one regeneration.** `distributions/claude/` is
   generated output that mirrors the shared docs, and `README.md` and
   `docs/harnesses.md` are part of it. Editing either file leaves
   `test_published_claude_runtime_is_current` failing until
   `python3 scripts/pack_plugin.py --target claude` output replaces the two
   stale copies. That folder was outside this change's edit surface, so the
   copies were left alone; see below.

## The one thing that could not be made to work

Two items, in order of how much they block a maintainer.

1. **Reviewer context isolation is only partially enforceable on Pi.** A child
   session starts with no parent conversation, but it loads the working
   directory's context files. EGM's Goldfish rule is "fresh context, no
   conversation history", which Pi satisfies; Claude's stricter `omitClaudeMd`
   posture has no Pi equivalent. A maintainer must decide whether that weaker
   posture is enough for a supported claim, or whether Pi reviews must run from
   a directory without EGM context files.
2. **The published Claude runtime cannot be regenerated from here.** Editing
   `README.md` and `docs/harnesses.md` invalidates the two matching files in
   `distributions/claude/`. Regenerating them is mechanical (two files, byte
   for byte the builder's output) but the folder is outside this change's edit
   surface. Until a maintainer runs the rebuild, the offline suite reports that
   one failure and nothing else.

## Verification state

* Offline: `python3 scripts/check_pi_distribution.py --check` compares every
  copied byte, checks metadata parity with `plugin.json`, and confirms the seven
  skills, nine personas, and five standards are present. `pytest tests/unit`
  covers link integrity, Markdown tables, and manifest metadata.
* Not run: any native Pi install, skill load, reviewer spawn, or workflow. See
  `TESTING.md` for the evidence a supported-harness claim needs.
* The freshness check is a script, not a unit test, because `tests/` was
  outside this change's edit surface. Promoting it into
  `tests/unit/test_packaging.py` is a one-function follow-up.

## Follow-ups a maintainer may want

1. Rebuild `distributions/claude/` after any edit to `README.md` or
   `docs/harnesses.md`; the builder compares every path and byte.
2. Add a Pi sentence to each `skills/*/SKILL.md` preamble, so a Pi session is
   pointed at the harness guide the way Claude and Codex sessions are.
3. Promote `scripts/check_pi_distribution.py` into `tests/unit` (or generate
   `distributions/pi/` from the pack script) so drift fails CI instead of
   depending on a manual run.
4. Consider a root `package.json` with the `pi` manifest, so Pi installs the
   repository itself and the copied tree disappears.
5. Run a native Pi probe and record it in `TESTING.md` before moving Pi out of
   the unverified group in `docs/harnesses.md`.

## First real run

2026-11-02. One `egm-comprehension` reviewer ran in REVIEW mode against a
396-line engineering design document, from a bare `git init` project, with
`PI_CODING_AGENT_DIR` pointed at a throwaway config directory instead of
`~/.pi/agent`. The nine adapter definitions were copied into that directory's
`agents/`, which is the first directory `agentDirectories` returns; the other
three it discovers (`subagents/`, `.pi/agents/`, `.pi/subagents/`) were left
absent, and `subagent_list_agents` resolved every persona from the first one.

Exact invocation (the `env -u` prefix matters: a shell that already carries
`GENTLE_PI_AGENTS_CHILD=1` makes `gentle-agents.ts` take its child branch and
register no subagent tools at all):

```bash
env -u GENTLE_PI_AGENTS_CHILD -u GENTLE_PI_AGENTS_OWNED_IPC \
    -u GENTLE_PI_AGENTS_REQUESTED_TOOLS \
    PI_CODING_AGENT_DIR=<sandbox>/config \
    pi -p --no-session "<prompt: call subagent_run with agent=egm-comprehension, \
the REVIEW-mode task, then relay the result verbatim>"
```

Isolation was complete for configuration and instructions: both packages
registered from the sandbox, the child session opened in the sandbox project
with no `AGENTS.md` or `CLAUDE.md` anywhere above it, and nothing was written
under `~/.pi/agent`. Skill discovery is the exception — it still reads
`~/.agents/skills`, so parent and child system prompts carried the machine's
real skill catalog, and only `PI_CODING_AGENT_DIR` content was isolated.

The reviewer read the persona, the document, and searched the directory for
related designs, then returned a two-heading paraphrase plus eighteen findings
(1 blocker, 13 major, 4 nit). It judged the document's core proposal — a
per-level loop with one login, a module-level level table, new parsers and one
normalisation point — paraphraseable, but reported that the normalisation
section describes a validation gate rather than a normaliser, that the stated
"dependency order" lists parsers before the constants they import, that the
recommended Hearing-only first ship is not delineated from the full three-level
change set, that the 600 s budget arithmetic ignores the 180 s per-request
read timeout, and that "pin", "credential", "apply", "breaker" and "twin"
are load-bearing terms the document never defines.
