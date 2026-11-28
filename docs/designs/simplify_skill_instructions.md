# Simplify Skill Instructions and Isolate Harness Workarounds

*   **Author:** EGM Contributors
*   **Status:** Draft
*   **Date:** 2026-11-28
*   **Issue:** [#477](https://github.com/google/elephant-goldfish-model/issues/477)

--------------------------------------------------------------------------------

## Overview

This design proposes a prompt-wording cleanup across EGM's core skills
(`skills/egm-bootstrap/SKILL.md`, `skills/egm-brainstorm/SKILL.md`,
`skills/egm-draft/SKILL.md`, `skills/egm-review/SKILL.md`) and shared execution
rules (`resources/execution_instructions.md`). It reduces `CRITICAL` label
density, replaces harness-specific `ask_question` tool-batching choreography
with plain-language intent, and removes redundant "Banned Apologies" rules.

## The Problem

Prompt audits against current models and multi-harness deployments show three
recurring sources of noise and cross-harness leakage:

1.  **`CRITICAL` Over-Saturation**: Every core skill opens with an
    `## Execution Constraints (CRITICAL)` (or `& Delegation (CRITICAL)`)
    heading, and individual rules add more `(CRITICAL)` tags (such as
    `Empty Write-in Guard (CRITICAL)` in `skills/egm-draft/SKILL.md`,
    `Final Correctness Verification (CRITICAL)` in
    `skills/egm-bootstrap/SKILL.md`, and four `(CRITICAL)` rules in
    `resources/execution_instructions.md`). When almost every rule is marked
    `CRITICAL`, models over-apply routine formatting preferences and lose the
    distinction between genuine safety gates and normal workflow guidance.
2.  **Harness-Specific Tool Choreography in Core Skills**:
    `skills/egm-review/SKILL.md`, `skills/egm-draft/SKILL.md`,
    `skills/egm-brainstorm/SKILL.md`, and `resources/execution_instructions.md`
    embed `ask_question` payload details (`len(questions) == 1`,
    `is_multi_select: false`, "be the sole tool call in its model response step",
    "never emit a structured question call with empty visible chat text"). These
    constraints work around one harness's tool-batching behavior and leak
    irrelevant JSON schema assumptions into other harnesses (such as Codex or
    Copilot CLI).
3.  **Redundant "Banned Apologies" Instructions**: The rule forbidding polite
    apologies (`"I apologize"`, `"I am sorry"`, `"Forgive me"`) is repeated in
    `skills/egm-draft/SKILL.md`, `skills/egm-brainstorm/SKILL.md`,
    `skills/egm-review/SKILL.md`, and `resources/execution_instructions.md`.
    Modern models do not require multi-line anti-apology bans, and repeating
    them across skills wastes prompt tokens on every invocation.

## Goals

*   **Reserve `CRITICAL` for Real Gates**: Limit `CRITICAL` markers to the
    small set of high-impact safety, isolation, and correctness gates (for
    example: the `egm-bootstrap` `> 15` subtree safety gate and BFS scoping
    rule, `egm-draft` scratchpad and no-production-code boundaries, and
    artifact-first / Goldfish-isolation boundaries), each paired with a one-line
    rationale.
*   **Express Interaction Intent Plainly**: Replace `len(questions) == 1` and
    `sole tool call` choreography in core skills and
    `resources/execution_instructions.md` with plain-language intent (such as
    "Ask one question at a time and wait for the user's answer before
    continuing."), moving any host-specific `ask_question` batching notes to
    `docs/harnesses.md`.
*   **Remove Redundant Anti-Apology Text**: Delete the "Banned Apologies"
    blocks from `skills/egm-draft/SKILL.md`, `skills/egm-brainstorm/SKILL.md`,
    `skills/egm-review/SKILL.md`, and `resources/execution_instructions.md`.
*   **Preserve Behavioral & Packaging Invariants**: Keep all existing skill
    frontmatter, stage ordering (`5 -> 6 -> 7 -> 8 -> 9` in `egm-review`),
    Goldfish isolation semantics, and `pytest tests/unit` checks passing.

## Non-Goals

*   **No Runtime Behavior Changes**: This proposal does not alter skill stage
    sequences, subagent delegation topology, or `egm-bootstrap` thresholds.
*   **No New Harness Adapters**: This proposal does not add or modify adapter
    code under `scripts/` or host-specific packaging layouts.
*   **No Removal of `resources/execution_instructions.md`**: Shared cross-skill
    rules remain in `resources/execution_instructions.md` (building on #369).

## Open Questions

*   Should `skills/egm-draft/SKILL.md` and `skills/egm-brainstorm/SKILL.md`
    also trim their duplicated `Plain-English Standard` / `Adversarial Rigor`
    bullets to reference `resources/execution_instructions.md` directly (matching
    `skills/egm-review/SKILL.md`), or keep short inline summaries for hosts
    where `execution_instructions.md` is not preloaded?

## Critical User Journeys (CUJs)

### CUJ 1: Interactive Skill Execution Without Harness Leakage

*   **Given**: A user runs `/egm-review`, `/egm-draft`, or `/egm-brainstorm` in
    Codex, Claude Code, or Antigravity.
*   **When**: The skill reaches an interactive gate or question step.
*   **Then**: The agent asks one clear question and waits for the user's
    response without relying on `ask_question`-specific JSON payload rules in
    the core skill prompt.

### CUJ 2: High-Signal Safety Gates Under `egm-bootstrap` and `egm-draft`

*   **Given**: A user runs `/egm-bootstrap` on a repository with > 15
    subdirectories or `/egm-draft` in a source repository.
*   **When**: The agent encounters a real safety boundary (subtree size gate,
    no-recursive-search rule, or no-production-code rule).
*   **Then**: The `CRITICAL` marker stands out clearly with its one-line
    rationale, while routine formatting and style guidance are stated at normal
    emphasis.

## Technical Plan (Architecture)

```text
skills/egm-*/SKILL.md
  ├── Keep 2-3 real CRITICAL gates (+ 1-line rationale each)
  ├── State routine rules at normal volume
  ├── Use plain-English interaction intent ("Ask one question and wait...")
  └── Omit "Banned Apologies" blocks
        │
        ▼
resources/execution_instructions.md
  ├── Shared rules without CRITICAL overuse or Banned Apologies
  └── Plain-English Interaction Invariants (no JSON tool-batching quirks)
        │
        ▼
docs/harnesses.md
  └── Host-specific structured question / tool-batching notes (where needed)
```

1.  **`CRITICAL` Triage Across Core Skills & `resources/execution_instructions.md`**:
    *   Rename section headings from `## Execution Constraints (CRITICAL)` /
        `## Execution Constraints & Delegation (CRITICAL)` to
        `## Execution Constraints` / `## Execution Constraints & Delegation`.
    *   Remove `(CRITICAL)` from routine headings (`NO SUMMARIES`,
        `Empty Write-in Guard`, `Final Correctness Verification` unless
        justified as a strict gate).
    *   Keep `CRITICAL` only on the 2–3 genuine safety/isolation gates per
        skill (e.g., `egm-bootstrap` `> 15` Safety Gate and BFS no-recursive-find
        rule; `egm-draft` no-production-code / scratchpad isolation; `egm-review`
        Goldfish isolation), each with a one-line explanation of why it matters.
2.  **Harness-Quirk Extraction**:
    *   Replace `len(questions) == 1`, `is_multi_select: false`, and `sole tool
        call in its model response step` rules in `skills/egm-review/SKILL.md`,
        `skills/egm-draft/SKILL.md`, `skills/egm-brainstorm/SKILL.md`, and
        `resources/execution_instructions.md` with plain-language guidance:
        "Ask one question at a time and wait for the user's answer before
        continuing."
    *   Document host-specific structured question tool behavior (e.g.,
        single-question `ask_question` turn-yielding) in `docs/harnesses.md`
        so non-affected harnesses do not pay the token or instruction-following
        cost.
3.  **Remove "Banned Apologies"**:
    *   Delete the `Banned Apologies` rule from
        `resources/execution_instructions.md`, `skills/egm-draft/SKILL.md`,
        `skills/egm-brainstorm/SKILL.md`, and the inline summary in
        `skills/egm-review/SKILL.md`.

## Alternatives Considered

### Alternative A: Keep All Rules Inline With Softer Wording Only

*   **Pros**: Fewer cross-file references; single-file self-containment.
*   **Cons**: Leaves `ask_question` tool-batching workarounds in every skill,
    continuing to leak one harness's quirks into Codex, Copilot, and Cursor.
*   **Reason for Rejection**: Rejected by author: fails to isolate harness
    workarounds from core skill prompts.

### Alternative B: Move All Constraints Out of `SKILL.md` Into `resources/`

*   **Pros**: Maximum deduplication across skills.
*   **Cons**: Hosts that inject `SKILL.md` without preloading
    `resources/execution_instructions.md` could miss critical safety gates.
*   **Reason for Rejection**: Rejected by author: genuine safety gates must
    remain visible in `SKILL.md`.

## Non-Functional Requirements

*   **Token Overhead**: Removing repeated anti-apology bans and tool-batching
    boilerplate reduces per-invocation prompt tokens across all core skills.
*   **Packaging Consistency**: Any changes to `skills/` and `resources/` must
    be reflected in generated runtime packages if applicable and pass
    `tests/unit/test_packaging.py`.

--------------------------------------------------------------------------------

## Detailed Implementation Plan

### Target Files to Create/Modify (Stage 2)

#### 1. `resources/execution_instructions.md` (Modify)

*   **Type / Scope**: Shared Skill Execution Rules
*   **Proposed Changes**: Remove `Banned Apologies`; replace `len(questions) == 1`
    / `sole tool call` choreography in `Interaction Invariants` with plain
    "ask one question and wait" guidance; reduce `(CRITICAL)` tags to genuine
    safety/isolation gates with one-line reasons.

#### 2. `skills/egm-bootstrap/SKILL.md`, `skills/egm-brainstorm/SKILL.md`, `skills/egm-draft/SKILL.md`, `skills/egm-review/SKILL.md` (Modify)

*   **Type / Scope**: Core Skill Definitions
*   **Proposed Changes**: Remove `(CRITICAL)` from section headings and routine
    constraints, retaining `CRITICAL` only on 2–3 real gates per skill with
    one-line rationales; remove `Banned Apologies`; replace `ask_question`
    batching choreography with plain-language single-question intent.

#### 3. `docs/harnesses.md` (Modify)

*   **Type / Scope**: Harness Integration Reference
*   **Proposed Changes**: Add a concise note covering structured question tool
    behavior (single-question turn-yielding) for harnesses that require it.

#### 4. `skills/egm-*/test_scenarios.yaml` & `tests/unit/` (Verify / Modify if needed)

*   **Type / Scope**: Unit Tests & Scenario Definitions
*   **Proposed Changes**: Ensure no unit test or scenario assertion depends on
    removed `"Banned Apologies"` or `len(questions) == 1` literal strings.

### Verification Plan

*   **Unit Tests**: `uv run --no-project --with pytest --with pyyaml pytest tests/unit`
*   **Packaging & Frontmatter Checks**: Verified via `tests/unit/test_packaging.py`,
    `tests/unit/test_frontmatter.py`, and `tests/unit/test_scenario_coverage.py`.
*   **Site Docs Check**: `npm --prefix site run check:docs` (if `docs/` links
    or pages are modified in Stage 2).

--------------------------------------------------------------------------------

*Drafted with EGM*
