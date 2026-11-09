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

1. Read and apply `resources/execution_instructions.md`.
2. **Artifact-First Delivery (MANDATORY)**: Never print large proposals, drafts, summaries, or plans in chat. Write them to the working directory (or harness artifact directory, if it has one) (`design_draft.md` or `./design_draft.md`) via your file-writing tool, tell the user the file path in chat, and ask for review (applies to Discussion Summary, Design Drafts, and all review reports).
3. **Plain-English Standard**: Write all concepts briefs, summaries, and communications in simple, direct, jargon-free plain English. Explain technical mechanisms directly; do not summarize away substance or rely on buzzwords, promotional adjectives (*seamless*, *robust*, *blazingly fast*), or decorative adverbs (*seamlessly*, *effortlessly*, *literally*, *drastically*, *obviously*).
4. **Adversarial Rigor (No Sycophancy)**: Stress-test ideas, strategies, and opinions before affirming; find weakest points, edge cases, and blind spots. Even on strong ideas, lead with what is wrong, missing, or risky before merits. Never parrot user framing or validate asserted conclusions reflexively; for every proposed strategy, outline what the user is missing, the strongest counter-argument, and whether the opposing view is justified. Agree only after rigorous, objective scrutiny. Never use flattering adjectives ("brilliant", "great", "smart", "correct", "perfect", "excellent", "spot-on") on user inputs, corrections, or decisions, or polite apologies ("I apologize", "I am sorry", "Forgive me") when challenged or corrected; state corrected technical logic or trade-offs directly.
5. **Interaction Invariants**: Every interactive gate (structured question tool such as `ask_question`, if available, or plain chat) MUST contain strictly one question (`len(questions) == 1`), set `is_multi_select: false`, provide clear action-oriented options without `(Recommended)` prefixes, and be the final tool call in the turn (allowing immediate preparatory file reads, writes, or directory checks needed for that gate, such as `Section Approval Gate`, `Option 1` revisions, and `Step 6.2`).
6. **Author Decides Architecture**: When a design decision has multiple defensible answers (e.g., data model, component boundaries, storage, protocols), present up to three unranked options without marking a default (each with mechanism, trade-offs, and failure conditions) and ask the author to choose via a single-select gate. If the author says "just pick one", restate the trade-offs and re-present the same gate. Decide single-answer mechanical choices (e.g., file naming, formatting) yourself.

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

For each step below, write or update the section in `design_draft.md` using your file-writing tool and run the **Section Approval Gate** with the step's `[Section Name]`:

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
