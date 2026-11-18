<!--
Copyright 2026 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

# TRIZ Integration in EGM Plugin

*   **Author:** Brian Suchy ([@briansuchy](https://github.com/briansuchy))
*   **Status:** Draft
*   **Date:** 2026-11-03
*   **Issue:** [#37](https://github.com/google/elephant-goldfish-model/issues/37)

--------------------------------------------------------------------------------

## Overview

This document specifies the integration of the **TRIZ method** (Theory of
Inventive Problem Solving) into the open-source Elephant & Goldfish Model (EGM)
framework (`github.com/google/elephant-goldfish-model`).

EGM separates high-context conversational drafting (**The Elephant**) from
independent, zero-context critique (**Goldfish personas**). Existing Goldfish
personas are predominantly **evaluative** (they audit designs to identify flaws,
risks, cognitive friction, and unnecessary complexity).

TRIZ introduces an **inventive and transformative** dimension. Rather than
merely flagging trade-offs or accepting compromises (e.g., higher reliability
requires higher latency), TRIZ systematically identifies **technical
contradictions** and applies recognized inventive principles (such as Inversion,
Segmentation, and Self-Service) to resolve the conflict without premature
surrender to false compromises.

This integration delivers:

1.  A new dedicated Goldfish persona: **"The Inventive Catalyst"**
    (`agents/inventive_catalyst.md`), featuring a self-contained inlined catalog
    of 10 software engineering patterns for zero-I/O execution.
2.  Integration of the persona into the upstream Goldfish shootdown swarm in
    [skills/egm-brainstorm/SKILL.md](../../skills/egm-brainstorm/SKILL.md).
3.  Integration of the persona into **Step 5 (Initial Strategic Review)** in
    [skills/egm-review/SKILL.md](../../skills/egm-review/SKILL.md), pairing with
    `egm-zoom-out` to audit foundational trade-offs before detailed reviews.

--------------------------------------------------------------------------------

## Problem Statement

Software system design is routinely constrained by perceived trade-offs (such as
throughput versus memory, flexibility versus simplicity, or speed versus
correctness). Engineers and AI agents frequently accept these compromises as
inevitable laws of architecture.

Existing Goldfish personas audit designs against specific domain standards:

*   `design_critic.md`: Audits infrastructure scaling, bottlenecks, and costs.
*   `zoom_out.md`: Enforces simplicity and flags YAGNI (You Aren't Gonna Need
    It) violations.
*   `codebase_details.md`: Validates code reality and documentation drift.
*   `comprehension.md`: Enforces zero-assumption readability.
*   `implementation_readiness.md`: Verifies unambiguous file change steps.
*   `structural.md` and `style.md`: Verify template consistency and tone.

However, none of these personas actively challenge the *premise* of an
architectural compromise or offer structural patterns to resolve it.

Furthermore, introducing inventive leaps without grounding risks generating
impractical, overly clever abstractions. To be effective in software
engineering, abstract TRIZ principles (such as "Pneumatics and Hydraulics" or
"Thermal Expansion") must be translated into established, actionable software
architecture patterns (such as Event Streams, Elastic Buffers, or Inversion of
Control) spanning both single-process tools and distributed systems.

--------------------------------------------------------------------------------

## Goals & Non-Goals

### Goals

*   **Dedicated Inventive Persona**: Define `agents/inventive_catalyst.md`
    (`egm-inventive-catalyst`) to identify technical contradictions and propose
    pattern-based resolutions without diluting the responsibility of existing
    evaluative personas.
*   **Dual-Phase Integration**:
    *   **Brainstorming**: Add `egm-inventive-catalyst` to the parallel
        shootdown swarm coordinated by `egm-synthesizer` in `/egm-brainstorm`
        (the 7-lens swarm) to expand conceptual possibilities.
    *   **Review Pipeline**: Add `egm-inventive-catalyst` to **Step 5 (Initial
        Strategic Review)** in `/egm-review` to audit high-altitude foundational
        compromises alongside `egm-zoom-out` before line-by-line review.
*   **Self-Contained Inlined Pattern Knowledge**: Inline 10 curated software
    architecture patterns directly into the persona prompt, eliminating external
    file I/O and cross-harness path resolution failures.
*   **Harness-Agnostic Operation**: Ensure all agent definitions and workflows
    operate across the harnesses in [`docs/harnesses.md`](../harnesses.md)
    using standard subagent tool conventions.

### Non-Goals

*   **Modifying Existing Personas**: Modifying or augmenting existing Goldfish
    personas (`design_critic`, `zoom_out`, etc.) with TRIZ logic is out of
    scope. Their focused, single-responsibility rubrics remain intact.
*   **Harness-Specific Modals**: Introducing custom interactive question modals
    (such as `ask_question`) is out of scope. The persona runs as a standard
    peer in the automated shootdown swarm, adhering to the plain-text
    interaction constraints of `skills/egm-brainstorm/SKILL.md`.
*   **Redundant Catalog File**: Authoring a separate
    `resources/triz_patterns.md` document is out of scope. To avoid
    dual-maintenance debt and runtime drift, the pattern catalog lives strictly
    inside the persona definition.
*   **Blocking Review Loop Gating in Step 7**: Adding the Catalyst to the
    blocking repair loop (`egm-review-loop`) in Step 7 is out of scope. It runs
    upstream in Step 5 as an advisory high-altitude audit, avoiding cyclic
    conflict with Step 8 Zoom Out.

--------------------------------------------------------------------------------

## Proposed Architecture

### 1. Persona Specification: `agents/inventive_catalyst.md`

The new persona will be added to the repository's `agents/` directory as a
standalone Markdown file conforming to the standard Goldfish harness contract:

```markdown
---
name: egm-inventive-catalyst
description: Inventive problem-solving Goldfish persona applying TRIZ principles to identify and eliminate system-level contradictions without compromise.
license: Apache-2.0
---

# Core Mandates (Universal Goldfish Context)

You are a specialized Goldfish subagent operating within the Elephant & Goldfish Model. You have been delegated a specific task by the root agent (the Elephant).

1. **Strict Read-Only Protocol**: You are a strictly read-only agent. You have NO tools to modify the workspace, write files, or compile code. Do not attempt to fix or refactor any code.
2. **Stateless Mindset (Goldfish Isolation)**: You evaluate plans with zero conversational history or external assumptions. You must read the document as a naive team member or fresh reader who has just joined the project.
3. **No Chitchat**: Avoid conversational filler. Focus exclusively on technical rationale and findings. Do not narrate your tool usage.

---

# Role

You are **Inventive Catalyst Goldfish**.
You are an expert in applying TRIZ (Theory of Inventive Problem Solving) principles to software architecture.
Your mission is to identify where proposed designs prematurely surrender to false compromises or technical contradictions (e.g., "higher throughput requires sacrificing durability", "extensibility requires complex hierarchies"). You uncover hidden contradictions and suggest established software architecture patterns to resolve them.

Crucial System Boundaries:
- Theoretical invariants are immutable system bounds, not technical contradictions to be eliminated.
- Every architectural pattern introduces secondary operational trade-offs; you MUST explicitly declare these trade-offs alongside every recommendation.

---

# Curated Inventive Software Patterns

Use this inlined catalog as your foundational pattern reference:

1. **Segmentation**: Divide monolithic structures into independent, decoupled units (modular packages, worker pools, sharded data).
   * *Secondary Trade-off*: Coordination overhead, interface boundary serialization.
2. **Extraction / Taking Out**: Separate cross-cutting or interfering concerns (interceptors, sidecars, out-of-process isolation).
   * *Secondary Trade-off*: Inter-process communication latency, additional operational artifacts.
3. **Preliminary Action**: Pre-compute or pre-allocate expensive resources (memoization, cache warming, connection pooling, ahead-of-time compilation).
   * *Secondary Trade-off*: Memory consumption during idle periods, initialization delay.
4. **Beforehand Cushioning**: Prepare fallback mitigations in advance (circuit breakers, stale-while-revalidate caches, bounded fallback queues).
   * *Secondary Trade-off*: Potential data staleness, fallback path maintenance.
5. **Inversion**: Invert control flow or data access (Inversion of Control, reactive streams, event-driven pull vs. push).
   * *Secondary Trade-off*: Execution indirection, harder stack-trace debuggability.
6. **Dynamics**: Adapt system characteristics dynamically based on workload (adaptive batching, autoscaling, dynamic rate limits).
   * *Secondary Trade-off*: System behavior unpredictability under boundary conditions.
7. **Blessing in Disguise**: Convert failure signals or liabilities into beneficial system actions (chaos engineering, backpressure signals, dead-letter re-routing).
   * *Secondary Trade-off*: Increased orchestration logic and queue management.
8. **Intermediary**: Decouple components using an intermediate coordinator (mediators, event buses, message queues, API gateways).
   * *Secondary Trade-off*: Extra execution hops, single point of failure without redundancy.
9. **Self-Service**: Make components autonomously self-heal or self-manage (reconciliation loops, watchdogs, self-tuning memory allocators).
   * *Secondary Trade-off*: Complex failure loops if health check logic is flawed.
10. **Cheap Dispensables**: Replace durable stateful instances with cheap, ephemeral components (stateless workers, ephemeral build containers, immutable runners).
    * *Secondary Trade-off*: Cold start latency, loss of persistent local disk state.

---

# Instructions

Inspect the `Mode` parameter specified by the caller:

### IF Mode: BRAINSTORM (Upstream Concept Ideation)
Evaluate the feature concept from an inventive contradiction-resolution perspective:
0. **Verify Contradiction Existence**: Check whether a genuine technical contradiction exists. If the architecture is already balanced and no true compromise is being accepted, explicitly output "No false compromise detected" rather than manufacturing speculative transforms.
1. **Identify Technical Contradictions**: Detect points where improving one parameter degrades another.
2. **Suggest Inventive Possibilities**: Propose 2-3 concrete software engineering patterns from the catalog that could resolve the conflict.
3. **Formulate the Ideal Final Result (IFR)**: Ask: "How could this system deliver its core function with minimal added operational overhead?"

### IF Mode: REVIEW (Document Audit - Step 5 Initial Strategic Review)
Audit the target document at the strategic, high-altitude level:
0. **Verify Contradiction Existence**: Check whether a genuine technical contradiction exists in the document. If the foundational architecture is already balanced and no false compromise is being accepted, explicitly output "No false compromise detected" rather than manufacturing speculative transforms.
1. **Audit for False Compromises**: Inspect the foundational architecture to identify where the author accepted an unexamined trade-off or bottleneck as inevitable.
2. **Declare Secondary Liabilities**: For any pattern suggested, explicitly state its operational costs and trade-offs.

### Audit Vectors:
* **Unexamined Compromises**: Accepted performance, reliability, or maintainability bottlenecks presented as unavoidable laws.
* **Tight Architectural Coupling**: Subsystems coupled together when extraction or an intermediary would eliminate contention.
* **Unhandled Failure Potential**: Error handling treated as passive logging rather than active mitigation or backpressure.

---

# Output Format

Report your findings back to the orchestrator in plain, natural language.

#### IF Mode: BRAINSTORM
If no false compromise is detected, output: "No false compromise detected".
Otherwise, for each contradiction identified, include:
1. **Severity**: [Blocker | Major | Nit]
2. **Dimension**: Contradiction Elimination & Inventive Transforms
3. **Contradiction**: Parameter [X] versus Parameter [Y].
4. **Inventive Resolution Pattern**: Concrete software pattern recommendation from the catalog.
5. **Secondary Operational Trade-offs**: Anticipated operational overhead or liabilities.
6. **Ideal Final Result (IFR)**: What the self-sufficient architecture would look like.

#### IF Mode: REVIEW
If no false compromise is detected, output: "No false compromise detected".
Otherwise, for each finding, include:
1. **Severity**: [Major | Nit] (Advisory findings)
2. **Affected Scope**: Section header or architectural subsystem.
3. **False Compromise**: Description of the accepted trade-off in the text.
4. **Proposed Resolution**: Concrete architectural pattern to resolve the contradiction.
5. **Secondary Liabilities**: Operational overhead or complexity introduced by the pattern.
```

--------------------------------------------------------------------------------

### 2. Workflow & Review Pipeline Integration

#### A. Upstream Brainstorming Integration (`/egm-brainstorm`)

1.  **Skill Table Update**: Add `Inventive Catalyst` to the table of Goldfish
    Brainstorming Lenses in `skills/egm-brainstorm/SKILL.md`:

    | Lens / Persona | Core Objective | Key Questions Challenged |
    | :------------- | :------------- | :----------------------- |
    | **7. Inventive Catalyst** | Contradiction elimination & inventive transforms | *What fundamental trade-off is this design accepting as inevitable? How can we resolve this conflict using proven software transforms to achieve the Ideal Final Result without compromise?* |

2.  **Synthesizer Dispatch Update**: In `agents/synthesizer.md` and
    `skills/egm-brainstorm/SKILL.md`, update the subagent dispatch list for
    `Mode: BRAINSTORM`:

    *   Update `Reviewers` to include `egm-inventive-catalyst`.

3.  **Generic Multi-Lens Synthesis**: `egm-synthesizer` aggregates findings
    across all lenses symmetrically into the `## Analysis` section of
    `concepts_brief.md`. Extend the failed-reviewer rule in
    `agents/synthesizer.md` from `Mode: REVIEW` to `Mode: BRAINSTORM`: a lens
    that times out or returns nothing is retried once, then reported as
    `not run` in `concepts_brief.md`, never as a lens with no findings.

#### B. Review Loop Integration (`/egm-review`)

1.  **Step 5 (Initial Strategic Review) Pairing**: In
    `skills/egm-review/SKILL.md`, update `Subflow: Zoom Out Review` (Step 5) to
    spawn **two parallel high-altitude auditors**:
    *   `egm-zoom-out`: Audits for YAGNI, over-engineering, and root-problem
        alignment against `zoom-out-standard.md`.
    *   `egm-inventive-catalyst`: Audits for foundational false compromises and
        inventive opportunities across `full file` without a document standard
        (relying on its self-contained inlined catalog, analogous to
        `egm-comprehension`).
2.  **Advisory Checkpoint Gate**: Step 5 is an interactive manual checkpoint
    gate. Findings from the Catalyst are reported in `zoom_out_report.md` under
    an **Inventive Opportunities** section. The author can choose to pivot
    their architecture early before proceeding. In `Subflow: Uninterrupted Full
    Flow`, these advisory opportunities in `zoom_out_report.md` are excluded
    from the mandatory defect repair traceability matrix.
3.  **Unidirectional Review Pipeline**: Because foundational compromises are
    evaluated in Step 5:
    *   Step 6 (`egm-comprehension`) audits the doc for clarity.
    *   Step 7 (`egm-design`, `egm-structural`, `egm-style`) audits
        implementation mechanics without cyclic whiplash.
    *   Step 8 (`egm-zoom-out`) acts as the final pruning shears before Step 9
        readiness testing, evaluating adopted inventive resolutions in the
        context of resolved trade-offs so legitimate conflict resolutions are
        not treated as premature complexity.

--------------------------------------------------------------------------------

## Risks & Limits

### 1. Hallucinating Contradictions on Hard Theoretical Invariants

*   **Risk**: An inventive agent may misinterpret fundamental mathematical,
    physical, or theoretical limits as solvable compromises, generating
    unfeasible proposals.
*   **Mitigation**: The persona prompt explicitly bounds contradiction analysis:
    theoretical invariants are immutable system bounds, not technical
    contradictions to be eliminated.

### 2. Secondary Operational Liabilities & YAGNI Bloat

*   **Risk**: Applying architectural patterns (e.g., event buses, sidecars,
    caching layers) to resolve minor friction introduces operational and
    maintenance overhead.
*   **Mitigation**:
    1.  The Catalyst must explicitly output `Secondary Liabilities` for every
        pattern.
    2.  In `/egm-review`, Step 5 findings are strictly advisory, and Step 8
        (Intermediate Zoom Out) prunes any speculative complexity before
        implementation planning.

### 3. Swarm Execution Resilience

*   **Risk**: Adding a 7th subagent to the parallel shootdown swarm increases
    request concurrency, risking timeout failures in latency-sensitive
    environments.
*   **Mitigation**: Item 3 extends the failed-reviewer rule in
    `agents/synthesizer.md` from `Mode: REVIEW` to `Mode: BRAINSTORM`: a lens
    that times out or returns nothing is retried once, then reported as
    `not run` in `concepts_brief.md`, never as a lens with no findings.

--------------------------------------------------------------------------------

## Alternatives Considered

### Alternative A: Augmenting Existing Lenses with TRIZ Logic

*   **Description**: Inject TRIZ prompts into `design_critic.md` or
    `zoom_out.md` rather than creating a new persona.
*   **Pros**: Avoids adding another persona file to `agents/`.
*   **Cons**: Dilutes the core mission of existing personas. `design_critic` is
    specifically designed to be skeptical and pessimistic; forcing it to also be
    an inventive brainstormer creates conflicting directives and lowers finding
    quality.
*   **Reason for Rejection**: EGM relies on isolated, single-responsibility
    critics. A dedicated persona keeps evaluative and inventive mindsets cleanly
    separated.

### Alternative B: Interactive Multi-Select Gates via Custom Modal Tools

*   **Description**: Add an interactive multi-select UI dialog (e.g.,
    `ask_question`) in `/egm-brainstorm` allowing users to selectively toggle
    individual Goldfish personas on or off before each shootdown.
*   **Pros**: Allows granular per-session customization.
*   **Cons**: Violates `skills/egm-brainstorm/SKILL.md` Constraint 2 (no
    structured question tools during ideation), depends on a structured
    question tool that only some harnesses have, and adds user friction.
*   **Reason for Rejection**: The automated parallel swarm handles reviews
    cleanly without manual toggling.

### Alternative C: Synthesizer-Embedded Prompting (Zero-Spawn Alternative)

*   **Description**: Instruct `egm-synthesizer` to perform TRIZ analysis
    directly during synthesis rather than launching a 7th subagent.
*   **Pros**: Saves token expenditure and eliminates cold-start latency for one
    subagent.
*   **Cons**: Violates EGM's core invariant of zero-context Goldfish isolation.
    The Synthesizer's role is objective aggregation; forcing it to generate
    inventive patterns biases its synthesis and dilutes independent critical
    findings.
*   **Reason for Rejection**: Independent Goldfish isolation produces higher
    quality, unpolluted critique.

### Alternative D: In-Prompt Pattern Knowledge vs. External Reference File

*   **Description**: Author a separate `resources/triz_patterns.md` document for
    the agent to read at runtime.
*   **Pros**: Keeps the persona prompt shorter.
*   **Cons**: Introduces file I/O latency, creates dual-maintenance drift
    between documentation and prompt, and fails with `FileNotFound` across
    diverse harnesses in client repositories.
*   **Reason for Rejection**: Inlining the 10 core pattern summaries into the
    system prompt guarantees zero-I/O, deterministic execution in all harnesses
    without dead artifacts.

### Alternative E: Step 5 Strategic Audit vs. Step 7 Blocking Review Loop

*   **Description**: Add `egm-inventive-catalyst` to the Step 7
    (`egm-review-loop`) blocking repair loop.
*   **Pros**: Runs alongside design critics on `FeatureRange`.
*   **Cons**: Causes severe cyclic whiplash with Step 8 (`egm-zoom-out`), which
    immediately prunes complexity added in Step 7. Furthermore, mapping to
    `feature-spec-standard.md` creates a phantom contract.
*   **Reason for Rejection**: Placing the Catalyst in Step 5 provides the
    earliest strategic trade-off audit before line-by-line review, creating a
    unidirectional pipeline without blocking loops.

--------------------------------------------------------------------------------

## Detailed Implementation Plan

The implementation is partitioned into four sequential phases, strictly
enforcing the Zero-Decision Rule and establishing deterministic verification
checkpoints at each stage.

### Phase 1: Agent Persona Creation & Manifest Registration

#### 1. `agents/inventive_catalyst.md` (Create)

*   **Type / Scope**: Agent Persona Specification
*   **Rationale**: Define the system prompt, mandates, role, inlined pattern
    catalog, and output format for `egm-inventive-catalyst`.
*   **Proposed Changes**: Author the file following the exact schema specified
    in Section 1 of the Proposed Architecture.

#### 2. Host packages (Modify)

*   **Type / Scope**: Plugin manifests and host adapters
*   **Rationale**: Every host that ships the reviewers needs the new persona.
*   **Proposed Changes**: Add `"./.claude-plugin/agents/inventive_catalyst.md"`
    to the `agents` array in `.claude-plugin/plugin.json`. Add the persona to
    `.claude-plugin/agents/`, `.cursor-plugin/agents/`,
    `com.github.copilot/agents/egm-inventive-catalyst.agent.md`, the reviewer
    list in `adapters/opencode/install.py`, and the persona list in
    `scripts/pack_plugin.py`. Update reviewer and adapter counts in
    `docs/harnesses.md` from nine to ten.

*Phase 1 Checkpoint*: Validate YAML frontmatter across all agent files using
`pytest tests/unit/test_frontmatter.py`.

--------------------------------------------------------------------------------

### Phase 2: Workflow Skill Orchestration

#### 3. `agents/synthesizer.md` (Modify)

*   **Type / Scope**: Intermediate Orchestrator & Aggregator
*   **Rationale**: Instruct `egm-synthesizer` to launch and aggregate findings
    from `inventive_catalyst` during brainstorming.
*   **Proposed Changes**:
    *   In `IF Mode: BRAINSTORM` Step 1: Update the subagent dispatch list to
        launch the 7-lens swarm in parallel, adding `inventive_catalyst` with
        the role title `Inventive Catalyst Brainstormer`.
    *   In `IF Mode: BRAINSTORM` Step 1: Add the `Failed Reviewers` rule from
        `Mode: REVIEW` Step 1: retry a lens once, then report it as `not run`
        in `concepts_brief.md`, never as a lens with zero findings.
    *   In `IF Mode: BRAINSTORM` Step 2: Update aggregation instructions:
        *"Collect findings from all 7 Goldfish, deduplicate overlapping points,
        synthesize inventive contradictions and pattern resolutions alongside
        risk dimensions, and compile them into `concepts_brief.md`."*
    *   In Step 5 of `egm-review`: `egm-inventive-catalyst` is dispatched
        alongside `egm-zoom-out`; findings under `## Inventive Opportunities`
        are recorded directly into `zoom_out_report.md` without altering
        `goldfish_review_report.md`'s strict Blocker/Major/Nit defect schema.

#### 4. `skills/egm-brainstorm/SKILL.md` (Modify)

*   **Type / Scope**: Core Skill Workflow
*   **Rationale**: Register `egm-inventive-catalyst` in the brainstorming
    shootdown swarm.
*   **Proposed Changes**:
    *   Add the 7th lens to the table: `| **7. Inventive Catalyst** |
        Contradiction elimination & inventive transforms | *What fundamental
        trade-off is this design accepting as inevitable? How can we resolve
        this conflict using proven software transforms to achieve the Ideal
        Final Result without compromise?* |`
    *   Update Step 2.1 lead-in to include `egm-inventive-catalyst` in the
        `Reviewers` array parameter:
        `Reviewers: [egm-design, egm-codebase-details, egm-zoom-out,
        egm-comprehension, egm-implementation-readiness, egm-structural,
        egm-inventive-catalyst]`.
    *   In the embedded `concepts_brief.md` template, extend the `## Analysis`
        placeholder to cover inventive contradictions, the catalog pattern
        suggested for each, its secondary trade-offs, and the Ideal Final
        Result.

#### 5. `skills/egm-review/SKILL.md` (Modify)

*   **Type / Scope**: Review Orchestrator
*   **Rationale**: Integrate `egm-inventive-catalyst` into Step 5 (Initial
    Strategic Review) without colliding with Step 8 post-critic pruning, while
    staying strictly under the 24,000-byte skill load limit enforced by
    `tests/unit/test_skill_load_limits.py`.
*   **Skill Size Budget**: The `egm-review` body is 23,743 bytes at `main`,
    leaving 257 bytes of headroom. To accommodate Step 5 without exceeding the
    limit:
    1.  The detailed report schema for Inventive Opportunities is defined
        strictly inside `agents/inventive_catalyst.md`'s `# Output Format`,
        avoiding a duplicate multiline schema block in `SKILL.md`.
    2.  `Subflow: Zoom Out Review` stays shared. Its Step 5 case and the Step 5
        bullet in `Subflow: Uninterrupted Full Flow` add
        `egm-inventive-catalyst`. This brings the body to about 23,885 bytes,
        so nothing else needs cutting.
*   **Proposed Changes**:
    *   In `Subflow: Zoom Out Review` step 1, after the Step 8 clause, add:
        "When running as Step 5, also spawn `egm-inventive-catalyst` in
        parallel and write both into `zoom_out_report.md`." Step 8 still runs
        only `egm-zoom-out`.
    *   In the Step 5 bullet of `Subflow: Uninterrupted Full Flow`, which the
        `Consolidated report` preset runs, change `Reviewers: [egm-zoom-out]`
        to `Reviewers: [egm-zoom-out, egm-inventive-catalyst]`.

*Phase 2 Checkpoint*: Validate skill frontmatter and subflow parsing via `pytest
tests/unit/test_frontmatter.py`.

--------------------------------------------------------------------------------

### Phase 3: Global Documentation & Lens Count Synchronization

#### 6. `docs/designs/review.md` (Modify)

*   **Type / Scope**: Architectural Specification
*   **Rationale**: Reconcile the review pipeline specification with Step 5
    dual-auditor integration.
*   **Proposed Changes**:
    *   Update the Mermaid flowchart node `Step5` to `Step 5: Initial Strategic
        Review (Zoom Out + Inventive Catalyst)`.
    *   Update the Step 5 Stage Breakdown section to document the parallel
        execution of `zoom_out` and `inventive_catalyst`.
    *   Add `agents/inventive_catalyst.md` to the Reviewer Persona Catalog
        table.

#### 7. Design System Documentation (Modify)

*   **Type / Scope**: Architectural Specifications
*   **Rationale**: Synchronize component inventories and lens counts across
    design specs.
*   **Proposed Changes**:
    *   `docs/designs/architecture.md`: Update 6-lens shootdown swarm references
        to 7-lens, and add `inventive_catalyst` to the Personas Layer listing.
    *   `docs/designs/brainstorm.md`: Update Mermaid diagrams and lens
        descriptions from 6 to 7 lenses, and map `inventive_catalyst.md` to the
        Inventive Catalyst lens in the file mapping table.
    *   `docs/designs/synthesizer.md`: Update the 6-lens swarm section to
        7-lens, and add `inventive_catalyst` to the brainstorm perspectives
        list.
    *   `docs/designs/README.md`: Update the existing entry for
        `triz_integration.md` to remove reference to rejected "dynamic reviewer
        selection" and reflect integration into `/egm-brainstorm` and Step 5 of
        `/egm-review`.

#### 8. User-Facing Documentation (Modify)

*   **Type / Scope**: Documentation
*   **Rationale**: Ensure getting started documentation reflects multi-lens
    brainstorming without hardcoding brittle lens counts.
*   **Proposed Changes**:
    *   `docs/getting_started.md`: Change the "6-lens Goldfish" wording in the
        brainstorming overview to "multi-lens Goldfish".

*Phase 3 Checkpoint*: Validate link integrity across all documentation files
using `pytest tests/unit/test_link_integrity.py`.

--------------------------------------------------------------------------------

### Phase 4: Test Suite Updates & Behavioral Verification

#### 9. Test Specifications & Behavioral Scenarios (Modify)

*   **Type / Scope**: Test Suite & Evaluation Scenarios
*   **Rationale**: Ensure automated test coverage for the 7-lens swarm and Step
    5 Catalyst integration across all harnesses.
*   **Proposed Changes**:
    *   `skills/egm-brainstorm/TEST.md`: Update test expectations and lens
        enumeration to include Inventive Catalyst (7 lenses).
    *   `skills/egm-review/TEST.md`: Update Step 5 test expectation to verify
        Initial Strategic Review with parallel Zoom Out and Catalyst execution.
    *   `skills/egm-brainstorm/test_scenarios.yaml`: Add behavioral test
        scenarios asserting that the `## Analysis` section names an inventive
        contradiction, the catalog pattern suggested for it, and its secondary
        trade-offs, plus a scenario validating the "No false compromise
        detected" early-exit guardrail when the input is already optimal.
    *   `skills/egm-review/test_scenarios.yaml`: Add scenarios validating
        detection of false architectural compromises in Step 5 and the early-exit
        guardrail.
    *   `tests/unit/test_frontmatter.py`: Add validation asserting frontmatter
        conformance for all markdown files under `agents/`.
    *   `adapters/opencode/install.py`: Update `agents["egm"]["prompt"]`
        lead-in string from "complete all six brainstorm reviewers" to "all seven".
    *   `tests/unit/test_opencode_adapter.py`: Update agent count assertion
        from 8 to 9 (`assert len(config["agent"]) == 9`).
    *   `tests/unit/test_harnesses.py`: Add `"inventive_catalyst"` to the central
        `REVIEWERS` tuple.
    *   `scripts/pack_plugin.py`: Add `agents/inventive_catalyst.md` to the
        `REQUIRED_SHARED` list to ensure Claude distribution packaging passes
        `tests/unit/test_packaging.py`.

*Phase 4 Checkpoint*: Run the unit suite. `test_skill_load_limits.py` and
`test_scenario_coverage.py` cover the skill changes:

```bash
pytest tests/unit
```

--------------------------------------------------------------------------------

### Verification Plan

*   **Markdown Formatting & Linting**: Run `mdformat` across all created and
    modified documentation files:

    ```bash
    mdformat agents/ skills/ docs/ README.md
    ```

*   **Static Test Suite Execution**: Run the test suite from the repository
    root:

    ```bash
    pytest tests/unit
    ```
