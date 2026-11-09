---
name: egm-review
license: Apache-2.0
disable-model-invocation: true
description: >-
  Orchestrates the EGM Goldfish Review Protocol. Used as part of the EGM
  process to perform design document reviews. Executes five review phases:
  Initial Zoom Out Review, Comprehension Review, Design Critique, Intermediate
  Zoom Out Review, and Implementation Readiness.
---

# Review, Validation & Automated Remediation

When running in Codex or ChatGPT Work, first read [Codex integration](../../docs/codex.md).
In Claude Code or Cowork, read `${CLAUDE_PLUGIN_ROOT}/docs/claude.md` first.

Reviews and validates a design document through specialized reviewer personas.

## Execution Constraints & Delegation (CRITICAL)

1. Read and apply `resources/execution_instructions.md` (Shared Execution Constraints and Subagent Delegation). If subagent nesting is unsupported, use direct dispatch instead of `egm-synthesizer` (see `docs/harnesses.md`). If your harness has no subagent tool, stop and tell the user: a review in the same context is not a Goldfish review.
2. **Artifact-First & Style**: Never dump drafts or reports in chat; write every report to the working or artifact directory, share its path, and apply direct plain English with adversarial scrutiny (no flattering adjectives or apologies).
3. **Interaction Invariants**: Every modal gate MUST contain one question (`len(questions) == 1`), set `is_multi_select: false` (preserving 5 -> 6 -> 7 -> 8 -> 9 topology), make Option 0 the unlabeled primary action (no `(Recommended)` prefix), and be the final tool call in the turn (after preparatory report writes). Ask for open-ended paths or free-text lists in plain chat text.

## Inputs

* **`TargetFile`**: Absolute or relative path to the design document.
* **`GoldfishContext`** (Optional): Reading list establishing the system baseline (an empty list or explicit "no additional context" counts as provided). If omitted, holds only the linked files added in Step 1.3.
* **`Step`** (Optional): `interactive`, `uninterrupted`, `feature_spec`, `implementation`, or an individual stage `5`, `6`, `7`, `8`, `9`. Prompts user if omitted.

## Workflow

### Step 1: Intake & Setup

1. **`TargetFile`**: If missing, explain in plain chat that the design document path is required to analyze its structure and discover the semantic split, ask for the path, and end your turn.
2. **`GoldfishContext`**: Once `TargetFile` is provided, if `GoldfishContext` is missing, explain in plain chat that baseline context files are optional (linked files inside the working directory are added automatically; other links and URLs require approval) and ask if they wish to provide additional context files.
3. **Linked Files (run later)**: Do not run during intake. Run once after Step 2 preset selection and right before the first stage that takes `GoldfishContext` (any stage except Stage 6), in any flow including `uninterrupted`:
   * Read `TargetFile`, skip anchor-only links (`#...`), drop `#fragment` suffixes, and resolve relative links against `TargetFile`'s folder.
   * Add each existing file whose real path (after following symbolic links) stays inside the working directory to `GoldfishContext`; skip missing local files.
   * If any link resolves outside the working directory or is a URL, list those links in plain chat, ask which to include, and end your turn (if unattended/headless, leave them all out and continue). Add only approved links and tell the user which were left out.
   * Because some reviewers cannot open URLs, save the raw page of each URL in `GoldfishContext` as a new file in the working directory (or harness artifact directory) and pass its absolute path instead. If saving fails, ask the user for a local copy and end your turn (if unattended/headless, leave it out, tell the user, and continue).
   * Pass `GoldfishContext` to every stage except Stage 6 (which reads the document alone); instruct any synthesizer to give these files to each reviewer.

### Step 2: Curated Pipeline Preset Selection

If `Step` was explicitly provided, map directly to that preset or individual stage (`5`..`9`) and bypass this gate. Otherwise, present a single-select gate:

