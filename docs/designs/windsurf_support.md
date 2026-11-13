# Windsurf workspace routing

- **Author:** [@n3wth](https://github.com/n3wth)
- **Status:** Proposal. Maintainer scope approval and design review pending.
- **Date:** 2026-11-10
- **Tracking:** [#376](https://github.com/google/elephant-goldfish-model/issues/376)

## Problem statement

Windsurf Cascade loads workspace rules from `.windsurf/rules/*.md` and slash
workflows from `.windsurf/workflows/*.md`. Users who open the EGM repository in
Windsurf have no native entry points for the seven EGM workflows. Copying skill
instructions into `.windsurf/workflows/` causes drift against
`skills/*/SKILL.md` and violates Goldfish fresh-context reviewer isolation.

This specification defines an experimental workspace routing adapter for
Windsurf Cascade. Each Windsurf entry point routes directly to the canonical
`skills/`, `agents/`, and `resources/` files at the repository root. Goldfish
swarm workflows stop immediately whenever Windsurf lacks isolated, read-only
subagent delegation.

## Scope

This section defines the boundaries for experimental Windsurf workspace routing
under [#376](https://github.com/google/elephant-goldfish-model/issues/376).

### Goals

The experimental adapter delivers four capabilities:

- Expose all seven EGM workflows as `.windsurf/workflows/egm-*.md` slash
  commands of at most 15 lines without copied skill prose.
- Define one `.windsurf/rules/egm.md` workspace rule (`trigger: model_decision`)
  that routes EGM requests to shared root files.
- Stop Goldfish swarm workflows (`egm-brainstorm`, `egm-review`,
  `egm-review-loop`) when fresh-context, read-only subagents are unavailable.
- Verify routing contracts, skill coverage, and line limits offline in
  `tests/unit/test_windsurf.py`.

### Non-goals

This change excludes four items:

- Claiming verified Windsurf support before live workflow execution, read-only
  enforcement, and reviewer isolation tests pass.
- Duplicating prompt rules from `skills/*/SKILL.md` or `agents/*.md` inside
  `.windsurf/`.
- Supporting non-root installations or filesystem symlinks, which fail Windows
  checkouts and multi-harness plugin validators.
- Building a custom Windsurf extension binary or an MCP subagent server in Stage
  1.

## Existing components and ownership

All canonical workflow behavior remains in `skills/`, `agents/`, and
`resources/` at the repository root. See [harnesses](../harnesses.md) and
[TESTING.md](../../TESTING.md) for current host boundaries.

The Windsurf adapter contributor maintains `.windsurf/`, the status entry in
[harnesses](../harnesses.md), and `tests/unit/test_windsurf.py`. Repository
maintainers approve the feature scope and decide when live test records justify
upgrading Windsurf from experimental status. Human users own all design
decisions and workflow approval gates.

## Proposed architecture

The adapter requires a workspace-root checkout where `.windsurf/` sits beside
`skills/`, `agents/`, and `resources/`. It adds eight minimal Markdown files
under `.windsurf/`, one status paragraph in [harnesses](../harnesses.md), and
one unit test module.

### Component layout

The table below lists each file in the adapter and its contract.

| Path | Role | Constraint |
| --- | --- | --- |
| `.windsurf/rules/egm.md` | Workspace routing and Goldfish isolation rule | Uses `trigger: model_decision` frontmatter and stays at or below 20 lines |
| `.windsurf/workflows/egm-*.md` | Seven slash-command pointers to `skills/egm-*/SKILL.md` | Stays at or below 15 lines with zero copied skill prose |
| `docs/harnesses.md` | User-facing host status record | Marks Windsurf experimental and notes missing live isolation evidence |
| `tests/unit/test_windsurf.py` | Offline contract test | Verifies rule frontmatter, skill parity, target paths, and isolation split |

### Execution and isolation flow

When a user runs `/egm-<workflow>` in Windsurf Cascade from the repository root,
execution follows four rules:

1. Cascade reads `.windsurf/workflows/egm-<workflow>.md` and
   `.windsurf/rules/egm.md`.
2. Cascade resolves `skills/egm-<workflow>/SKILL.md`, `agents/*.md`, and
   `resources/document_standards/*.md` relative to the workspace root.
3. Single-session and inline-capable workflows (`egm-draft`, `egm-resolve`,
   `egm-drift-report`, `egm-bootstrap`) run in the active session. In
   `egm-bootstrap`, Cascade runs scout steps inline when no subagent tool
   exists, matching [egm-bootstrap](../../skills/egm-bootstrap/SKILL.md).
4. Goldfish swarm workflows (`egm-brainstorm`, `egm-review`, `egm-review-loop`)
   require isolated, read-only subagents with zero parent history. Before
   executing reviewer prompts, the workflow wrapper instructs Cascade to stop
   if native read-only subagent delegation is unavailable. Cascade reports that
   a same-context review is not a Goldfish review and invokes no write or shell
   tools.
5. Every Goldfish reviewer launches on the host's read-only subagent profile
   (`subagent_explore` in the Devin CLI, which exposes no write, edit, or shell
   tool). The rule and the three Goldfish wrappers forbid write-capable
   profiles and forbid resuming a reviewer. Reviewers return findings as text.
   Only the parent writes files: the outputs the skill assigns to it, or a file
   the user asks for, after the user approves the write.

### Human approval gates

Windsurf Cascade uses plain chat responses when no structured question widget
is available. The adapter preserves every human pause from the canonical skills:

- [Brainstorm](../../skills/egm-brainstorm/SKILL.md): wait for user readiness
  before Goldfish dispatch and wait for brief approval before handoff.
- [Draft](../../skills/egm-draft/SKILL.md): wait for intake sign-off, section
  approvals, and output path approval.
- [Review](../../skills/egm-review/SKILL.md): wait for preset selection and
  stage pause choices once subagent delegation exists.
- [Resolve](../../skills/egm-resolve/SKILL.md): present proposed fixes and
  contested items and wait for explicit user approval before editing files.

## Verification and release gates

Validation separates hermetic CI tests from live Windsurf Cascade probes,
matching [additional-harnesses.md](additional-harnesses.md) and
[TESTING.md](../../TESTING.md).

### Offline tests

Automated CI runs `tests/unit/test_windsurf.py` on Linux and Windows without
Windsurf installed:

- Verify `.windsurf/rules/egm.md` parses valid YAML frontmatter, sets
  `trigger: model_decision`, and states the `fresh-context` rule.
- Verify `.windsurf/workflows/*.md` matches `EXPECTED_SKILLS` one-to-one and
  stays at or below 15 lines per file.
- Verify Goldfish swarm workflows (`egm-brainstorm`, `egm-review`,
  `egm-review-loop`) carry the subagent stop rule while single-session and
  inline workflows (`egm-draft`, `egm-resolve`, `egm-drift-report`,
  `egm-bootstrap`) do not false-stop.
- Verify the rule and the three Goldfish wrappers name the read-only subagent
  profile, forbid resuming a reviewer, and reserve file writes for the parent.

### Live promotion gates

Windsurf retains experimental status until a contributor records live evidence
on a pinned Windsurf version for three gates:

1. **Workflow execution**: Run `egm-brainstorm`, `egm-draft`, and `egm-review`
   from a clean workspace and verify interactive human pauses.
2. **Read-only enforcement**: Attempt to write a disposable workspace file from
   a Goldfish reviewer subagent and verify host tool denial.
3. **Fresh-context isolation**: Place a random marker in the parent session.
   Inspect Windsurf trajectory logs to verify child reviewers receive neither
   parent history nor sibling findings.

Gate 2 needs two probes. A request that names no EGM workflow does not load the
`model_decision` rule, so it does not test the adapter. Probe the host by asking
a subagent on the read-only profile to create a file. Probe the adapter by
asking, inside `/egm-review`, for each reviewer to save its own notes.

### Recorded CLI evidence (2026-11-10)

Cognition renamed Windsurf to Devin Desktop on 2026-06-02. Devin Local
replaced Cascade as the local agent, and the legacy Cascade agent ended on
2026-07-01. Devin Desktop and the Devin CLI run the same Devin Local agent.
Devin Desktop was not installed for these runs. The author drove the Devin CLI 3000.12.43 from a Muse 1.4.15 session on
macOS 27.2, headless and interactively in `tmux`, against the
[#379](https://github.com/google/elephant-goldfish-model/pull/379) adapter. The
CLI lists `.windsurf/rules/egm.md` as a Windsurf rule. It does not list
`.windsurf/workflows/` as slash commands; `/egm-*` requests route through the
rule. Every file write was denied, so no workflow ran to its final artifact.

| Gate | CLI result | Evidence |
| --- | --- | --- |
| Workflow execution | Pass for routing and pauses | `egm-brainstorm`, `egm-draft`, and `egm-review` read their `SKILL.md`. Draft paused three times before any write. Brainstorm waited for readiness before dispatching seven reviewers. Review paused at intake |
| Read-only enforcement | Pass | A subagent on the read-only profile had no tool that writes. Inside EGM workflows, 22 of 22 reviewer launches used that profile with no resume. A reviewer-notes file the user asked for reached the user as a parent write prompt and was not written |
| Fresh-context isolation | Pass | The marker appeared in 0 of 2 reviewer task texts and 0 of 70 child transcript nodes in the host session store |

These runs do not satisfy the promotion gates. They used the CLI, not the IDE,
and stopped before final artifacts.

## Alternatives considered

The table below evaluates design alternatives against maintenance cost and
isolation safety.

| Alternative | Decision | Rationale |
| --- | --- | --- |
| Copy `SKILL.md` bodies into `.windsurf/workflows/*.md` | Rejected | Windsurf caps each workflow at 12,000 characters, and copied prompts drift on every edit |
| Symlink `.windsurf/workflows/` to `skills/` | Rejected | Windsurf expects flat `.md` files, and symlinks fail Windows checkouts and packagers |
| Simulate Goldfish personas sequentially in one chat | Rejected | Shared conversation history violates EGM fresh-context reviewer independence |
| Build an MCP server to spawn external reviewers | Deferred | An MCP server adds runtime setup and API key handling, which belongs in a separate proposal if Windsurf adds no native subagent API |
| Defer all Windsurf files until live isolation passes | Rejected | Minimal routing files let users run `egm-draft` and `egm-resolve` safely while blocking simulated reviews |

## Risks and mitigations

The table below lists technical constraints, security risks, and mitigations.

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Cascade ignores prose rules and simulates inline reviews | Breaches Goldfish isolation and exposes workspace write tools | Keep Windsurf experimental, put an immediate stop instruction in the three Goldfish wrappers, and forbid write or shell calls in review paths |
| Windsurf enforces a 12,000-character limit per workflow file | Large workflows fail to load in Cascade | Cap `.windsurf/workflows/*.md` at 15 lines in `test_windsurf.py` and keep full prompts in `skills/` |
| Users copy `.windsurf/` without the repository root | Relative `skills/` paths fail to open | State the workspace-root layout requirement in `.windsurf/rules/egm.md` so missing files fail immediately |
| A request that names no EGM workflow asks for a reviewer subagent | The host does not load the rule, picks a write-capable profile, and offers to write for the reviewer | Out of adapter scope. The rule governs EGM workflows only; the Gate 2 probes above run inside them |
| The user denies a permission prompt in an interactive session | The host ends its turn without a message and drops batched tool calls | Host behavior. Send a follow-up message to continue; record it as a limit in [harnesses](../harnesses.md) |
| Personal session hooks or MCP servers inject instructions | A headless run can stop on a rejected tool call before it reads the skill | Run live probes with a host config that has no hooks |
| New EGM skills land without a Windsurf workflow | Slash command list falls behind `skills/` | `test_windsurf.py` asserts exact equality against `EXPECTED_SKILLS` on every pull request |

## Rollout and rollback

Rollout uses a two-PR stack under
[#376](https://github.com/google/elephant-goldfish-model/issues/376):

1. Merge this Stage 1 specification and its index row in
   [README.md](README.md) (`Refs #376`).
2. Merge the stacked Stage 2 implementation in
   [#379](https://github.com/google/elephant-goldfish-model/pull/379)
   (`Refs #376`), leaving
   [#376](https://github.com/google/elephant-goldfish-model/issues/376) open
   until live Windsurf verification passes.

Rollback is a single revert of
[#379](https://github.com/google/elephant-goldfish-model/pull/379). Reverting
removes `.windsurf/`, the status note in [harnesses](../harnesses.md), and
`tests/unit/test_windsurf.py` without touching any other harness.

## Open decisions and review status

- Maintainers must review this Stage 1 scope under
  [#376](https://github.com/google/elephant-goldfish-model/issues/376) before
  [#379](https://github.com/google/elephant-goldfish-model/pull/379) merges.
- The author ran subagent delegation, read-only denial, and session-store
  inspection on the Devin CLI on 2026-11-10; see
  [Recorded CLI evidence](#recorded-cli-evidence-2026-11-10). No contributor
  has run them in the Windsurf IDE (Devin Desktop) or to a final artifact.
- Maintainers decide whether Devin CLI evidence counts toward the promotion
  gates or only IDE evidence does. Both surfaces run Devin Local.
- The author ran the EGM Structural, Style, and Design Critic Goldfish
  reviewers on 2026-11-10 against the feature specification standard and
  resolved all Blocker and Major findings in this draft and in
  [#379](https://github.com/google/elephant-goldfish-model/pull/379).

## Research references

Reviewed 2026-11-10. These links document Windsurf surfaces rather than EGM
verification evidence:

- [Windsurf is now Devin Desktop](https://devin.ai/blog/windsurf-is-now-devin-desktop)
- [Devin Desktop FAQ](https://docs.devin.ai/desktop/devin-desktop-faq)
- [Windsurf Cascade workflows](https://docs.windsurf.com/windsurf/cascade/workflows)
- [Windsurf Cascade memories and rules](https://docs.windsurf.com/windsurf/cascade/memories)
- [Additional coding-agent harness support](additional-harnesses.md)
- [Harness integrations](../harnesses.md)
- [EGM harness test record](../../TESTING.md#harness-test-record)
