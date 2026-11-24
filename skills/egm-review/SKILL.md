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

1.  **Shared Rules & Plugin-Root Paths**: Read the *Plugin-Root Resource Paths*, *Subagent Delegation (Goldfish Isolation)*, and *Shared Design & Review Constraints* sections of [execution instructions](../../resources/execution_instructions.md) (Claude Code: `${CLAUDE_PLUGIN_ROOT}/resources/execution_instructions.md`; pathless `<SKILL>`: `~/.gemini/config/plugins/egm/resources/execution_instructions.md`; **omp**: `skill://` reads cannot leave this skill's folder, so run `realpath skill://egm-review` or read `skill://egm-review` and go two directories up from its physical header path to `<plugin-root>`, then read bundled files by absolute path). Do not apply the drafting-only section here. Never call a bundled file missing after a failed skill-relative lookup, and pass spawned reviewers the resolved absolute paths of their persona file (`agents/<file>.md`) and document standard (`resources/document_standards/<name>.md`). If file tools cannot read `execution_instructions.md`, apply the inline rules below. Use direct dispatch instead of `egm-synthesizer` if nesting is unsupported (see [harnesses.md](../../docs/harnesses.md)); if no subagent tool exists, stop and tell the user that a review in the same context is not a Goldfish review.
2.  **Artifact-First & Style**: Never dump drafts or reports in chat; write every report to the working or artifact directory, share its path, and use direct plain English with adversarial scrutiny (never `"brilliant"`, `"great"`, `"smart"`, `"correct"`, `"perfect"`, `"excellent"`, `"spot-on"`, or apologies).
3.  **Interaction Invariants**: Every modal gate MUST contain strictly one question (`len(questions) == 1`), set `is_multi_select: false` (no multi-select checklists, protecting the `5 -> 6 -> 7 -> 8 -> 9` stage order), put the primary default action as Option 0 with no `(Recommended)` prefix on any option, emit non-empty visible chat text first, and be the sole tool call in its model response step (finish report writes or reads in an earlier step of the turn first). Ask open-ended paths/lists in plain chat.

## Inputs

* **`TargetFile`**: Absolute or relative path to the design document.
* **`GoldfishContext`** (Optional): Reading list establishing the system baseline (empty list or "no additional context" counts as provided; if omitted, holds Step 1.3 linked files).
* **`Attachments`** (Optional): Reading list of diagrams, screenshots, or data
  files. If omitted or empty, only `TargetFile` and `GoldfishContext` are
  inventoried.
* **`Step`** (Optional): `interactive`, `uninterrupted`, `feature_spec`, `implementation`, or an individual stage `5`, `6`, `7`, `8`, `9`. Prompts user if omitted.

## Workflow

### Step 1: Intake & Setup

1. **`TargetFile`**: If missing, explain in plain chat that the design document path is required to analyze its structure and semantic split, ask for the path, and end your turn.
2. **`GoldfishContext`**: Once `TargetFile` is known, if `GoldfishContext` is missing, explain in plain chat that baseline context files are optional (workspace-internal linked files are added automatically; other links and URLs require approval), ask if they wish to provide additional context files (do NOT use a structured question tool for open-ended file paths), and end your turn.
3. **Linked Files (run later)**: Do not run during intake. Run once after Step 2 and right before the first stage taking `GoldfishContext` (any stage except Stage 6), including in `uninterrupted`:
   * Read `TargetFile`, skip `#...` anchors, drop `#fragment` suffixes, and resolve relative links against `TargetFile`'s folder.
   * Add existing files whose real path (following symlinks) stays inside the working directory to `GoldfishContext`; skip missing local files.
   * If any link resolves outside the working directory or is a URL, list those links in plain chat, ask which to include, and end your turn (if unattended/headless, leave them all out and continue). Add only approved links and tell the user which were left out.
   * Because some reviewers cannot open URLs, save the raw page of each URL in `GoldfishContext` as a new file in the working (or harness artifact) directory and pass its absolute path instead. If saving fails, ask the user for a local copy and end your turn (if unattended/headless, leave it out, tell the user, and continue).
   * Pass `GoldfishContext` to every stage except Stage 6 (which reads the document alone); tell any synthesizer to give these files to each reviewer.
4. **Input Preflight**: Before proceeding to Step 2, inventory all declared inputs (`TargetFile`, `GoldfishContext`, and any referenced images/attachments), confirming the count, type (`text`, `image`, `attachment`), and identity of each. Verify readability of each input. Stop immediately with an actionable error if any input is absent or unreadable; record the preflight result.

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
| **5: Initial Zoom Out Review** | `full file` + `GoldfishContext` | Spawn `egm-synthesizer` (or direct) running `egm-zoom-out` (`agents/zoom_out.md`, standard `zoom-out-standard`) and `egm-inventive-catalyst` (`agents/inventive_catalyst.md`, `Mode: REVIEW`) in parallel | Write both to `zoom_out_report.md`; keep `"No false compromise detected"` when none found. |
| **6: Comprehension Test** | `FeatureRange` & `DetailedRange` (no `GoldfishContext`) | Spawn `egm-comprehension` (`agents/comprehension.md`) **directly** (never `egm-synthesizer`, which drops the paraphrase) with **no document standard** (tests self-containment; never `re-implementation-standard.md`, which asks for code detail forbidden in `FeatureRange`) | Write full output to `comprehension_report.md`: two verbatim paraphrase headings first, then findings (keep paraphrase even when there are no findings). |
| **7: Critic Review** | `FeatureRange` + `GoldfishContext` | **Interactive**: invoke [egm-review-loop](../egm-review-loop/SKILL.md) in-thread (`uninterrupted`: single-pass `egm-synthesizer` or direct subagents) for `[egm-design (agents/design_critic.md), egm-structural (agents/structural.md), egm-style (agents/style.md)]`, standards `{"egm-design": "feature-spec-standard", "egm-structural": "feature-spec-standard"}` | Write `critic_report.md`; unless `uninterrupted`, show Stage 7 gate (Option 1 runs [egm-resolve](../egm-resolve/SKILL.md)). |
| **8: Intermediate Zoom Out** | `full file` + `GoldfishContext` | Spawn `egm-synthesizer` (or direct `egm-zoom-out` at `agents/zoom_out.md`) with `zoom-out-standard`; include `zoom_out_report.md` path in context, auditing Comprehension/Critic additions | Write `intermediate_zoom_out_report.md`. |
| **9: Implementation Readiness Test** | `DetailedRange` + `GoldfishContext` | **Interactive**: invoke [egm-review-loop](../egm-review-loop/SKILL.md) in-thread (`uninterrupted`: single-pass `egm-synthesizer` or direct subagents) for `[egm-implementation-readiness (agents/implementation_readiness.md), egm-codebase-details (agents/codebase_details.md), egm-style (agents/style.md)]`, standards `{"egm-implementation-readiness": "implementation-readiness-standard", "egm-codebase-details": "implementation-readiness-standard"}` | Write `implementation_readiness_report.md`; unless `uninterrupted`, show Stage 9 gate (Option 1 runs [egm-resolve](../egm-resolve/SKILL.md)). |

On direct dispatch, map standard shortnames to `resources/document_standards/<name>.md` (passing absolute paths when `<plugin-root>` was resolved); retry a failed reviewer once, else record `Failed Reviewers` (`<name>: not run`).

### Subflow: Uninterrupted Full Flow

1. Execute Stages 5 -> 6 -> 7 -> 8 -> 9 in sequence without interactive checkpoint pauses, writing each individual stage report file.
2. Collect findings across all 5 stage reports, consolidate into prioritized tasks (🔴 Blocker, 🟡 Major, 🟢 Nit), and build a Traceability Matrix mapping raw findings to consolidated action items.
3. Write `consolidated_review_report.md` via your file-writing tool and notify the user with its path.

### Interactive Checkpoint Gates & Pause/Resume Protocol

Conclude each stage (unless `uninterrupted`) by notifying the user of the report path and presenting the single-select gate:

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
* **Resolution Semantics (Option 1 in Stages 7 & 9)**: Run [egm-resolve](../egm-resolve/SKILL.md) in-thread on `FeatureRange` (`critic_report.md` or `goldfish_review_report.md`) or `DetailedRange` (`implementation_readiness_report.md` or `goldfish_review_report.md`) to classify findings (`PROPOSE FIX`, `CONTEST`, `ESCALATE`, `DECLINE`), write `goldfish_review_report.md`, apply approved edits to `TargetFile`, re-read `TargetFile` for shifted line bounds, then advance to Stage 8 (Stage 7) or conclude the review session (Stage 9), or re-run the current stage (**max 1 re-audit**).
* **Pause & Resume (Manual Doc Updates)**: Confirm in chat that review is paused for manual edits and yield immediately. When edits are done, re-read `TargetFile` for line shifts, apply Step 1.3 to newly added links if Step 1.3 has run, and re-run the current stage (**max 1 re-audit per stage**; on a second manual-update request, note the cap is reached, record residual findings as accepted trade-offs, auto-bind Option 0, and advance).
* **Graceful Halt (`Pause Review`)**: Halt immediately with zero tools, keeping all report files.
