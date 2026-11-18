---
name: egm-ask
license: Apache-2.0
disable-model-invocation: true
description: >-
  Read-only contextual help for the Elephant & Goldfish Model (EGM). Checks
  which EGM artifacts exist on disk, reads installed skill descriptions and
  harness docs, and replies in chat with a short answer and up to three
  suggested next steps.
---

# EGM Ask: Read-Only Contextual Help & Next-Step Guidance

When running in Codex or ChatGPT Work, first read [Codex integration](../../docs/codex.md).
In Claude Code or Cowork, read `${CLAUDE_PLUGIN_ROOT}/docs/claude.md` first.

Advisory only. Do **not** write files, run other skills, spawn subagents, or
change the state of any in-progress skill. Do **not** run shell commands such as
`git status`.

## Step 1: Classify the Question

Sort the user's question into one of four types (if no question is given, treat
it as **Next step**):

| Type | Example | Files to read (read-only) |
| :--- | :------ | :------------------------ |
| **Next step** | "What do I do now?" | Artifact names in the workspace / EGM artifact directory and the stage table below |
| **Skill choice** | "Which skill checks my README?" (or EGM task requests like "Fix my draft") | `skills/*/SKILL.md` frontmatter `description` fields |
| **Troubleshooting** | "The reviewer cannot read its persona." | `docs/harnesses.md` and the harness guide (`docs/claude.md` or `docs/codex.md`) |
| **Out of scope** | "How do I fix this TypeScript error?" | None. Reply that `/egm-ask` only covers EGM and stop. |

## Step 2: Detect the Workflow Stage (for Next-Step Questions)

Check which EGM artifacts exist on disk (do not read full contents unless needed):

- No EGM artifacts: suggest `/egm-brainstorm` (new feature/architecture) or `/egm-lite` (small bug fix / refactor).
- `concepts_brief.md` present, no `design_draft.md`: suggest `/egm-draft`.
- `design_draft.md` present, no `goldfish_review_report.md`: suggest `/egm-review`.
- `goldfish_review_report.md` present: suggest `/egm-resolve`.
- Approved design doc in `docs/designs/` without drift check: suggest `/egm-drift-report`.

## Step 3: Reply

Reply in chat with:
1. A short, direct answer (citing the relevant doc or artifact if applicable).
2. At most **three** suggested next steps, formatted in the command style expected by the user's harness.
