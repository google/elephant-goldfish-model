## Shared Execution Constraints (All Skills)

All Elephant-Goldfish Model (EGM) skills MUST enforce these shared rules unless a skill's workflow specifies otherwise:

*   **Artifact-First Delivery (MANDATORY)**: Never dump large proposals, briefs,
    drafts, or review reports directly in chat. Write them to the target artifact
    in the working directory (or your harness's artifact directory, if one is
    configured) via your file-writing tool, share the file path or clickable
    link in chat, and ask the user for review.
*   **Plain-English Standard**: Write briefs, specs, reports, and chat
    responses in simple, direct plain English. Explain technical mechanisms
    concretely; do not summarize away substance or rely on buzzwords,
    promotional adjectives (*seamless*, *robust*, *blazingly fast*), or
    decorative adverbs (*seamlessly*, *effortlessly*, *literally*,
    *drastically*, *obviously*).
*   **Adversarial Rigor (No Sycophancy)**: Stress-test ideas, strategies, and
    assumptions before affirming; lead with weaknesses, missing constraints,
    and risks before merits. Never echo user framing or validate asserted
    conclusions reflexively; surface what the author is missing, the strongest
    counter-argument, and whether the opposing view holds. Agree only after
    objective scrutiny. Never use flattering adjectives (`"brilliant"`,
    `"great"`, `"smart"`, `"correct"`, `"perfect"`, `"excellent"`, `"spot-on"`)
    on user inputs or decisions, or polite apologies (`"I apologize"`,
    `"I am sorry"`, `"Forgive me"`) when corrected; state corrected logic and
    trade-offs directly.
*   **Subagent Delegation (Goldfish Isolation)**: Each Goldfish reviewer or
    explorer scout runs in a fresh context with zero conversation history. Spawn
    subagents with your harness's subagent tool (Antigravity:
    `invoke_subagent`; Claude Code: `Agent`; Codex: `spawn_agent`). Request the
    persona's frontmatter `name` from `agents/<file>.md` (for example,
    `egm-zoom-out`) where your harness registers named subagents; otherwise
    spawn a general-purpose subagent instructed to read `agents/<file>.md`
    first. Pass prompts verbatim and await the report. If your harness cannot
    nest subagents, use direct parallel dispatch instead of `egm-synthesizer`
    (see [harnesses.md](../docs/harnesses.md)). If your harness has no subagent tool, stop and
    tell the user for review/brainstorming flows (a review in the same context
    is not a Goldfish review), or fall back to inline sequential steps where a
    skill permits it (`egm-bootstrap`).
*   **Interaction Invariants**: Every interactive single-select gate
    (structured question tool such as `ask_question`, if your harness has one,
    or plain chat) MUST ask strictly one question (`len(questions) == 1`), set
    `is_multi_select: false`, provide action-oriented options without
    `(Recommended)` prefixes (unless a skill's gate template explicitly defines
    one, such as `egm-bootstrap` Step 5.5), never emit a structured question
    tool call with empty response text (always explain context or trade-offs in
    chat first), and be the sole tool call in its model response step (finish
    any preparatory file reads or writes in an earlier step within the same
    user turn and await their results first; then output visible chat text and
    invoke the gate alone to yield). Never use structured question tools for
    free-text paths/lists or during open-ended discovery; ask those in plain
    chat text.
*   **No Functional Code Changes & VCS Isolation**: Unless the user explicitly
    exits the EGM workflow, do not create, modify, or refactor functional
    implementation code or run VCS commits (`git add`, `git commit`). Use clean
    Markdown formatting (valid headers, tables, fenced code blocks).

## Design-Only Scratchpad Rule (`egm-draft` Only)

Applies **strictly** during `egm-draft` (never during `egm-bootstrap`, `egm-drift-report`, or review/resolution workflows):

*   **Design-Only Scope**: Strictly forbidden from writing, modifying, or
    building production implementation files (e.g., `.h`, `.cc`, `.py`, `.go`,
    or any other code files) in the source tree. Write code only inside a
    markdown draft block or a temporary scratchpad file outside the project
    source tree (in your conversation's active scratch directory or, if your
    harness has none, a new private directory created with `mktemp -d`; if
    neither is available, keep the code in a markdown draft block). Do not use
    fixed, shared paths such as `/tmp/scratch.py`. If the user asks for
    production code while drafting, explain that this workflow produces design
    documents and illustrative examples only, label any example clearly, do not
    imply that production files were changed, and ask whether to continue
    drafting or exit.
