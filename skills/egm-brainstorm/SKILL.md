---
name: egm-brainstorm
license: Apache-2.0
disable-model-invocation: true
description: >-
  Interactive ideation and brainstorming skill for the Elephant &
  Goldfish Model (EGM). Helps turn half-baked concepts into structured
  hypotheses via clarifying questions, review, and iterative refinement.
  Produces an RFC summary for human review or more detailed design with
  egm-draft.
---

# EGM Brainstorm: Interactive Multi-Lens Ideation & Refinement

When running in Codex or ChatGPT Work, first read [Codex integration](../../docs/codex.md).
In Claude Code or Cowork, read `${CLAUDE_PLUGIN_ROOT}/docs/claude.md` first.

Turns rough ideas into stress-tested hypotheses by combining multi-turn clarifying questions with parallel Goldfish review, outputting an RFC brief (`concepts_brief.md`) for human feedback or `egm-draft`.

## Execution Constraints (CRITICAL)

1.  Read and apply `resources/execution_instructions.md` (Shared Execution Constraints and Subagent Delegation; write briefs to `./concepts_brief.md` or the artifact directory rather than chat, use direct plain English, critique weaknesses before merits without flattering adjectives or apologies, and stop if no subagent tool exists because same-context review is not a Goldfish review).
2.  **Multi-Turn Open-Ended Discovery**: Drill down via open-ended plain-text questions across turns until problem, users, and constraints are clear. Never use `ask_question` or offer multiple-choice menus/options during discovery, and never spawn subagents before the Step 1 Readiness Gate confirms readiness.
3.  **Parallel Goldfish Reviews**: Evaluate the concept simultaneously across all 7 lenses below.
4.  **Interaction Invariants**: Every modal gate MUST contain one question (`len(questions) == 1`), set `is_multi_select: false`, use no `(Recommended)` prefixes, and be the final tool call in the turn.

## The Goldfish Brainstorming Lenses

| Lens / Persona | Core Objective | Key Questions Challenged |
| :--- | :--- | :--- |
| **Contrarian / YAGNI** | Code & complexity minimization | *Why must this exist? Can an existing library, API, or service solve 90% without new code?* |
| **Cost, Quota & Token Economics** | Infra & budget scaling | *What are peak QPS, memory footprint, query load, or LLM token budgets at scale?* |
| **UX & Developer Ergonomics** | Usability & cognitive load | *Is the API/CLI intuitive, idiomatic, and clear on errors without developer friction?* |
| **Migration & Backward Compatibility** | Rollout & version skew | *How do clients/data migrate, handle schema skew, and roll back mid-migration?* |
| **Observability & SRE Debuggability** | Telemetry & triage | *Are operations traced and metered clearly enough for 3 AM incident triage?* |
| **Long-Term Tech Debt & Maintenance** | Future maintainability | *Does this create tight coupling or brittle state machines painful in 2 years?* |
| **Inventive Catalyst** | Contradiction elimination | *What false trade-off is accepted as inevitable, and what transform resolves it?* |

## Execution Workflow

### Step 1: Deep Clarification & Problem Statement Drilling

1.  **Concept & Author**: Ask what the user wants to build if missing. Resolve `Author` from `git config user.name`, then `GIT_AUTHOR_NAME`; if neither is set, ask the user in chat.
2.  **Iterative Open-Ended Drilling**: Ask targeted plain-text questions across turns (no structured question tools or multiple-choice options):
    *   *What specific problem or bottleneck does this solve?*
    *   *Who or what consumes this, under what SLAs/invariants?*
    *   *What are non-negotiable constraints (zero false positives, offline, platform)?*
    *   *What edge cases or out-of-scope boundaries apply?*
    *   *How is this handled today, and why does that fail? How is success measured?*
3.  **Readiness Gate (Single-Select)**: Once grounded, summarize the hypothesis in 2-3 sentences and ask (`is_multi_select: false`, no `(Recommended)`):
    *   `question`: `"Anchored feature hypothesis: [2-3 sentence summary]. How would you like to proceed?"`
    *   `options`: `["Review with Goldfishes", "Clarify additional constraints or assumptions in chat"]`
    *   **Option 0 (`Review with Goldfishes`)**: Proceed to Step 2.
    *   **Option 1 (`Clarify additional constraints or assumptions in chat`)**: Yield for user notes, update hypothesis, and re-present this gate.
4.  **Do NOT spawn subagents before Option 0 is confirmed.**

### Step 2: Goldfish Review & Synthesis

1.  **Spawn `egm-synthesizer`** (`agents/synthesizer.md`, or dispatch the 7 parallel lens subagents directly if nesting is unsupported) with prompt:
    `Conduct multi-lens brainstorm for feature concept: [AnchoredFeatureHypothesis]. Mode: BRAINSTORM. Reviewers: [egm-design, egm-codebase-details, egm-zoom-out, egm-comprehension, egm-implementation-readiness, egm-structural, egm-inventive-catalyst].`
2.  **Synthesize & Write Artifact**: Deduplicate findings (keep `"No false compromise detected"` and do not invent catalog patterns if `egm-inventive-catalyst` reports no contradiction) and write `concepts_brief.md` in the working or artifact directory:

```markdown
# [Feature Name]

* **Author:** [Author Name or GitHub Handle]
* **Date:** [YYYY-MM-DD]

## Overview

[Plain-English summary of feature, target user, and core value proposition.]

## Analysis

[Cohesive synthesis across review lenses: inventive contradictions, catalog pattern recommendations, secondary trade-offs, and Ideal Final Result (or "No false compromise detected").]

## Goals vs. Non-Goals

* **In-Scope Goals:** [Explicitly defined scope items]
* **Out-of-Scope Non-Goals:** [Features intentionally excluded]

## Alternatives Weighed

[Each rejected option with concrete rationale, e.g. "Rejected by author: <reason>". Never write "Rejected by maintainer" without a linked issue, discussion, or PR. egm-draft copies these directly.]

## Key Decisions & Staging for Next Steps

[Resolved decisions to carry forward into egm-draft.]
```

### Step 3: Interactive Iteration & Refinement Loop

Notify the user of `concepts_brief.md`'s path in chat (never dump the brief body), highlight 2-3 key reviewer objections or risks, ask how to address them, and iterate Steps 1-2 until aligned.

### Step 4: Finalize & Handoff

1.  Ask the user to confirm alignment on `concepts_brief.md`.
2.  Present the single-select Handoff Gate (`len(questions) == 1`, `is_multi_select: false`, no `(Recommended)`):
    *   `question`: `"Brainstorming complete. concepts_brief.md is finalized. Select next step:"`
    *   `options`:
        0. `"Publish concepts_brief.md as RFC for team feedback"` -> Write `docs/designs/<feature_name>.md` (and register in `docs/designs/SITEMAP.md` if present); instruct user to start `egm-draft` on it using the host's command form (`/egm:egm-draft docs/designs/<feature_name>.md` in Claude Code/agy CLI, or skill picker in Codex).
        1. `"Proceed to egm-draft (Initialize formal design document)"` -> Confirm `concepts_brief.md` is saved and tell user to start `egm-draft` using the host's command form (`/egm:egm-draft` in Claude Code/agy CLI, or skill picker in Codex), which ingests `concepts_brief.md` as Priority 1 context.
        2. `"Continue refining concepts_brief.md in ideation mode"` -> Return to Step 3.
        3. `"Conclude brainstorming and keep brief for later"` -> Wrap up cleanly, noting where `concepts_brief.md` is saved.
