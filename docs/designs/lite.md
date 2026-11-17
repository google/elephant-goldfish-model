# EGM-Lite: Rapid Ad-Hoc Engineering Protocol

*   **Author:** Jonathan Njeunje ([@njeunje](https://github.com/njeunje))
*   **Status:** Proposed
*   **Date:** 2026-11-10

--------------------------------------------------------------------------------

## Overview

**EGM-Lite** (`/egm-lite`) adapts the Elephant-Goldfish Model (EGM) for small, rapid iterations,
specification revisions, code refactors, and bug fixes without requiring a full multi-document lifecycle. It enforces
a decoupled 5-phase state machine with explicit **Elephant and Goldfish persona switching**:
**Phase 1: Critique Pause** (Elephant (Critic)), **Phase 2: Lightweight Execution Checklist**
(Elephant (Planner)) followed by a **Spec Review** (Goldfish (Specification Reviewer via
Subagent)) that the user can skip, **Phase 3: Scope-Contained Execution** (Elephant (Builder)),
**Phase 4: Adversarial Diff Review** (Goldfish (Reviewer via Subagent)), and **Phase 5:
Post-Review Resolution Gate** (Elephant (Resolver)).

## The Problem

Executing the full EGM lifecycle (`/egm-brainstorm` -> `/egm-draft` -> `/egm-review`) for small
changes introduces unnecessary process overhead. Conversely, unconstrained agent execution defaults
to:

1.  Ungrounded code edits without verifying upstream contracts.
2.  Speculative abstractions and out-of-scope refactoring (YAGNI).
3.  Self-validation masking edge cases and regressions.

EGM-Lite provides an on-rails middle ground with isolated verification gates and fast turnaround.

## Non-Goals

- Replace the full EGM design lifecycle for architectural changes.
- Perform a same-context review when an isolated reviewer is unavailable.
- Expand implementation beyond the approved checklist or make review mandatory.

## System Architecture & Decoupled State Machine

Transitions between phases occur strictly upon explicit user command triggers and asynchronous
subagent completion:

*   **Code References & IDE Navigation**: All phases link referenced local files, symbols, and
    line ranges using clickable links, and cite external contracts via symbol or definition queries.
*   **Plain-English `> **BLUF:**` Blockquotes**: Phases that require a `> **BLUF:**` open with a
    concise single-paragraph blockquote (followed by `---`) stating the plain-English takeaway and
    recommended action without raw IDs, code literals, or line links.
*   **Decoupled Phase Triggers**: Transitions occur strictly on user commands.
    Phase 1 leads only to the checklist. From the checklist, developers can fast-path to
    Phase 3 (`exec`) without a spec review and review the result afterwards. The Phase 2B spec
    review and the Phase 4 diff review (`review` / `goldfish`) are Goldfish reviews that the
    user can skip; neither is mandatory.
*   **Adaptive Gating**: Phase 2A checks the checklist against fixed complexity criteria and
    recommends the spec review for non-trivial changes or direct execution for routine ones.
    The developer chooses; the recommendation never adds a mandatory step.
*   **Command Routing & State Advisory**: `review` and `goldfish` are aliases bound to the most
    recently completed phase. After Phase 2A or Phase 5 spec triage they start the Phase 2B spec
    review. After Phase 3 or Phase 5 diff triage, or with no task in progress on an existing
    diff, they start the Phase 4 diff review. An out-of-order command (a review with nothing to
    review, or a spec review before a checklist exists) returns a `> **BLUF:**` state advisory
    that names the valid next command.
*   **Subagent Integrity Guard**: Phases 2B and 4 require an isolated, fresh-context subagent
    tool (`invoke_subagent`). In single-agent environments without subagent capabilities,
    the protocol halts and informs the developer rather than executing a biased, same-context
    self-review.
*   **Non-Sycophantic Posture**: All phases lead with technical risks, trade-offs, or defects and
    forbid flattering adjectives or polite apologies.

```mermaid
flowchart TD
    Start(["/egm-lite &lt;task&gt;"]) --> CritiquePause
    CritiquePause["Phase 1: Critique Pause<br/><i>(Elephant Critic)</i>"]

    CritiquePause -->|"checklist"| ChecklistPhase

    subgraph SpecStage ["Specification & Planning (Adaptive Gating)"]
        direction TB
        ChecklistPhase["Phase 2A: Checklist<br/><i>(Elephant Planner)</i>"]
        SpecReview["Phase 2B: Spec Review<br/><i>(Goldfish Subagent)</i>"]
        SpecResolution["Phase 5: Spec Triage<br/><i>(Elephant Resolver)</i>"]

        ChecklistPhase -->|"review / goldfish"| SpecReview
        SpecReview -->|"Findings / LGTM"| SpecResolution
        SpecResolution -->|"checklist"| ChecklistPhase
        SpecResolution -->|"review / goldfish"| SpecReview
    end

    subgraph DiffStage ["Implementation & Diff Review"]
        direction TB
        ExecPhase["Phase 3: Scope-Contained Execution<br/><i>(Elephant Builder)</i>"]
        DiffReview["Phase 4: Adversarial Diff Review<br/><i>(Goldfish Subagent)</i>"]
        DiffResolution["Phase 5: Diff Triage<br/><i>(Elephant Resolver)</i>"]

        ExecPhase -->|"review / goldfish"| DiffReview
        DiffReview -->|"Findings / LGTM"| DiffResolution
        DiffResolution -->|"exec"| ExecPhase
    end

    ChecklistPhase -->|"exec / Proceed"| ExecPhase
    SpecResolution -->|"exec / Proceed"| ExecPhase
    DiffResolution -->|"checklist"| ChecklistPhase
    DiffResolution -->|"LGTM, or all findings contested"| Done(["Complete"])
    ExecPhase -->|"no review requested"| Done
    ExistingDiff(["review / goldfish on an existing diff"]) --> DiffReview
```

### Phase 1: Critique Pause (`/egm-lite`)

*   **Persona**: Elephant (Critic) — Adversarial, skeptical. It works with the full conversation
    context, so it is an Elephant; the zero-context Goldfish reviews run in Phases 2B and 4.
*   **Grounding & BLUF**: Probes target files, direct callers or tests, any existing directory
    `README.md` or user-cited doc, and repository definitions before proposing solutions, leading
    with a `> **BLUF:**` on whether the approach is ready for `checklist` or blocked.
*   **Contract Tracking**: Tags assumptions as `[⚠️ UNVERIFIED]` (untested contracts) or `[⏳ ACK]`
    (scheduled for empirical test).
*   **Alternatives Considered**: When multiple viable approaches exist, documents trade-offs in
    `egm_lite_alternatives.md` (led by a `> **BLUF:**` on the recommended option and trade-off)
    and links the artifact in chat without inline discussion (omitting it for trivial or single-path
    tasks).
*   **Completion Gate**: Halts execution; awaits the `checklist` command. An `exec`, `review` or
    `goldfish` command at this point returns a state advisory directing the user to generate a
    checklist first.

### Phase 2: Lightweight Execution Checklist & Spec Review

#### Phase 2A: Checklist Generation (`checklist`)

*   **Persona**: Elephant (Planner) — Structured, methodical.
*   **Artifact Generation**: Writes or updates `egm_lite_checklist.md` structured
    into three canonical sections:
    1.  *Targets & Tasks*: Ordered checklist items as GFM checkboxes (`- [ ]`) linking
        exact file paths and line ranges or tooling commands with brief rationales.
    2.  *Pre-Review Exclusions*: Explicitly agreed scope boundaries suppressed from
        review.
    3.  *Accepted CONTEST Rationales*: Settled false-positive findings retained across
        iteration loops to prevent redundant review flags.
*   **Spec Gating (Adaptive Gating)**: Evaluates the checklist against fixed complexity criteria
    (two or more production code files, async/concurrency, public APIs, or `[⚠️ UNVERIFIED]` /
    `[⏳ ACK]` tags) and opens the gate with a `> **BLUF:**` that recommends the spec review
    (`goldfish` or `review`) for non-trivial tasks, or says direct execution (`exec`) is
    reasonable for routine fixes and doc-only edits.
*   **Completion Gate**: Offers both commands in every case and halts execution until the user
    types `goldfish` / `review` or clicks **Proceed** / types `exec`.

#### Phase 2B: Stateless Spec Review (`goldfish` / `review`)

*   **Persona**: Goldfish (Specification Reviewer via Subagent) — Isolated, zero-context auditor.
*   **Subagent Isolation**: Spawns an isolated subagent (role "Goldfish Specification
    Reviewer") and injects the full markdown content of `egm_lite_checklist.md` into its prompt.
    On a re-review from Phase 5, first updates the checklist with the agreed revisions. If no
    fresh-context subagent tool is available, stops and offers `exec` / **Proceed** on the
    checklist instead.
*   **Spec Review Rubric**: Enforces a strictly binary output contract (`[✅ LGTM]` on zero
    findings) across four dimensions, skipping pre-review exclusions and accepted `CONTEST`
    rationales and forbidding AST or code-diff checks, since nothing is implemented yet:
    1.  *Scope Containment & YAGNI*: Targets stay within the task and add no unrequested
        abstractions.
    2.  *Contract & Invariant Tagging*: External dependencies and untested boundaries carry
        `[⚠️ UNVERIFIED]` or `[⏳ ACK]`.
    3.  *Edge Cases & Failure Modes*: Error handling, timeouts, and boundary conditions are
        mapped.
    4.  *Test Plan Actionability*: Test targets or empirical validation steps are concrete and
        runnable.
*   **Completion Gate**: Halts execution after spawning the subagent and awaits its asynchronous
    response.

### Phase 3: Scope-Contained Execution (`exec`)

*   **Persona**: Elephant (Builder) — Focused implementer.
*   **Artifact Initialization**: After a completed checklist or a verified specification (from
    Phase 2A, Phase 2B, or a Phase 5 spec LGTM), reads `egm_lite_checklist.md` directly without
    re-creating it. On the fast path from Phase 5 with agreed revisions or fixes, first creates
    or updates `egm_lite_checklist.md` before modifying any file or running commands.
*   **Boundary Enforcement**: Applies any inline comments left on `egm_lite_checklist.md` and
    executes only approved items and targets in the checklist, across code, specifications, or
    design documents; zero speculative logic.
*   **Code Standards**: Adds inline comments on non-obvious or complex logic blocks.
*   **Test Verification & Self-Repair**: Runs local tests covering affected targets with autonomous
    monotonic convergence (not applicable, or a linter, for doc-only edits).
*   **Checklist Progress**: Updates `egm_lite_checklist.md` marking completed tasks with `- [x]`
    after test verification passes, leading with a `> **BLUF:**` on escalation halts, autonomous
    self-repairs, or multi-file summaries while omitting it on clean single-target runs.
*   **Completion Gate**: Prompts for `review` or `goldfish` and halts execution with a strict
    negative constraint forbidding subsequent phases until triggered. The diff review is a Goldfish
    review that the user can skip: the gate recommends it whenever Phase 3 edited files, and the
    user can end the task without it.

### Phase 4: Adversarial Diff Review (`review` / `goldfish`)

*   **Persona**: Goldfish (Reviewer via Subagent) — Isolated, zero-context auditor.
*   **Entry**: Runs after Phase 3 or Phase 5 diff triage, or with no task in progress on an
    existing diff (workspace changes, or a diff or pull request the user supplies). With nothing
    to review it returns a state advisory.
*   **Subagent Isolation**: Evaluates the clean VCS diff against the checklist in a fresh subagent
    context, spawned as "Goldfish Reviewer" (`invoke_subagent`, `Agent`, or `spawn_agent`,
    stopping if no fresh-context subagent tool is available), with zero conversational bias,
    skipping pre-review exclusions and accepted `CONTEST` rationales recorded in the checklist
    and suppressing stylistic nitpicks.
*   **Diff Review Rubric**: Enforces a strictly binary output contract (findings only vs.
    explicit `[✅ LGTM]` on zero findings) across five dimensions. For doc-only diffs, the first
    three are replaced by checks for factual consistency against the approved checklist, clarity,
    link hygiene, and markdown line length:
    1.  *Thread & State Safety*: Race conditions, deadlocks, async mutations.
    2.  *Boundary Conditions*: Null checks, off-by-one, unhandled errors.
    3.  *Test Coverage & Regression Audit*: Unit test coverage of all new branches.
    4.  *YAGNI Audit*: Pruning unneeded abstractions.
    5.  *Contract & Tag Audit*: Verification that `[⚠️ UNVERIFIED]` and `[⏳ ACK]` tags are tested
        and removed.
*   **Completion Gate**: Halts execution after spawning the subagent and awaits its asynchronous
    response.

### Phase 5: Unified Post-Review Resolution Gate (Subagent Response)

*   **Persona**: Elephant (Resolver) — Contextual triage.
*   **Response Routing**: Uses the phase that spawned the review (Phase 2B or Phase 4,
    identified by the subagent role) to decide whether it is handling a spec review or a diff
    review response.
*   **Strict Non-Mutating Triage**: The Elephant Resolver operates strictly in
    read-only presentation mode and is forbidden from modifying application source files
    during triage. Approved fixes are staged into `egm_lite_checklist.md` to be executed
    under a subsequent `exec` or `checklist` turn.
*   **Finding Triage (`PROPOSE FIX` vs. `CONTEST`)**: Cross-references subagent findings against the
    codebase or spec without making code edits or running VCS mutations, opening with a
    `> **BLUF:**` led by
    **`[🛠️ X FIX | 🛡️ Y CONTEST]`** before presenting numbered and priority-tagged items
    (`[X] [PY]`, e.g., `[1] [P0]`, `[2] [P0]`, `[3] [P3]`) in a structured bullet list or compact
    comparison table sorted within each group in descending severity order
    (`P0` > `P1` > `P2` > `P3`, regardless of tier gaps), grouping `PROPOSE FIX` patches ahead of
    codebase-backed `CONTEST` false alarms (bypassed by default).
*   **Completion & Synchronization Gate**:
    *   *Pre-Implementation (Spec Review)*: A clean pass, or the user confirming that all findings
        are contested or dismissed, stamps the checklist `Verified [✅ LGTM]` and prompts for
        `exec` / **Proceed**. It never closes the task. Remaining findings prompt for `checklist`
        to revise, `exec` to implement, or `goldfish` / `review` to re-review.
    *   *Post-Implementation (Diff Review)*: A clean pass, or the user confirming that all
        findings are contested or dismissed, opens with a `> **BLUF:**` led by **`[✅ LGTM]`** and
        summarizes modified files and passing tests; otherwise prompts `checklist` (or fast-path
        `exec`) if flaws remain.

## Implementation Files

The EGM-Lite capability is implemented across the following package files:

| File Path | Type | Purpose & Reason for Existence |
| :-------- | :--- | :----------------------------- |
| `skills/egm-lite/SKILL.md` | Skill Definition | Implements the decoupled 5-phase state machine with Adaptive Gating (`/egm-lite` -> `checklist` -> spec review (the user can skip it) -> `exec` -> `review` -> resolution). |
| `skills/egm-lite/agents/openai.yaml` | Host Metadata | Declares extension interface, display names, and brand styling for OpenAI/Codex. |
| `skills/egm-lite/assets/icon.svg` | Vector Artwork | Self-contained 24x24 dual-facet icon (Spark) adhering to the EGM design system. |
| `skills/egm-lite/TEST.md` | Unit Tests | Verification test scenarios testing decoupled phase gating and persona switching. |
| `skills/egm-lite/test_scenarios.yaml` | Evaluation Benchmark | Benchmark test suite evaluating model adherence to the 5-phase EGM-Lite protocol. |

### Verification Plan

The EGM-Lite protocol is validated through deterministic behavioral evaluation
suites (`skills/egm-lite/test_scenarios.yaml`), protocol checklists
(`skills/egm-lite/TEST.md`), and unit tests (`pytest tests/unit`).

Verification enforces six core behavioral invariants:

1.  **State Machine & Pause Gating (Phases 1 & 2):** Asserts that mutating operations
    pause for user confirmation (`checklist`, then `exec` or **Proceed**),
    `egm_lite_checklist.md` is initialized with GFM checkboxes, and competing
    architectures are recorded in `egm_lite_alternatives.md`.
2.  **Scope-Contained Execution & Convergence (Phase 3):** Verifies that code edits
    stay strictly within approved checklist items, local tests execute with
    autonomous monotonic convergence, and completed tasks are marked `- [x]`.
3.  **Fresh-Context Subagent Isolation (Phase 4):** Enforces true context separation
    via a fresh-context subagent tool (`invoke_subagent`), refusing same-context
    Goldfish reviews and skipping user-agreed pre-review exclusions.
4.  **Binary Review Contract (Phase 4):** Asserts that any defect strictly suppresses
    LGTM and outputs prioritized findings (`P0`–`P3`), while clean passes lead with
    an explicit `> **BLUF:**` with `[✅ LGTM]`.
5.  **Post-Review Triage & Synchronization (Phase 5):** Validates presentation-only
    triage (`[🛠️ X FIX | 🛡️ Y CONTEST]`), persistence of `CONTEST` rationales in the
    checklist, and loop closure.
6.  **Adaptive Gating & Command Routing (Phases 2A, 2B & 5):** Asserts that Phase 2A
    offers both `exec` and `goldfish` / `review` with a recommendation for non-trivial
    changes, the spec review subagent receives the checklist and the Spec Review Rubric,
    a spec LGTM prompts for `exec` without closing the task, and an out-of-order command
    returns a state advisory.

#### Test Execution

```bash
# Run unit tests, packaging validation, and harness discovery
pytest tests/unit

# Validate markdown link integrity
pytest tests/unit/test_link_integrity.py
```

## References

*   [EGM Framework Architecture](architecture.md)
*   [EGM Goldfish Review Protocol & Resolution Engine](review.md)
*   [EGM Design Drafting](draft.md)
*   [Shared Skill Icons](skill_icons.md)
*   [Testing Guidelines](../../TESTING.md)
