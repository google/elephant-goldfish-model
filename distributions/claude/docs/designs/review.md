# EGM Goldfish Review Protocol & Resolution Engine

*   **Authors:** Brandon Tearse ([@tearseb](https://github.com/tearseb)), Brian Suchy ([@briansuchy](https://github.com/briansuchy)), Sean Stappas ([@seanstappas](https://github.com/seanstappas))
*   **Status:** Current
*   **Date:** 2026-06-10

--------------------------------------------------------------------------------

## Overview

The **Goldfish Review Protocol** is the verification engine of the Elephant &
Goldfish Model (EGM). It stress-tests draft design specifications using
isolated, zero-context AI subagents ("Goldfish") evaluating the document against
strict qualitative rubrics.

This document specifies:

1.  The multi-stage review pipeline (`/egm-review`).
2.  The review orchestration driver (`egm_review_loop`).
3.  The complete catalog of specialized reviewer personas.
4.  The mapping to document standards and evaluation rubrics
    (`resources/document_standards/`).
5.  The interactive resolution engine (`egm_resolve`).

## The Problem

Self-review by the authoring LLM suffers from severe confirmation bias. When the
same context window drafts and reviews a plan:

1.  **Blind Spots Persist**: The model assumes the context it holds in memory is
    obvious from the text, overlooking unstated assumptions and undefined terms.
2.  **Hallucination Masking**: Invalid API assumptions made during discussion go
    untested against actual source code.
3.  **Premature Implementation Approval**: Implementation plans lacking concrete
    file paths or test strategies are rubber-stamped without scrutiny.

The Goldfish model mitigates this by spawning fresh, stateless subagents that
read only the target document and explicitly referenced source files.

## Review Pipeline Architecture (`/egm-review`)

The full review pipeline executes five sequential evaluation phases:

```mermaid
flowchart TD
    Start([Target Design Doc]) --> Step5[Step 5: Zoom Out Review]
    Step5 --> Gate5{Pass / Abort?}
    Gate5 -- Abort --> FixArch[Refactor Architecture]
    Gate5 -- Pass --> Step6[Step 6: Comprehension Test]
    Step6 --> Gate6{Gaps Found?}
    Gate6 -- Yes --> UpdateContext[Clarify Definitions / Context]
    Gate6 -- No --> Step7[Step 7: Critic Review]
    Step7 --> Loop7[egm_review_loop: design_critic + structural + style]
    Loop7 --> Resolve7[egm_resolve]
    Resolve7 --> Step8[Step 8: Intermediate Zoom Out Review]
    Step8 --> Gate8{YAGNI / Bloat Found?}
    Gate8 -- Yes --> PruneBloat[Prune Defensive Over-Engineering]
    Gate8 -- No / Resolved --> Step9[Step 9: Implementation Readiness Test]
    Step9 --> Loop9[egm_review_loop: implementation_readiness + codebase_details + style]
    Loop9 --> Resolve9[egm_resolve]
    Resolve9 --> Done([Ready for Human Peer Review])
```

### Stage Breakdown

1.  **Step 5: Zoom Out Review (Altitude Check)**:
    *   *Target*: Full Document.
    *   *Persona*: [`zoom_out`](../../agents/zoom_out.md) (Skeptical Architect).
    *   *Standard*: `zoom-out-standard.md`.
    *   *Focus*: Validates problem framing, rejects speculative features
        (YAGNI), and verifies reuse of existing infrastructure before investing in
        detailed review passes.
2.  **Step 6: Comprehension Test (Self-Containment Check)**:
    *   *Target*: `FeatureRange` vs `DetailedRange`.
    *   *Persona*: [`comprehension`](../../agents/comprehension.md) (Naive Reader).
    *   *Standard*: Baseline Self-Containment.
    *   *Focus*: Reads the document with zero prior context. Identifies missing
        prerequisites, unexplained acronyms, and conceptual gaps.
3.  **Step 7: Critic Review (Antagonistic Stress-Test)**:
    *   *Target*: `FeatureRange` (High-Level Architecture).
    *   *Personas*: [`design_critic`](../../agents/design_critic.md),
        [`structural`](../../agents/structural.md), [`style`](../../agents/style.md).
    *   *Standards*: `feature-spec-standard.md`, `heilmeier-standard.md`.
    *   *Focus*: Probes single points of failure (SPOFs), scaling limits,
        failure modes, and edge cases.
4.  **Step 8: Intermediate Zoom Out Review (Post-Critic Pruning)**:
    *   *Target*: Full Document.
    *   *Persona*: [`zoom_out`](../../agents/zoom_out.md) (Skeptical Architect).
    *   *Standard*: `zoom-out-standard.md`.
    *   *Focus*: Incremental audit focusing on additions, modifications, and
        defensive mitigations introduced during Comprehension and Critic
        reviews. Purges speculative complexity and YAGNI elements before task
        planning, while avoiding re-flagging decisions accepted in Step 5.
5.  **Step 9: Implementation Readiness Test (Actionability Check)**:
    *   *Target*: `DetailedRange` (`## Detailed Implementation Plan`).
    *   *Personas*: [`implementation_readiness`](../../agents/implementation_readiness.md),
        [`codebase_details`](../../agents/codebase_details.md), [`style`](../../agents/style.md).
    *   *Standards*: `implementation-readiness-standard.md`, `re-implementation-standard.md`.
    *   *Focus*: Verifies that every file touched is listed with rationale, API
        signatures match current codebase reality, and step-by-step test plans exist.

--------------------------------------------------------------------------------

## Reviewer Persona Catalog

All reviewer persona prompts reside under [`agents/`](../../agents/):

| Persona File | Role Title | Core Responsibilities |
| :----------- | :--------- | :-------------------- |
| [`agents/zoom_out.md`](../../agents/zoom_out.md) | Skeptical Architect | Audits for over-engineering, YAGNI, and unneeded complexity. Searches codebase for existing utilities to prevent reinvention. |
| [`agents/comprehension.md`](../../agents/comprehension.md) | Naive Reader | Assumes no prior knowledge. Identifies undefined jargon, assumed system context, and missing architectural diagrams. |
| [`agents/design_critic.md`](../../agents/design_critic.md) | Analytical Design Critic | Evaluates system reliability, scale limits, operational risks, failure recovery, and trade-off justification. |
| [`agents/implementation_readiness.md`](../../agents/implementation_readiness.md) | Tech Lead Auditor | Ensures implementation plans contain unambiguous, deterministic instructions, complete file lists, and verification steps. |
| [`agents/codebase_details.md`](../../agents/codebase_details.md) | Codebase Auditor | Cross-references referenced paths, classes, and function signatures against live source code to prevent drift and hallucinated APIs. |
| [`agents/structural.md`](../../agents/structural.md) | Layout Validator | Enforces standard heading hierarchy, table formatting, and document template conformance. |
| [`agents/style.md`](../../agents/style.md) | Technical Copy Editor | Strips conversational filler, enforces factual, objective tone, and ensures adherence to concise technical writing standards. |
| [`agents/synthesizer.md`](../../agents/synthesizer.md) | Review Synthesizer | Spawns reviewers in parallel, deduplicates findings, formats file links, and writes consolidated report artifacts. |

--------------------------------------------------------------------------------

## Document Standards & Rubrics (`resources/document_standards/`)

Reviewers evaluate drafts against the versioned standards listed in the
[shared runtime resources](../../resources/README.md). Read the actual standard
for its requirements. The stage breakdown above maps each review to its
standards; it does not replace those rubrics.

--------------------------------------------------------------------------------

## The Interactive Resolution Engine (`egm_resolve`)

When Goldfish reviewers complete their audit, the **Elephant Resolution Engine**
ingests the flat findings list and manages interactive triage.

### 1. Evaluation & Categorization

For each finding, the Elephant determines:

*   **`PROPOSE FIX`**: The critique is valid. Generates exact replacement
    strings or structural edits.
*   **`CONTEST`**: The critique is invalid or based on a misunderstanding. Cites
    concrete codebase evidence defending the current text.

### 2. User Triage Modes

The engineer reviews `goldfish_review_report.md` via four interaction modes:

*   **Auto Accept**: Batch-applies all `PROPOSE FIX` suggestions and skips
    `CONTEST` items.
*   **Interactive Breakdown**: Sequential, item-by-item chat walkthrough with
    detailed explanations and overrule capabilities.
*   **Artifact Comments**: Inline comments on the artifact parsed and applied by
    the Elephant. (Recommended)
*   **Wildcard Requests**: Pauses the review to answer ad-hoc questions or run
    exploratory commands before resuming triage.

### 3. Iteration & Checkpoint Gating

After fixes are applied, the loop presents a mandatory checkpoint asking the
user whether to run another review pass or complete the workflow. The process
concludes when zero blocking findings remain or the engineer halts the loop.

## Implementation Files

| File Path | Type | Purpose & Reason for Existence |
| :-------- | :--- | :----------------------------- |
| `skills/egm_review/SKILL.md` | Skill Definition | Entry point orchestrating the multi-stage review pipeline (Zoom Out $\rightarrow$ Comprehension $\rightarrow$ Critic $\rightarrow$ Intermediate Zoom Out $\rightarrow$ Readiness). |
| `skills/egm_review/TEST.md` | Unit Tests | Verification test scenarios testing `/egm-review` multi-stage flow and checkpoint gating. |
| `skills/egm_review/test_scenarios.yaml` | Evaluation Benchmark | Benchmark test suite evaluating model review precision and recall. |
| `skills/egm_review_loop/SKILL.md` | Skill Definition | Central review driver managing asynchronous subagent spawning and findings collection. |
| `skills/egm_review_loop/TEST.md` | Unit Tests | Verification test scenarios testing goldfish review loop dispatch. |
| `skills/egm_review_loop/test_scenarios.yaml` | Evaluation Benchmark | Benchmark test suite evaluating goldfish review loop dispatch. |
| `skills/egm_resolve/SKILL.md` | Skill Definition | Elephant resolution engine managing `CONTEST` vs `PROPOSE FIX` triage and automated fixes. |
| `skills/egm_resolve/TEST.md` | Unit Tests | Verification test scenarios validating the finding categorization and resolution loop. |
| `skills/egm_resolve/test_scenarios.yaml` | Evaluation Benchmark | Benchmark test suite evaluating model resolution and fix proposal accuracy. |
| `agents/*.md` | Persona Prompts | System prompt instructions for all 7 Goldfish reviewers and the Synthesizer. |
| `resources/document_standards/*.md` | Document Standards | Evaluation rubrics and standards for feature specs, implementation readiness, and simplicity. |

## References

*   Dave Rensin, [Elephants, Goldfish, and the New Golden Age of Software Engineering](https://medium.com/@drensin/elephants-goldfish-and-the-new-golden-age-of-software-engineering-c33641a48874) (Medium, 2026).
*   DARPA, [The Heilmeier Catechism](https://www.darpa.mil/about/heilmeier-catechism).
