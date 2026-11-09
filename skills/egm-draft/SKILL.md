---
name: egm-draft
license: Apache-2.0
disable-model-invocation: true
description: >-
  Drafts a design document section-by-section using the concepts brief from
  egm-brainstorm (or user notes). This is the second step in the Elephant-Goldfish (EGM)
  feature flow. Use when you are ready to write a design doc after aligning on
  requirements + solution.
---

# Design Drafting (Document Construction)

When running in Codex or ChatGPT Work, first read [Codex integration](../../docs/codex.md).
In Claude Code or Cowork, read `${CLAUDE_PLUGIN_ROOT}/docs/claude.md` first.

Guides the user through drafting a technical design document section-by-section from aligned brainstorm problem and requirements context.

## Execution Constraints (CRITICAL)

1. Read and apply [execution instructions](../../resources/execution_instructions.md) (in Claude Code: `${CLAUDE_PLUGIN_ROOT}/resources/execution_instructions.md`; if `<SKILL>` omits a file path, check `~/.gemini/config/plugins/egm/resources/execution_instructions.md`; if file tools are unavailable, apply the inline constraints below), enforcing both Shared Execution Constraints and the Design-Only Scratchpad Rule.
2. **Artifact-First & Style**: Never print drafts, summaries, or code in chat; write `design_draft.md` in the working or artifact directory, share its path, and use direct plain English with adversarial scrutiny (never `"brilliant"`, `"great"`, `"smart"`, `"correct"`, `"perfect"`, `"excellent"`, `"spot-on"`, or apologies).
3. **Interaction Invariants**: Every interactive gate MUST have strictly one question (`len(questions) == 1`), `is_multi_select: false`, clear action-oriented options without `(Recommended)` prefixes, non-empty visible chat text before invoking the gate, and be the sole tool call in its model response step (finish preparatory file writes or reads in an earlier step within the same user turn first).
4. **Author Decides Architecture**: For design choices with multiple defensible answers (storage, data model, component boundaries, protocols), explain up to three unranked options in chat without a default (mechanism, trade-offs, failure conditions), then ask the author to choose via a single-select gate; if told to "just pick one", restate trade-offs and re-present the same gate. Decide mechanical choices (naming, formatting) yourself.
5. **Drafting Pace & Discipline**:
   * **Explicit Consensus Gates**: Achieve explicit agreement at each step transition; never save the final document or advance without user go-ahead, and challenge weak assumptions at each step.
   * **ONE QUESTION AT A TIME**: Present strictly one clarification question per turn and wait for the user's answer before continuing; never bundle multiple questions.
   * **NO SUMMARIES**: Never end responses with a "Summary of work", "Status", "Adherence", or "Rule checklist"; respond only with technical content and next steps.
   * **Contradiction Auditing**: If new requests contradict earlier goals or architecture, **do NOT modify any files** in that turn; report the contradiction in plain text and ask for resolution first.

## Inputs

* **`Context File`** (Optional): File path to a predecessor document (e.g., `docs/designs/<feature_name>.md`, `concepts_brief.md`, or `discussion_summary.md`). Defaults to discovering predecessor context in Step 1.

## Execution Workflow

Execute Steps 1-6 in order, allowing the user to revisit earlier phases anytime. Never skip ahead without explicit user consensus, and write `design_draft.md` iteratively across sections.

### Section Approval Gate (Steps 2-5)

After writing or updating each section in `design_draft.md` via your file-writing tool, present the approval gate in the same turn in strict order:

1. **Visible Chat Summary & Link (FIRST)**: Output conversational Markdown before invoking the question gate: state which section was drafted or updated, highlight 2-3 key decisions or additions, and include a link or path to `design_draft.md` (e.g., `[design draft](/absolute/project/design_draft.md)` in Codex). Never print the section body in chat, and NEVER emit a structured question tool call with empty response text.
2. **Approval Gate (SECOND)**: Present the single-select choice (`len(questions) == 1`, `is_multi_select: false`):
   * **Question**: `"Drafted [Section Name] in design_draft.md. Please review. How would you like to proceed?"`
   * **Option 0 (`"Approve [Section Name] and proceed to next section"`)**: Apply any inline comments on `design_draft.md` present in the turn context first, then advance to the next section.
   * **Option 1 (`"Request revisions to [Section Name] (via inline comments or write-in)"`) or Modal Skip with Inline Comments**: Inspect write-in instructions and inline comments on `design_draft.md` (retaining positively highlighted sections, revising or removing critiqued content), apply revisions to `design_draft.md` via your file-writing tool, notify the user, and re-present this gate. **Empty Write-in Guard (CRITICAL)**: If selected without write-in text and without inline comments, do not loop or fail; prompt in chat `"Please specify the adjustments or additions needed for [Section Name] (either via inline comments on design_draft.md or here in chat) so I can revise the draft."` and yield.

### Step 1: Ingest Predecessor Context (Concepts Brief or Notes)

