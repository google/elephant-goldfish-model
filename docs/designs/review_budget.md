# Review Run Invocation Budget

Status: Draft (Stage 1 Design Doc for [#528](https://github.com/google/elephant-goldfish-model/issues/528)).
Date: 2026-11-28.

Related issues: [#528](https://github.com/google/elephant-goldfish-model/issues/528), [#385](https://github.com/google/elephant-goldfish-model/issues/385), [#105](https://github.com/google/elephant-goldfish-model/issues/105).

## Problem Statement & Motivation

A full Goldfish review (running isolated, fresh-context reviewer subagents)
consumes multiple reviewer calls and model quota. In
[TESTING.md](../../TESTING.md), the recorded Claude Cowork run (`Opus 5.5 Medium`,
2026-10-22) was interrupted by a usage limit during Stage 8, leaving final
artifacts, Stage 9, and child-isolation output unverified
([#105](https://github.com/google/elephant-goldfish-model/issues/105)).

Today, [`egm-review`](../../skills/egm-review/SKILL.md) and
[`egm-review-loop`](../../skills/egm-review-loop/SKILL.md) bound loop rounds (a
5-round cap in `egm-review-loop` and max 1 re-audit per stage in `egm-review`),
and retry a failed reviewer once, but neither skill caps total reviewer
subagent invocations across a run. Without an explicit invocation budget:

*   A multi-stage review (`egm-review` Stages 5–9: Initial Zoom Out,
    Comprehension, Critic, Intermediate Zoom Out, and Implementation Readiness)
    dispatches up to 10 single-pass reviewer calls before retries or loop
    iterations, which can exhaust subscription quota mid-run.
*   Users have no predictable internal stopping boundary or accounting of
    completed versus pending reviewers when they want to bound a run's size.

## Goals vs. Non-Goals

### Goals (In Scope)

*   Introduce one explicit cap (`MaxInvocations`) on reviewer subagent
    invocations per review run, displayed to the user before dispatch.
*   Define deterministic accounting for initial dispatches, retries, parallel
    batches, and `egm-review` to `egm-review-loop` handoffs against
    `MaxInvocations`.
*   When `MaxInvocations` blocks a required reviewer (initial, retry, or next
    convergence round), stop dispatching further reviewer calls and report
    completed and pending work using existing `not run` status conventions.
*   Preserve fresh reviewer context (Goldfish isolation) and all required human
    checkpoints.
*   Verify both a run that completes within its budget and a run that hits
    `MaxInvocations`.

### Non-Goals (Out of Scope)

*   Dollar budgets, token budgets, model pricing, or usage/duration
    documentation (owned by [#385](https://github.com/google/elephant-goldfish-model/issues/385)).
*   Changing reviewer selection, document standards, or Goldfish fresh-context
    isolation rules; a required reviewer blocked by the cap leaves the run
    incomplete rather than falling back to in-context review.
*   Automatic host quota polling or cross-run persistent budget tracking.
*   Modifying `skills/` or `agents/` in this Stage 1 Design Doc PR.

## Design Overview

### 1. Explicit Invocation Cap (`MaxInvocations`)

Add an optional positive integer input `MaxInvocations` (unbounded when omitted)
to both `egm-review` and `egm-review-loop`:

*   **Input validation**: Reject non-integer or non-positive values (`<= 0`)
    before dispatch with a usage error.
*   **Pre-dispatch display**: Before spawning the first reviewer subagent,
    display the selected cap alongside the planned stages and reviewers for the
    chosen preset (`interactive`, `uninterrupted`, `feature_spec`,
    `implementation`, or an individual stage). If `MaxInvocations` is smaller
    than the minimum required reviewers for the selected preset, warn the user
    before dispatch: in interactive modes, ask whether to proceed or raise
    `MaxInvocations`; in `uninterrupted` or headless mode, record the warning and
    proceed until `MaxInvocations` is reached.
*   **Scope of the counter**: Every Goldfish reviewer subagent call (`egm-zoom-out`,
    `egm-inventive-catalyst`, `egm-comprehension`, `egm-design`,
    `egm-structural`, `egm-style`, `egm-implementation-readiness`,
    `egm-codebase-details`) consumes `1` from `MaxInvocations`. Parent
    orchestrator turns (the persistent **Elephant** context) and in-thread
    finding resolution (`egm-resolve`) do not consume reviewer invocations.
*   **Single-owner accounting via direct dispatch**: When `MaxInvocations` is
    set, both `egm-review` and `egm-review-loop` use direct subagent dispatch
    (already supported by both skills) rather than delegating through
    [`agents/synthesizer.md`](../../agents/synthesizer.md), and disable optional
    dual-instance (`A`/`B`) reviewer spawning. This keeps invocation counting in
    one place in the parent orchestrator.
*   **Cross-skill handoff**: When `egm-review` invokes `egm-review-loop`
    in-thread for Stage 7 (Critic Review) or Stage 9 (Implementation Readiness),
    it passes the remaining budget and receives the updated remaining budget
    when `egm-review-loop` exits.
*   **Parallel batch ordering**: Before launching a stage's parallel batch of
    `N` reviewers, if fewer than `N` invocations remain, dispatch only as many
    reviewers as remain in the stage's listed order (for example,
    `[egm-design, egm-structural, egm-style]` in Stage 7) and mark the rest as
    `not run (budget exhausted)`.

### 2. Retry & Loop Accounting

Under current rules, a failed or timed-out reviewer is retried once, and
`egm-review-loop` requires two consecutive clean rounds to converge:

*   **Initial dispatch**: Consumes `1` invocation before spawning.
*   **Retry**: Consumes `1` invocation before spawning. If no invocations remain
    when a retry is needed, skip the retry, mark that reviewer as
    `not run (budget exhausted)`, and trigger the incomplete-run stop below.
*   **Inter-round exhaustion**: If the budget reaches `0` between
    `egm-review-loop` rounds before achieving two consecutive clean rounds, do
    not start the next round; halt the run as incomplete.

### 3. Incomplete-Run Behavior & Reporting

If the invocation budget reaches `0` while any required reviewer, retry,
convergence round, or subsequent stage in the selected preset remains pending:

1.  **Zero further reviewer calls**: Stop dispatching new reviewer subagents
    and retries. Do not fall back to reviewing in the parent Elephant context.
2.  **Preserve human checkpoints**: In interactive modes, do not skip or
    auto-approve pending human gates. If findings were already collected in the
    current stage, `egm-resolve` may still run in-thread (at zero reviewer
    invocations) before presenting the checkpoint or concluding.
3.  **Reuse `not run` status & report budget**: Record blocked reviewers in the
    existing `Failed Reviewers` / `Reviewer Status` section of the active stage
    report (or `goldfish_review_report.md` for standalone `egm-review-loop`, and
    `consolidated_review_report.md` for `uninterrupted` runs) as
    `<name>: not run (budget exhausted)`. Add one summary line
    `Invocation budget: <used> / <MaxInvocations> (incomplete — pending: <stages/reviewers>)`
    so completed and pending work are explicit without introducing a separate
    report schema.

## Alternatives Considered

*   **Per-stage caps instead of one run-level cap**: Bounding each stage
    separately would require users to configure up to five numbers and would not
    prevent total run cost from growing across retries and `egm-review-loop`
    rounds. A single `MaxInvocations` cap is simpler to set and reason about.
*   **Reserving retry slots up front**: Holding back `1` retry slot per reviewer
    from the usable budget would block normal reviewers early even when no
    reviewer fails. A shared pool lets healthy runs finish more stages while
    still capping total calls.
*   **Delegating budget tracking to `egm-synthesizer`**: Passing remaining budget
    into `egm-synthesizer` would duplicate counting logic across two agent
    layers and complicate accounting if the synthesizer times out mid-batch.
    Using existing direct dispatch when `MaxInvocations` is set keeps one
    authoritative counter.

## Risks & Mitigations

*   **Prompt-enforced counter drift**: Because skill instructions are executed by
    an LLM orchestrator across turns, long multi-stage sessions could miscount.
    *Mitigation*: Keep one counter in the parent orchestrator, emit
    `Invocation budget: <used> / <MaxInvocations>` in each stage summary, and
    avoid delegating counting to `egm-synthesizer`.
*   **Partial-stage or unverified coverage**: Stopping mid-stage leaves some
    review lenses unrun, which could be mistaken for a clean pass.
    *Mitigation*: Reuse `not run (budget exhausted)`—existing `egm-review-loop`
    rules already treat any `not run` reviewer as making a round not clean—and
    list pending stages/reviewers in the summary line.
*   **External host quota interruption**: `MaxInvocations` only stops runs that
    reach the configured internal cap; an external host quota abort can still
    interrupt mid-run before a final summary is written.
    *Mitigation*: Write each stage report as soon as its reviewers return so
    completed stage artifacts persist on disk.

## Verification Plan (Stage 2)

When implementing this design in Stage 2:

1.  **Scenario definitions**: Add scenarios in
    [`skills/egm-review/test_scenarios.yaml`](../../skills/egm-review/test_scenarios.yaml)
    and
    [`skills/egm-review-loop/test_scenarios.yaml`](../../skills/egm-review-loop/test_scenarios.yaml)
    covering pre-dispatch budget display, retry counting, parallel batch
    truncation, and stopping on cap.
2.  **Within-budget run**: Execute a review with `MaxInvocations` set above
    the required reviewer count and confirm normal completion, full reports, and
    accurate `<used> / <MaxInvocations>` accounting.
3.  **Budget-exhausted run**: Execute a review with `MaxInvocations` set below
    the required reviewer count (for example, `MaxInvocations: 2` on a 3-reviewer
    stage or full preset) and verify:
    *   No more than `MaxInvocations` reviewer subagent calls are made.
    *   The run halts without falling back to in-context review.
    *   The output report records completed reviewers, marks blocked reviewers
        `not run (budget exhausted)`, and names pending stages/reviewers.
