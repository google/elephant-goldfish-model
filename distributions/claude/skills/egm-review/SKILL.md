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

## Delegation

A Goldfish runs in a fresh context with no conversation history. Spawn each subagent using your harness tool (Antigravity: `invoke_subagent`; Claude Code: `Agent`; Codex: `spawn_agent`). Persona definitions reside in `agents/<file>.md`; use the frontmatter `name` (for example `egm-zoom-out`) where named subagents are registered, or spawn a general subagent directed to read that persona file. Pass prompts verbatim and await the report. If subagents cannot be nested, use direct dispatch instead of the synthesizer (`docs/harnesses.md`). If your harness lacks subagent support, halt: in-context review is not a Goldfish review.

## Execution Constraints (CRITICAL)

1.  **Artifact-First Delivery (MANDATORY)**: You are **STRICTLY FORBIDDEN** from presenting large proposals, drafts, summaries, or plans directly in the chat pane. You **MUST** write them to the working directory (or your harness's artifact directory, if it has one) using your file-writing tool and then tell the user in chat the file path and ask for review. This applies to the Discussion Summary, Design Drafts, and all review reports.
2.  **Plain-English Standard**: You **MUST** write all concepts briefs, summaries, and communications in simple, direct, jargon-free plain English. Explain technical mechanisms directly. Do not summarize away substance or rely on buzzwords. Do not use ungrounded promotional adjectives (e.g., *seamless*, *robust*, *blazingly fast*) or decorative adverbs (e.g., *seamlessly*, *effortlessly*, *literally*, *drastically*, *obviously*).
3.  **Default to Stress-Testing**: Never agree by default. Your primary directive is to stress-test ideas, strategies, and opinions. Find the weakest points, edge cases, and blind spots before affirming anything.
4.  **No Glazing & Tone**: Eliminate sycophancy. Never call ideas "great," "brilliant," or "smart." Compliments without substance are noise. Critique first: lead with what is wrong, missing, or risky before highlighting merits.
5.  **Reject Echo-Chamber Framing**: Never parrot framing back to the user. If a conclusion is asserted, do not validate it reflexively. Actively outline: What is the user not seeing? What is the strongest counter-argument? Is the opposing view justified?
6.  **Earn Your Agreement**: Only agree when the idea has survived rigorous, objective scrutiny.
7.  **Banned Adjectives (No Flattery)**: Strictly prohibited from using validating adjectives like "brilliant," "great," "smart," "correct," "perfect," "excellent," or "spot-on" when referring to the user's inputs, corrections, or decisions.
8.  **Banned Apologies**: Strictly prohibited from polite apologies (e.g., "I apologize," "I am sorry," "Forgive me"). Outline corrected technical logic directly.
9.  **Interaction Invariants**: All interactive gates (structured question tools like `ask_question`, or plain chat) MUST contain strictly one question (`len(questions) == 1`), be the sole tool call in the turn, and provide clear, action-oriented options without `(Recommended)` prefixes.

## Inputs

*   **`TargetFile`**: Absolute or relative path to the design document.
*   **`GoldfishContext`** (Optional): Reading list to establish the system baseline. If omitted, it holds only the linked files that Step 1.3 adds.
*   **`Step`** (Optional): Specific pipeline preset or stage to run (e.g. `interactive`, `uninterrupted`, `feature_spec`, `implementation`, or an individual stage `5`, `6`, `7`, `8`, `9`). If omitted, prompt the user.

## Workflow

### Step 1: Intake & Setup

1.  **Verify TargetFile**: If missing, explain that the target design document path is required to analyze structure and semantic split. Prompt the user in chat via regular text (do NOT use structured question tools such as `ask_question`, as file paths are open-ended) and end turn.
2.  **Verify GoldfishContext**: Once `TargetFile` is provided, check `GoldfishContext` (empty list counts as provided). If missing, explain that context files establish baseline knowledge, note that linked files inside the working directory are added automatically, and prompt via regular text if they wish to provide additional files.
3.  **Linked Files (run later)**: Run this once, after Step 2 preset selection and right before the first stage taking `GoldfishContext` (any stage except Stage 6), in any flow including `uninterrupted`. Read `TargetFile`, skip anchor-only links (`#...`), strip `#fragment`, and resolve relative links against the document folder. Add links staying inside the working directory to `GoldfishContext`, skipping nonexistent files. If any link resolves outside the working directory or is a URL, list those links in chat, ask which to include, and end turn; in headless runs, omit them and proceed. Add only approved links and report excluded ones. Reviewers cannot fetch URLs directly: save the raw page of each URL in `GoldfishContext` as a local file in the working directory (or artifact directory) and pass its absolute path instead. If saving fails, ask the user for a local copy and end turn; if unanswered, omit it, inform user, and continue. Pass `GoldfishContext` to every stage except Stage 6 (which reads the document alone).

### Step 2: Curated Pipeline Preset Selection

1.  **Preset Gate Check**: If `Step` parameter was explicitly provided, map to the preset/subflow and bypass the gate. Otherwise, present the single-select preset gate (sole tool call, `len(questions) == 1`, `is_multi_select: false`, Option 0 default without `(Recommended)` prefix):

    ```json
    {
      "questions": [
        {
          "question": "Select the review execution mode for this document:",
          "options": [
            "Interactive review with all review rubrics (step-by-step, check in after each review)",
            "Consolidated report with all review rubrics (runs full flow without stopping)",
            "Feature spec only (evaluate design without considering implementation)",
            "Implementation plan only (evaluate design for implementation readiness)"
          ],
          "is_multi_select": false
        }
      ]
    }
    ```

2.  **Dispatch Action**:
    *   **Preset 0 (`Interactive review with all review rubrics`)**: Discover split (Step 3), then execute Stages 5, 6, 7, 8, 9 sequentially with interactive checkpoints.
    *   **Preset 1 (`Consolidated report with all review rubrics`)**: Discover split (Step 3), then run Uninterrupted Full Flow consolidating into `consolidated_review_report.md`.
    *   **Preset 2 (`Feature spec only`)**: Bypass Step 3 split discovery. Set `FeatureRange = 1..End`, `DetailedRange = N/A`. Execute Stages 5, 6, 7, 8 with checkpoints. Cleanly halt after Stage 8.
    *   **Preset 3 (`Implementation plan only`)**: Discover split (Step 3), confirm `DetailedRange`, and jump directly to Stage 9.

### Step 3: Semantic Split Discovery

1.  **Split Bypass Check**: If Preset 2 (`Feature spec only`) was selected, skip this step. Set `FeatureRange = 1..End`, `DetailedRange = N/A`, and proceed to Step 4.
2.  **Inspect Structure**: Read `TargetFile` and scan for the primary dividing header `## Detailed Implementation Plan` (or synonyms: `## Implementation Plan`, `## Work Breakdown`, `## Implementation Steps`).
    *   **Standard Boundary Found (line L)**: Assign `FeatureRange = 1..(L-1)` and `DetailedRange = L..End`. Confirm in chat: `"Discovered semantic boundary at line L. FeatureRange: 1..(L-1), DetailedRange: L..End."` Proceed to Step 4 without modal.
    *   **Ambiguous Boundary / Multiple Candidate Headers**: Present a single-select gate (`len(questions) == 1`) proposing the top candidate line as Option 0, with Option 1 allowing write-in.
    *   **No Implementation Plan Found**: If document contains only a feature spec, notify user in chat, set `FeatureRange = 1..End`, `DetailedRange = N/A`, and proceed with Stages 5-8.

### Step 4: Staging Strategy

Confirm `FeatureRange` and `DetailedRange`, then dispatch:
*   **Interactive full flow**: Stages 5 → 6 → 7 → 8 → 9 sequentially.
*   **Consolidated full flow**: Subflow: Uninterrupted Full Flow.
*   **Feature spec only**: Stages 5 → 6 → 7 → 8, then halt.
*   **Implementation plan only**: Jump directly to Stage 9.

---

## Subflows

### Subflow Checkpoint Gates & Pause/Resume Protocol

Interactive review stages conclude with a single-select gate (`len(questions) == 1`, `is_multi_select: false`, sole tool call):

1.  **Altitude & Comprehension Checkpoints (Stages 5, 6, 8)**:
    *   Option 0: `Proceed to next stage: Stage [N+1] ([Next Stage Name])` (or `Conclude review and begin detailed implementation planning` for Stage 8 terminal).
    *   Option 1: `I will update doc first (pause session; notify me in chat when edits are complete to re-run)`.
    *   Option 2: `Pause Review (save progress and exit)`.
2.  **Remediation & Readiness Checkpoints (Stages 7, 9)**:
    *   Option 0: `Proceed to next stage: Stage [N+1] ([Next Stage Name])` (or `Conclude review and finalize document` for Stage 9 terminal).
    *   Option 1: `Resolve findings with agent (evaluate findings, propose fixes, and apply approved edits)`.
    *   Option 2: `I will update doc manually (pause session; notify me in chat when edits are complete to re-run)`.
    *   Option 3: `Pause Review (save progress and exit)`.
3.  **Resolution Semantics (Option 1 for Stages 7 and 9)**:
    *   Invoke `egm-resolve` in primary Elephant context on target range (`FeatureRange` or `DetailedRange`), passing parsed findings from `critic_report.md` or `implementation_readiness_report.md`.
    *   The Elephant classifies findings (`PROPOSE FIX` vs `CONTEST`), writes `goldfish_review_report.md`, and executes approved edits on `TargetFile`.
    *   Re-read `TargetFile` to update line bounds. Advance to next stage or re-run stage audit (enforcing max 1 re-audit limit).
4.  **Pause & Resume Semantics (Manual Doc Updates)**:
    *   Yield execution immediately. When user indicates edits are complete in chat: re-read `TargetFile`, apply Step 1.3 to new links, and re-run current stage (max 1 re-audit; if requested again, document residual findings as accepted trade-offs, auto-bind Option 0, and advance).
5.  **Pause Review**: Halt immediately with zero tool calls, preserving report artifacts.

### Subflow: Uninterrupted Full Flow

Execute all 5 stages in sequence without interactive pauses. Write each individual report to the working directory (or artifact directory). Pass `GoldfishContext` to every step except Step 6:
*   **Step 5 (Initial Zoom Out)**: Spawn `egm-synthesizer` (or direct subagents) with `Reviewers: [egm-zoom-out, egm-inventive-catalyst]` on `full file` → write `zoom_out_report.md`. Note: `egm-inventive-catalyst` audits dialectical contradictions using its inlined 10-pattern catalog (no document standard file). Advisory inventive opportunities in `zoom_out_report.md` are excluded from the mandatory defect repair matrix.
*   **Step 6 (Comprehension Test)**: Spawn `egm-comprehension` directly on `FeatureRange` & `DetailedRange` with no document standard → write `comprehension_report.md` (keep paraphrase verbatim).
*   **Step 7 (Critic Review)**: Spawn `egm-synthesizer` with `Reviewers: [egm-design, egm-structural, egm-style]` on `FeatureRange` → write `critic_report.md`.
*   **Step 8 (Intermediate Zoom Out)**: Spawn `egm-synthesizer` with `Reviewers: [egm-zoom-out]` on `full file` → write `intermediate_zoom_out_report.md`.
*   **Step 9 (Implementation Readiness Test)**: Spawn `egm-synthesizer` with `Reviewers: [egm-implementation-readiness, egm-codebase-details, egm-style]` on `DetailedRange` → write `implementation_readiness_report.md`.

**Synthesis & Delivery**: Collect findings across all 5 reports, consolidate actionable items by priority (🔴 Blocker, 🟡 Major, 🟢 Nit), build Traceability Matrix mapping raw findings to actions, write `consolidated_review_report.md`, and notify user with file path.

### Subflow: Zoom Out Review

1.  **Delegate to Synthesizer**: Spawn `egm-synthesizer` (or `egm-zoom-out` at `agents/zoom_out.md`) on `full file` applying `resources/document_standards/zoom-out-standard.md`. Pass `GoldfishContext`.
    *   **Stage 5**: Spawn `egm-zoom-out` and `egm-inventive-catalyst` in parallel. `egm-inventive-catalyst` evaluates false compromises and trade-offs using its inlined 10-pattern catalog without an external document standard file. Write both sets of findings into `zoom_out_report.md`.
    *   **Stage 8**: When running as Step 8, include `zoom_out_report.md` path in context, focus on additions/mitigations from Comprehension and Critic stages, and write findings to `intermediate_zoom_out_report.md`.
2.  **Delivery & Notification**: Write report (`zoom_out_report.md` for Stage 5, `intermediate_zoom_out_report.md` for Stage 8) and notify user with file path.
3.  **Checkpoint Gate**: Present tri-state gate:
    *   **Stage 5**: `"Stage 5 (Initial Zoom Out Review) completed. Findings written to zoom_out_report.md. How would you like to proceed?"`, Option 0: `"Proceed to next stage: Stage 6 (Comprehension Test)"`.
    *   **Stage 8 (Feature Spec Only)**: `"Stage 8 (Intermediate Zoom Out) completed. High-level architecture verified. How would you like to proceed?"`, Option 0: `"Conclude review and begin detailed implementation planning"`.
    *   **Stage 8 (Interactive Full Flow)**: `"Stage 8 (Intermediate Zoom Out) completed. Findings written to intermediate_zoom_out_report.md. How would you like to proceed?"`, Option 0: `"Proceed to next stage: Stage 9 (Implementation Readiness Test)"`.
    *   Options 1 (`I will update doc first...`) and 2 (`Pause Review...`) follow Checkpoint Protocol.

### Subflow: Comprehension Test

1.  **Spawn Reviewer Directly**: Spawn `egm-comprehension` (`agents/comprehension.md`) directly on `FeatureRange` & `DetailedRange` with no document standard (do not use synthesizer, and do not apply `re-implementation-standard.md`). The test evaluates self-containment, not code detail.
2.  **Delivery & Notification**: Write complete output to `comprehension_report.md`, starting with the two paraphrase headings verbatim, then findings. Always retain the paraphrase, even if there are zero findings. Notify user with file path.
3.  **Checkpoint Gate**: Present Stage 6 tri-state gate:
    *   Question: `"Stage 6 (Comprehension Test) completed. Findings written to comprehension_report.md. How would you like to proceed?"`
    *   Option 0: `"Proceed to next stage: Stage 7 (Critic Review)"`
    *   Option 1: `"I will update doc first (pause session; notify me in chat when edits are complete to re-run)"`
    *   Option 2: `"Pause Review (save progress and exit)"`

### Subflow: Critic Review

1.  **Invoke Review Loop**: Invoke `egm-review-loop` on `FeatureRange` with reviewers `[egm-design, egm-structural, egm-style]`, standards `{"egm-design": "feature-spec-standard", "egm-structural": "feature-spec-standard"}`, and `GoldfishContext`.
2.  **Delivery & Notification**: Write `critic_report.md` and notify user with file path.
3.  **Checkpoint Gate**: Present Stage 7 gate:
    *   Question: `"Stage 7 (Critic Review) completed. Findings written to critic_report.md. How would you like to proceed?"`
    *   Option 0: `"Proceed to next stage: Stage 8 (Intermediate Zoom Out Review)"`
    *   Option 1: `"Resolve findings with agent (evaluate findings, propose fixes, and apply approved edits)"`
    *   Option 2: `"I will update doc manually (pause session; notify me in chat when edits are complete to re-run)"`
    *   Option 3: `"Pause Review (save progress and exit)"`
4.  **Remediation (Option 1)**: Follow Subflow Checkpoint Resolution Semantics via `egm-resolve` on `FeatureRange`, then re-read `TargetFile` to update bounds and advance to Stage 8 (or re-run Stage 7, max 1 re-audit).

### Subflow: Implementation Readiness Test

1.  **Invoke Review Loop**: Invoke `egm-review-loop` on `DetailedRange` with reviewers `[egm-implementation-readiness, egm-codebase-details, egm-style]`, standards `{"egm-implementation-readiness": "implementation-readiness-standard", "egm-codebase-details": "implementation-readiness-standard"}`, and `GoldfishContext`.
2.  **Delivery & Notification**: Write `implementation_readiness_report.md` and notify user with file path.
3.  **Terminal Checkpoint Gate**: Present Stage 9 terminal gate:
    *   Question: `"Stage 9 (Implementation Readiness Test) completed. Report written to implementation_readiness_report.md. How would you like to proceed?"`
    *   Option 0: `"Conclude review and finalize document"`
    *   Option 1: `"Resolve findings with agent (evaluate findings, propose fixes, and apply approved edits)"`
    *   Option 2: `"I will update doc manually (pause session; notify me in chat when edits are complete to re-run)"`
    *   Option 3: `"Pause Review (save progress and exit)"`
4.  **Remediation (Option 1)**: Follow Subflow Checkpoint Resolution Semantics via `egm-resolve` on `DetailedRange`, then re-read `TargetFile` to update bounds and conclude review (or re-run Stage 9, max 1 re-audit).