* **Question**: `"Select the review execution mode for this document:"`
* **Options & Pipeline Dispatch**:
  0. `"Interactive review with all review rubrics (step-by-step, check in after each review)"` -> Run Step 3, then execute Stages 5 -> 6 -> 7 -> 8 -> 9 sequentially with checkpoint gates.
  1. `"Consolidated report with all review rubrics (runs full flow without stopping)"` -> Run Step 3, then run Uninterrupted Full Flow (Stages 5 -> 6 -> 7 -> 8 -> 9 without checkpoints into `consolidated_review_report.md`).
  2. `"Feature spec only (evaluate design without considering implementation)"` -> **Bypass Step 3** (`FeatureRange = 1..End`, `DetailedRange = N/A`), execute Stages 5 -> 6 -> 7 -> 8 with checkpoints, and halt cleanly after Stage 8 before Stage 9.
  3. `"Implementation plan only (evaluate design for implementation readiness)"` -> Run Step 3 to confirm `DetailedRange`, then jump directly to Stage 9.

### Step 3: Semantic Split Discovery

Skip completely if Preset 2 (`Feature spec only`) was selected (`FeatureRange = 1..End`, `DetailedRange = N/A`). Otherwise, read `TargetFile` and scan for `## Detailed Implementation Plan` (or synonyms `## Implementation Plan`, `## Work Breakdown`, `## Implementation Steps`):

* **Standard Layout at line `L`**: Assign `FeatureRange = 1..(L-1)` and `DetailedRange = L..End`, post `"Discovered semantic boundary at line L. FeatureRange: 1..(L-1), DetailedRange: L..End."` in chat, and proceed directly without a confirmation gate.
* **Ambiguous / Multiple Candidate Headers**: Present a single-select gate proposing the most likely split line as Option 0 and custom line ranges (write-in) as Option 1.
* **No Implementation Plan Found**: Notify the user in chat, assign `FeatureRange = 1..End` and `DetailedRange = N/A`, and offer to execute Stages 5-8 (`Feature spec only`).

## Subflows

### Stage Specifications (Stages 5-9)

Write each stage's report via your file-writing tool and notify the user in chat with its file path (no chat dumps):

| Stage | Target & Context | Delegation & Standards | Report File & Delivery Rules |
| :--- | :--- | :--- | :--- |
| **5: Initial Zoom Out Review** | `full file` + `GoldfishContext` | Spawn `egm-synthesizer` (or direct) running `egm-zoom-out` (`agents/zoom_out.md`, standard `resources/document_standards/zoom-out-standard.md`) and `egm-inventive-catalyst` (`agents/inventive_catalyst.md`, `Mode: REVIEW`) in parallel | Write both into `zoom_out_report.md`; keep `"No false compromise detected"` when none found. |
| **6: Comprehension Test** | `FeatureRange` & `DetailedRange` (no `GoldfishContext`) | Spawn `egm-comprehension` (`agents/comprehension.md`) **directly** (never `egm-synthesizer`; synthesizer keeps only findings and drops the paraphrase) with **no document standard** (tests self-containment; do not apply `re-implementation-standard.md`, which asks for code-level detail forbidden in `FeatureRange` by the Zoom Out standard) | Write complete result to `comprehension_report.md`: two paraphrase headings verbatim first, then findings (keep paraphrase even when there are no findings). |
| **7: Critic Review** | `FeatureRange` + `GoldfishContext` | Interactive: invoke `egm-review-loop` in-thread; Uninterrupted: spawn `egm-synthesizer` (or direct subagents). Reviewers `[egm-design (agents/design_critic.md), egm-structural (agents/structural.md), egm-style (agents/style.md)]`, standards `{"egm-design": "feature-spec-standard", "egm-structural": "feature-spec-standard"}` | Write `critic_report.md`. |
| **8: Intermediate Zoom Out** | `full file` + `GoldfishContext` | Spawn `egm-synthesizer` (or direct `egm-zoom-out` at `agents/zoom_out.md`) applying `resources/document_standards/zoom-out-standard.md`; include `zoom_out_report.md` path in context and focus on additions/mitigations from Comprehension and Critic stages | Write `intermediate_zoom_out_report.md`. |
| **9: Implementation Readiness Test** | `DetailedRange` + `GoldfishContext` | Interactive: invoke `egm-review-loop` in-thread; Uninterrupted: spawn `egm-synthesizer` (or direct subagents). Reviewers `[egm-implementation-readiness (agents/implementation_readiness.md), egm-codebase-details (agents/codebase_details.md), egm-style (agents/style.md)]`, standards `{"egm-implementation-readiness": "implementation-readiness-standard", "egm-codebase-details": "implementation-readiness-standard"}` | Write `implementation_readiness_report.md`. |

