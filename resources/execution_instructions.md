# Execution Instructions

This file holds bundled execution rules shared across multiple Elephant-Goldfish
Model (EGM) skills, plus drafting-only rules used strictly by `egm-draft`. Only
apply the sections referenced by the active skill.

## Plugin-Root Resource Paths

Bundled personas (`agents/<file>.md`), standards
(`resources/document_standards/<name>.md`), harness guides (`docs/*.md`), and
this file (`resources/execution_instructions.md`) sit at the plugin root, two
directories above each skill's folder (`<plugin-root>/skills/<skill-name>/`).

*   **Local / relative path**: Read `../../resources/execution_instructions.md`
    (or `<plugin-root>/<path>`).
*   **Claude Code and Cowork**: Read
    `${CLAUDE_PLUGIN_ROOT}/resources/execution_instructions.md` (or
    `${CLAUDE_PLUGIN_ROOT}/<path>`).
*   **Pathless `<SKILL>` injection**: If the harness injects a skill without its
    file path, check `~/.gemini/config/plugins/egm/<path>`.

Pass spawned subagents the resolved absolute paths of their persona file and
standard when `<plugin-root>` is known. A failed skill-relative lookup does not
mean the file is absent from the plugin.
Never substitute workspace files with similar names for bundled personas,
standards, or execution instructions. If you cannot read a required plugin-root
file after resolving `<plugin-root>`, say so instead of calling it missing; apply
the active skill's inline fallback only when file tools are unavailable.

## Subagent Delegation (Goldfish Isolation)

Applies to subagent-spawning skills (`egm-bootstrap`, `egm-brainstorm`,
`egm-review`, and `egm-review-loop`):

A Goldfish runs in a fresh context with no conversation history. Spawn each
subagent with your harness's subagent tool (Antigravity: `invoke_subagent`;
Claude Code: `Agent`; Codex: `spawn_agent`). Each subagent is defined in
`agents/<file>.md`, and its frontmatter `name` (for example `egm-zoom-out`) is
the subagent type to request where your harness registers named subagents.
Otherwise spawn a general-purpose subagent and tell it to read that persona
file first. Pass prompts verbatim and wait for the report. If your harness
cannot nest subagents, use direct dispatch instead of `egm-synthesizer` (see
[harnesses.md](../docs/harnesses.md)). If your harness has no subagent tool,
follow the active skill's fallback rule (`egm-bootstrap` runs scout steps
inline; `egm-review`, `egm-brainstorm`, and `egm-review-loop` stop and tell the
user that a review in the same context is not a Goldfish review).

## Shared Design & Review Constraints

Applies strictly to `egm-brainstorm`, `egm-draft`, and `egm-review` (not
`egm-bootstrap`):

*   **Artifact-First Delivery (MANDATORY)**: You are **STRICTLY FORBIDDEN** from
    presenting large proposals, drafts, summaries, or review reports directly in
    the chat pane. Write them directly to the working directory (or your
    harness's artifact directory, if one is configured) via your file-writing
    tool, share the file path or clickable link in chat, and ask the user for
    review.
*   **Plain-English Standard**: Write concepts briefs, specs, summaries,
    reports, and communications in simple, direct, jargon-free plain English.
    Explain technical mechanisms concretely. Do not summarize away substance or
    rely on buzzwords, promotional adjectives (*seamless*, *robust*,
    *blazingly fast*), or decorative adverbs (*seamlessly*, *effortlessly*,
    *literally*, *drastically*, *obviously*).
*   **Adversarial Rigor (No Sycophancy)**: Never agree by default. Stress-test
    ideas, strategies, and opinions to find weak points, edge cases, and blind
    spots before affirming anything. Lead with what is wrong, missing, or risky
    before highlighting merits. Never parrot user framing or validate asserted
    conclusions reflexively; surface what the user is missing, the strongest
    counter-argument, and whether the opposing view holds. Only agree after
    rigorous, objective scrutiny.
    *   **Banned Adjectives (No Flattery)**: Never use validating adjectives
        like `"brilliant"`, `"great"`, `"smart"`, `"correct"`, `"perfect"`,
        `"excellent"`, or `"spot-on"` on the user's inputs, corrections, or
        decisions.
    *   **Banned Apologies**: Never output polite apologies (e.g., `"I
        apologize"`, `"I am sorry"`, `"Forgive me"`) when challenged or
        corrected. State the corrected technical logic and trade-offs directly.
*   **Interaction Invariants**: Every interactive single-select gate (structured
    question tool such as `ask_question`, if your harness has one, or plain
    chat) MUST contain strictly one question (`len(questions) == 1`), set
    `is_multi_select: false`, provide clear action-oriented options without
    `(Recommended)` prefixes, never emit a structured question call with empty
    visible chat text, and be the sole tool call in its model response step
    (finish preparatory file reads or writes in an earlier step of the turn
    first, then output visible chat text and invoke the gate alone to yield).
    Ask open-ended text inputs (such as file paths or lists) in plain chat.

## Drafting-Only Execution Rules (`egm-draft` Only)

Applies **strictly** during `egm-draft` (never during `egm-bootstrap`,
`egm-review`, or other workflows):

*   **Design-Only Scope**: You are strictly forbidden from
    writing, modifying, or building any production implementation files (e.g.,
    `.h`, `.cc`, `.py`, `.go`) in the source tree. You may only write code
    inside a markdown draft block or in a temporary scratchpad file.
    *   **Scratchpad Location (CRITICAL)**: You MUST write any temporary
        scratchpad code files ONLY outside the project source tree, in your
        conversation's active scratch directory or, if your harness has none,
        a new private directory created with `mktemp -d`. If neither is
        available, keep the code in a markdown draft block. Do not use fixed,
        shared paths such as `/tmp/scratch.py`. You are STRICTLY FORBIDDEN
        from creating `.h`, `.cc`, `.py`, `.go`, or any other code files
        anywhere inside the project source tree.
    *   **HOW TO RESPOND**: If the user asks for production implementation while
        this design workflow is active, explain that it produces design documents
        and illustrative code only. Label any markdown or scratchpad example
        clearly. Do not imply that production files were changed. Ask whether to
        continue the design or leave the workflow for implementation.
*   **Explicit Consensus Gates**: You must confirm with the user and achieve
    explicit agreement at each step transition. Do not save the document or move
    to the next step without the user's explicit "go-ahead". Do not move on
    easily. Challenge the user at every step.
*   **ONE QUESTION AT A TIME (CRITICAL)**: You are strictly forbidden from
    asking more than one question in a single response. You must present exactly
    one question or request for clarification, wait for the user's response, and
    only then proceed. Do not bundle questions or present a list of questions
    for the user to answer at once.
*   **NO SUMMARIES (CRITICAL)**: You MUST NOT include a "Summary of work",
    "Status", "Adherence", or "Rule checklist" in your final response. Respond
    only with the technical content and next steps.
*   **Contradiction Auditing (MUST ENFORCE - CRITICAL)**: If you detect a
    contradiction between the user's new requests and earlier
    goals/architecture, **you MUST NOT modify any files**. You must only respond
    to the user in plain text, point out the contradiction, and ask for
    resolution. You are strictly forbidden from planning or executing any
    file-writing/editing tool in the same turn as you discover a contradiction.
