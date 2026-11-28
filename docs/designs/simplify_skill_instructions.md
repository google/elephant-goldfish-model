# Simplify Skill Instructions and Isolate Harness Workarounds

*   **Author:** Rohit Singh ([@singhrohit90](https://github.com/singhrohit90))
*   **Status:** Draft
*   **Date:** 2026-11-28
*   **Issue:** [#477](https://github.com/google/elephant-goldfish-model/issues/477)

--------------------------------------------------------------------------------

## Overview

This Stage 1 design document proposes a prompt-wording cleanup across the
Elephant-Goldfish Model (EGM) core skills
([`egm-bootstrap`](../../skills/egm-bootstrap/SKILL.md),
[`egm-brainstorm`](../../skills/egm-brainstorm/SKILL.md),
[`egm-draft`](../../skills/egm-draft/SKILL.md),
[`egm-review`](../../skills/egm-review/SKILL.md)) and shared execution rules
([`resources/execution_instructions.md`](../../resources/execution_instructions.md)).
It reserves `CRITICAL` markers for genuine safety and isolation gates, replaces
harness-specific `ask_question` JSON payload and tool-batching choreography with
plain-English behavioral invariants, and removes redundant `Banned Apologies`
blocks.

## The Problem

Inspecting the current skill prompts and shared execution rules on `main` shows
three sources of instruction noise and cross-harness leakage:

1.  **`CRITICAL` Over-Saturation**: Every core skill opens with an
    `## Execution Constraints (CRITICAL)` (or `& Delegation (CRITICAL)`)
    heading, and individual rules add more `(CRITICAL)` tags—for example,
    `Empty Write-in Guard (CRITICAL)` in `skills/egm-draft/SKILL.md` (which
    re-prompts if a user selects a write-in option with empty text),
    `Final Correctness Verification (CRITICAL)` in
    `skills/egm-bootstrap/SKILL.md` (which re-reads generated contract files),
    and four `(CRITICAL)` rules in `resources/execution_instructions.md`
    (`Scratchpad Location`, `ONE QUESTION AT A TIME`, `NO SUMMARIES`, and
    `Contradiction Auditing`). The working assumption of this design is that
    marking routine formatting and workflow steps `CRITICAL` dilutes the signal
    of genuine safety and isolation gates.
2.  **Harness-Specific Tool Choreography in Core Prompts**:
    `skills/egm-review/SKILL.md`, `skills/egm-draft/SKILL.md`,
    `skills/egm-brainstorm/SKILL.md`, `skills/egm-bootstrap/SKILL.md`, and
    `resources/execution_instructions.md` embed `ask_question` schema and
    tool-batching workarounds (`len(questions) == 1`, `is_multi_select: false`,
    `"questions": [...]` JSON blocks, `"be the sole tool call in its model
    response step"`, and `"never emit a structured question call with empty
    visible chat text"`). These rules work around one host's tool-batching
    behavior and leak host-specific schema assumptions into other hosts (such
    as Codex, Copilot CLI, and Cursor).
3.  **Redundant `Banned Apologies` Instructions**: The rule forbidding polite
    apologies (`"I apologize"`, `"I am sorry"`, `"Forgive me"`) is repeated in
    `skills/egm-draft/SKILL.md`, `skills/egm-brainstorm/SKILL.md`,
    `skills/egm-review/SKILL.md`, and `resources/execution_instructions.md`,
    adding repeated prompt tokens across every skill invocation.

## Goals

*   **Reserve `CRITICAL` for High-Impact Gates**: Limit `CRITICAL` markers to
    the 2–3 high-impact safety, isolation, and scope boundaries per file, each
    paired with a one-line rationale explaining why it matters.
*   **Strip Harness Tool-Batching Quirks While Preserving Behavioral
    Invariants**: Remove `len(questions) == 1`, `is_multi_select: false`,
    `sole tool call`, and raw JSON `"questions": [...]` blocks from core
    skills and `resources/execution_instructions.md`, while preserving the
    underlying EGM behavioral invariants in plain English (single-select choices
    only, primary default option first without `(Recommended)` prefixes, visible
    chat text before the gate, open-ended inputs in plain chat, and waiting for
    the user's answer before continuing).
*   **Isolate Any Host-Specific Note in Runtime-Loaded Host Docs**: Keep
    human-facing `docs/harnesses.md` free of runtime tool-batching rules; if a
    specific host (such as Claude Code, which reads
    `${CLAUDE_PLUGIN_ROOT}/docs/claude.md`) still requires an explicit
    turn-yielding reminder, place it only in that host's runtime-loaded guide.
*   **Remove Redundant `Banned Apologies` Text**: Delete `Banned Apologies`
    from `resources/execution_instructions.md`, `skills/egm-draft/SKILL.md`,
    `skills/egm-brainstorm/SKILL.md`, and `skills/egm-review/SKILL.md`.
*   **Unify Shared-Rule Delegation**: Align `skills/egm-draft/SKILL.md` and
    `skills/egm-brainstorm/SKILL.md` with `skills/egm-review/SKILL.md` by
    referencing `resources/execution_instructions.md` for shared `Plain-English
    Standard` (direct, jargon-free prose) and `Adversarial Rigor` (stress-test
    before agreeing) rules, keeping only a short inline fallback when
    `execution_instructions.md` cannot be read.

## Non-Goals

*   **No Stage Order or Delegation Topology Changes**: This proposal does not
    alter `egm-review` stage ordering (`5 -> 6 -> 7 -> 8 -> 9`: Initial Zoom Out,
    Comprehension, Critic, Intermediate Zoom Out, Implementation Readiness),
    Goldfish isolation (spawning fresh-context, stateless reviewer subagents with
    no conversation history), or `egm-bootstrap` directory thresholds.
*   **No New Harness Adapters**: This proposal does not add or modify adapter
    code under `scripts/` or host packaging layouts.
*   **No Removal of `resources/execution_instructions.md`**: Shared cross-skill
    rules remain in `resources/execution_instructions.md` (building on
    [PR #369](https://github.com/google/elephant-goldfish-model/pull/369),
    which consolidated shared rules out of `egm-bootstrap` and `egm-review`).

## Open Questions

*   **Question 1**: Does Claude Code or Antigravity still require an explicit
    turn-yielding note in `docs/claude.md` once `sole tool call` is removed from
    core skills, or can the workaround be deleted entirely?

## Critical User Journeys (CUJs)

### CUJ 1: Interactive Skill Execution Without Harness Leakage

*   **Given**: A user runs `/egm-review`, `/egm-draft`, `/egm-brainstorm`, or
    `/egm-bootstrap` in Codex, Claude Code, or Antigravity.
*   **When**: The skill reaches an interactive gate or question step.
*   **Then**: The agent emits visible context, presents a single-select choice
    (or open-ended question in plain chat), and waits for the user's answer
    without relying on `ask_question` JSON payload rules in the core skill.

### CUJ 2: High-Signal Safety Gates Under `egm-bootstrap` and `egm-draft`

*   **Given**: A user runs `/egm-bootstrap` on a repository with > 15
    subdirectories or `/egm-draft` in a source repository.
*   **When**: The agent encounters a high-impact boundary (the `> 15` subtree
    safety gate, BFS no-recursive-find scoping, or `egm-draft`
    no-production-code / scratchpad isolation).
*   **Then**: The `CRITICAL` marker stands out clearly with its one-line
    rationale, while routine formatting and style rules are stated at normal
    emphasis.

## Technical Plan (Architecture)

```text
skills/egm-{bootstrap,brainstorm,draft,review}/SKILL.md
  ├── Keep 2-3 high-impact CRITICAL gates (+ 1-line rationale each)
  ├── State routine rules at normal volume
  ├── Use plain-English behavioral invariants (no JSON / sole-tool-call quirks)
  ├── Omit "Banned Apologies" blocks
  └── Reference resources/execution_instructions.md (short inline fallback)
        │
        ▼
resources/execution_instructions.md
  ├── Keep CRITICAL only on Scratchpad Location & ONE QUESTION AT A TIME
  ├── Plain-English Interaction Invariants (single-select, Option 0 default, wait)
  └── Omit "Banned Apologies"
        │
        ▼
docs/claude.md (only if host testing shows turn-yielding still needs a note)
```

### 1. `CRITICAL` Triage Across Core Files

| File | Keep `CRITICAL` (with 1-line reason) | Downgrade to Normal Volume |
| :--- | :--- | :--- |
| `resources/execution_instructions.md` | `Scratchpad Location` (prevents polluting source tree), `ONE QUESTION AT A TIME` (prevents bundled multi-question overload) | `NO SUMMARIES`, `Contradiction Auditing` |
| `skills/egm-bootstrap/SKILL.md` | `Mandatory Safety Gate (> 15 Subdirectories)` (caps fan-out cost), `BFS Discovery` no-recursive-find rule (prevents hangs on large trees), `No Code Generation & VCS Isolation` (documentation-only boundary) | Section heading `## Execution Constraints`, `Final Correctness Verification` |
| `skills/egm-draft/SKILL.md` | `Design-Only Scope` / `Scratchpad Location` (prevents source-tree edits), `Explicit Consensus Gates` (prevents skipping author sign-off) | Section heading `## Execution Constraints`, `Empty Write-in Guard` |
| `skills/egm-brainstorm/SKILL.md` | `Goldfish Isolation` / `Readiness Gate` (prevents premature subagent fan-out before problem drilling) | Section heading `## Execution Constraints` |
| `skills/egm-review/SKILL.md` | `Goldfish Isolation` (same-context review invalidates independent audit), `Stage Order` (`5 -> 6 -> 7 -> 8 -> 9` prevents skipping Zoom Out / Comprehension) | Section heading `## Execution Constraints & Delegation` |

### 2. Harness-Quirk Removal & Plain-English Interaction Invariants

*   Replace `len(questions) == 1`, `is_multi_select: false`, `sole tool call in
    its model response step`, and inline `"questions": [...]` JSON blocks across
    all four core skills and `resources/execution_instructions.md` with
    plain-English single-select gate descriptions.
*   Preserve non-harness EGM invariants in `Interaction Invariants`: single-select
    only (no multi-select checklists), primary default action first without
    `(Recommended)` prefixes, visible chat text before the gate, open-ended
    inputs in plain chat, and waiting for the user's answer before continuing.
*   Do not move runtime tool-batching rules into `docs/harnesses.md`, because
    `docs/harnesses.md` is human-facing documentation (and
    `tests/unit/test_harnesses.py` forbids backticked `docs/harnesses.md`
    references in `egm-bootstrap` and `egm-review`).

### 3. `Banned Apologies` Removal & Shared-Rule Alignment

*   Remove `Banned Apologies` from `resources/execution_instructions.md`,
    `skills/egm-draft/SKILL.md`, `skills/egm-brainstorm/SKILL.md`, and the
    inline summary in `skills/egm-review/SKILL.md`.
*   Trim duplicated `Plain-English Standard` and `Adversarial Rigor` bullets in
    `skills/egm-draft/SKILL.md` and `skills/egm-brainstorm/SKILL.md` to match
    `skills/egm-review/SKILL.md`'s pattern (reference
    `resources/execution_instructions.md`, with a short inline fallback).

## Alternatives Considered

### Alternative A: Move `ask_question` Workarounds to `docs/harnesses.md`

*   **Pros**: Keeps the workaround documented in one central harness file.
*   **Cons**: `docs/harnesses.md` is not loaded by skills at runtime, so moving
    runtime rules there silently drops them while adding YAGNI doc churn.
*   **Reason for Rejection**: Rejected by author: runtime-only notes belong in
    runtime-loaded host guides (such as `docs/claude.md`) only if a host still
    requires them.

### Alternative B: Move All Constraints Out of `SKILL.md` Into `resources/`

*   **Pros**: Maximum deduplication across skills.
*   **Cons**: Hosts that inject `SKILL.md` without preloading
    `resources/execution_instructions.md` could miss safety gates.
*   **Reason for Rejection**: Rejected by author: genuine safety and isolation
    gates must remain visible in `SKILL.md`.

## Risks & Mitigations

*   **Multi-Model Instruction-Following Drift**: Removing `CRITICAL` tags,
    `Banned Apologies`, or `sole tool call` could soften compliance on smaller
    or non-Claude models (Codex, Copilot, Cursor, OpenCode, Muse).
    *   *Mitigation*: Keep `CRITICAL` on genuine safety/isolation gates with
        one-line rationales, preserve all behavioral invariants in plain English,
        and verify Stage 2 changes with `tests/unit/test_scenario_coverage.py`
        and manual multi-host spot checks.
*   **Host Fails to Pause on Single-Question Intent**: A host that previously
    relied on `sole tool call` might batch a question with file writes.
    *   *Mitigation*: State `"Ask one question at a time and wait for the user's
        answer before continuing"` explicitly, and add a targeted note in
        `docs/claude.md` only if Claude Code testing shows batching regressions.
*   **Unit Test String Assertions**: `tests/unit/test_harnesses.py` asserts
    exact phrases in `resources/execution_instructions.md` and
    `skills/egm-bootstrap/SKILL.md` (such as `mktemp -d`,
    `Do not use fixed, shared paths`, and `up to 5 parallel workers`).
    *   *Mitigation*: Preserve asserted phrases and run `pytest tests/unit`
        after every Stage 2 edit.

--------------------------------------------------------------------------------

## Non-Functional Requirements

*   **Token Overhead**: Removing repeated `Banned Apologies` blocks, inline JSON
    gate templates, and duplicated `Plain-English Standard` / `Adversarial
    Rigor` bullets reduces per-invocation prompt tokens across core skills.
*   **Packaging Consistency**: Changes to `skills/` and `resources/` must keep
    generated runtime packages (built by `scripts/pack_plugin.py`) in sync,
    enforced by `tests/unit/test_packaging.py`.

--------------------------------------------------------------------------------

## Detailed Implementation Plan

### Target Files to Modify (Stage 2)

1.  `resources/execution_instructions.md`: Apply `CRITICAL` triage per table
    above; remove `Banned Apologies`; replace `len(questions) == 1`,
    `is_multi_select: false`, and `sole tool call` with plain-English
    `Interaction Invariants`.
2.  `skills/egm-bootstrap/SKILL.md`: Apply `CRITICAL` triage; replace
    `is_multi_select: false` at lines 50 and 92 with plain-English single-select
    gate descriptions.
3.  `skills/egm-brainstorm/SKILL.md`: Apply `CRITICAL` triage; remove `Banned
    Apologies`; replace `len(questions) == 1` / `sole tool call` and JSON
    `"questions": [...]` blocks with plain-English gate descriptions; trim
    duplicated shared rules to reference `resources/execution_instructions.md`.
4.  `skills/egm-draft/SKILL.md`: Apply `CRITICAL` triage; remove `Banned
    Apologies`; replace `len(questions) == 1` / `sole tool call` and JSON
    `"questions": [...]` blocks with plain-English gate descriptions; trim
    duplicated shared rules to reference `resources/execution_instructions.md`.
5.  `skills/egm-review/SKILL.md`: Apply `CRITICAL` triage; remove `"or
    apologies"` from the inline style summary; replace `len(questions) == 1`,
    `is_multi_select: false`, and `sole tool call` with plain-English
    `Interaction Invariants`.
6.  `docs/claude.md` (conditional): Add a brief `ask_question` turn-yielding
    note only if Stage 2 testing on Claude Code shows a regression.

### Verification Plan

*   **Unit Tests**: `uv run --no-project --with pytest --with pyyaml pytest tests/unit`
*   **Targeted Invariant Suites**: Confirm `tests/unit/test_harnesses.py`,
    `tests/unit/test_packaging.py`, `tests/unit/test_frontmatter.py`, and
    `tests/unit/test_scenario_coverage.py` pass without relaxing assertions.

--------------------------------------------------------------------------------

*Drafted with EGM*