### Subflow: Uninterrupted Full Flow

1. Execute Stages 5 -> 6 -> 7 -> 8 -> 9 in sequence without interactive checkpoint pauses, writing each individual stage report file.
2. Collect findings across all 5 stage reports, consolidate into prioritized tasks (🔴 Blocker, 🟡 Major, 🟢 Nit), and build a Traceability Matrix mapping raw findings to consolidated action items.
3. Write `consolidated_review_report.md` via your file-writing tool and notify the user with its path.

### Interactive Checkpoint Gates & Pause/Resume Protocol

Conclude each interactive stage by notifying the user of the report path and presenting the single-select gate:

* **Per-Stage Question & Option 0**:
  * **Stage 5**: Question `"Stage 5 (Initial Zoom Out Review) completed. Findings written to zoom_out_report.md. How would you like to proceed?"`; Option 0 `"Proceed to next stage: Stage 6 (Comprehension Test)"`.
  * **Stage 6**: Question `"Stage 6 (Comprehension Test) completed. Findings written to comprehension_report.md. How would you like to proceed?"`; Option 0 `"Proceed to next stage: Stage 7 (Critic Review)"`.
  * **Stage 7**: Question `"Stage 7 (Critic Review) completed. Findings written to critic_report.md. How would you like to proceed?"`; Option 0 `"Proceed to next stage: Stage 8 (Intermediate Zoom Out Review)"`.
  * **Stage 8 (`Feature spec only`)**: Question `"Stage 8 (Intermediate Zoom Out) completed. High-level architecture verified. How would you like to proceed?"`; Option 0 `"Conclude review and begin detailed implementation planning"`.
  * **Stage 8 (`Interactive`)**: Question `"Stage 8 (Intermediate Zoom Out) completed. Findings written to intermediate_zoom_out_report.md. How would you like to proceed?"`; Option 0 `"Proceed to next stage: Stage 9 (Implementation Readiness Test)"`.
  * **Stage 9**: Question `"Stage 9 (Implementation Readiness Test) completed. Report written to implementation_readiness_report.md. How would you like to proceed?"`; Option 0 `"Conclude review and finalize document"`.
* **Remaining Gate Options**:
  * **Stages 5, 6, 8**: Option 1 `"I will update doc first (pause session; notify me in chat when edits are complete to re-run)"`; Option 2 `"Pause Review (save progress and exit)"`.
  * **Stages 7, 9**: Option 1 `"Resolve findings with agent (evaluate findings, propose fixes, and apply approved edits)"`; Option 2 `"I will update doc manually (pause session; notify me in chat when edits are complete to re-run)"`; Option 3 `"Pause Review (save progress and exit)"`.
* **Resolution Semantics (Option 1 in Stages 7 & 9)**: Invoke `egm-resolve` in the primary Elephant context on `FeatureRange` (Stage 7, passing findings from `critic_report.md` or `goldfish_review_report.md`) or `DetailedRange` (Stage 9, passing findings from `implementation_readiness_report.md` or `goldfish_review_report.md`) to classify findings (`PROPOSE FIX` vs `CONTEST`), write `goldfish_review_report.md`, and execute approved edits on `TargetFile`. Re-read `TargetFile` to recalculate line bounds, then advance (or re-run the stage, max 1 re-audit).
* **Pause & Resume (Manual Doc Updates)**: Confirm in chat that the review is paused for manual edits and yield immediately. When the author replies that edits are complete, re-read `TargetFile` to recalculate line shifts, apply Step 1.3 rules to any links added since Step 1.3 ran, and re-run the current stage. **1-Audit Convergence Cap**: Max 1 re-audit per stage; if manual updates are requested again, inform the author the cap is reached, document residual findings as accepted trade-offs, auto-bind Option 0, and advance.
* **Graceful Halt (`Pause Review`)**: Halt immediately with zero tools, preserving all report artifacts.