1. **Context Discovery**: Read `Context File` if specified; otherwise check `./<file>`, the conversation artifact directory, and `scratch/<file>` in strict priority order:
   * **Priority 1**: `concepts_brief.md`
   * **Priority 2**: `discussion_summary.md` (ingest silently; **do NOT** prompt to start `/egm-brainstorm` or warn of deprecation)
   * **Priority 3**: If neither exists, prompt the user in chat for the problem statement, goals, and technical context, or suggest starting `egm-brainstorm` with the host's command form (e.g., `/egm:egm-brainstorm` in Claude Code and agy CLI, or the skill picker in Codex).
2. **Verify & Confirm Consensus**: Present a brief confirmation of the parsed context and get explicit approval to start drafting.
3. **Resolve Author**: Use `Author` from the ingested brief if present; otherwise use `git config user.name`, then `GIT_AUTHOR_NAME`; if neither is set, prompt the user in chat. Record it in the document header.

### Steps 2-5: Iterative Section Drafting

For each step below, append or update the section in `design_draft.md` using your file-writing tool (preserving previously approved sections) and run the **Section Approval Gate** with the step's `[Section Name]`:

* **Step 2: Overview, Goals & Problem Statement (`[Section Name] = Overview & Goals`)**: Frame the business problem and user pain points from ingested context. Write `The Problem`, `Overview`, `Goals`, and `Non-Goals` in plain-English Markdown per `references/design_doc.md`, emphasizing the *why* (user need and business value) over implementation *how*.
* **Step 3: Technical Plan (`[Section Name] = Technical Plan`)**: Synthesize the proposed high-level architecture in clear prose, identifying new components, modified files, API changes, and text-based data-flow block diagrams (ASCII or Mermaid).
* **Step 4: Alternatives (`[Section Name] = Alternatives Considered`)**: Read rejected alternatives from `Alternatives Weighed` in the ingested context (do not rely on session memory; if absent, ask the user which alternatives were rejected and why). State concrete rejection reasons (e.g., latency, scaling limits, team unfamiliarity) as `Rejected by author: [technical rationale]`; do NOT write `Rejected by maintainer` unless quoting an upstream maintainer issue, discussion, or PR URL.
* **Step 5: Detailed Implementation (`[Section Name] = Detailed Implementation`)**: Ask clarifying questions until the plan alone suffices to implement without impactful open decisions:
  1. **Single Implementation List**: List all work in one unified section.
  2. **Enumerate Every File & Rationale**: Reference **every** file changed, created, or deleted (code, docs, schemas, configs, protos, tests), explaining *what* changes and *why*.
  3. **Format Links**: Use full paths if known or clear basenames, with relative paths (`./sub/README.md`, `../sibling/README.md`) for intra-package and sibling documentation links.
  4. **NO CODE**: Generate no implementation code (pseudocode, APIs, and schemas only).

### Step 6: Write Design Document Finalization

1. **Reconcile Against Predecessor Context**: Do not grade the draft against the Zoom Out standard here (`/egm-review` Stage 5 runs that check from a fresh context). Re-read the Step 1 context file (skip if none existed) and compare it with `design_draft.md` (no Goldfish reads the brief):
   * **Contradiction**: Brief decided a question and the draft decides it differently (report every one).
   * **Addition**: Draft decides an unraised question that changes architecture, an external interface, or a dependency.

   List contradictions first, one line each quoting brief and draft, and ask the user to decide each. Do not edit the draft to match the brief on your own (drafting reads code that brainstorming did not). If nothing diverges, say so in one line. While any contradiction is open, stop and wait for the user; apply each decision to `design_draft.md` before Step 6.2.
2. **Target Directory**: Use the user-specified directory or file if given. Otherwise probe `Context File`'s directory, `docs/designs/`, and `<project>/docs/designs/`, bind `[DiscoveredPath]` (default `docs/designs/`), and present a single-select gate:
   * **Question**: `"Where should the design be saved?"`
   * **Option 0 (`"Save to detected directory: [DiscoveredPath]"`)**: Set `<DESIGN_DIR>` to `[DiscoveredPath]`.
   * **Option 1 (`"Specify custom target directory"`)**: Set `<DESIGN_DIR>` to the write-in path; if empty write-in, prompt in chat `"Please specify the custom target directory path where you would like to save the design document."` and yield.
3. **Save, Sitemap & Handoff**: If `<DESIGN_DIR>/SITEMAP.md` exists, register the design (Link, Date, Author, Components, Description). Write `design_draft.md` to `<DESIGN_DIR>/<FEATURE>.md` following the [template](references/design_doc.md) with clean Markdown, valid table syntax, and proper code fences. Provide a clickable link and recommend starting `egm-review` on `<DESIGN_PATH>` via the host's command form (e.g., `/egm:egm-review <DESIGN_PATH>` in Claude Code and agy CLI, or the skill picker in Codex).
