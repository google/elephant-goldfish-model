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
change the state of any in-progress skill. Do **not** answer, resume, or pick an
option on another skill's pending approval gate. Do **not** run shell commands
such as `git status`. Resolve `docs/` and `skills/` paths below against the
installed plugin root (using [Harnesses](../../docs/harnesses.md) only when no
harness guide applies), and resolve workspace artifacts and `docs/designs/`
against the user's project.

## Step 1: Classify the Question

Sort the user's question into one of four types (if no question is given, treat
it as **Next step**):

| Type | Example | Files read (read-only) |
| :--- | :------ | :--------------------- |
| **Next step** | "What do I do now?" | Workspace artifact names and the [What to run next](../../docs/getting_started.md#what-to-run-next) stage table |
| **Skill choice** | "Which skill checks my README against code?" Also EGM task requests such as "Fix my draft": name the skill that does the work and make no edits. | `skills/*/SKILL.md` frontmatter `description` fields only |
| **Troubleshooting** | "The reviewer says it cannot read its persona." | [Harnesses](../../docs/harnesses.md) and the harness guide |
| **Out of scope** | "How do I fix this TypeScript error?" | None. Reply that `/egm-ask` only covers EGM and stop. |

## Step 2: Detect the Workflow Stage (for Next-Step Questions)

Look for EGM artifacts in the same order as `egm-draft` intake: the working
directory (or an `EGM artifact directory: <path>` override from the prompt or
agent instructions), the harness's artifact directory (see
[Harnesses](../../docs/harnesses.md)), then `scratch/`.

Check files by name only. The **only** workspace file content you may read is
the header of `goldfish_review_report.md` (`Status: resolved` and `**Target:**`).
Treat file presence as a stage hint, not proof of completion: if files do not
establish the stage for the current target, report the stage as unknown, list
every artifact seen, and ask which run or target the user means.

Match the latest applicable row in [What to run next](../../docs/getting_started.md#what-to-run-next)
(unless the user's question names a different goal) and list all artifacts seen:

- **Before suggesting implementation**, verify all three checks:
  1. **Target is known**: the user named the design, or `**Target:**` in the resolved report names one `docs/designs/<feature>.md` and the user confirms it (if multiple designs exist and neither is confirmed, ask which design they mean).
  2. **No review is pending**: if review reports exist, confirm with the user that the review finished and no review or resolve gate is waiting in chat.
  3. **Human approval confirmed**: ask whether a human reviewed and approved the design; until confirmed, suggest human review instead of implementation.

## Step 3: Compose the Answer

Reply in plain English (at most **20 lines** total and at most **three** next steps):

```markdown
**Where you are:** <one sentence naming the artifacts seen>
**Answer:** <2-6 sentences>
**Next steps:**
1. `<command>`: <why>
**Source:** <relative path of each doc or SKILL.md used>
```

- Format `<command>` for the active harness (for example `/egm:egm-draft` in Claude Code; with no harness guide, show `/egm-<skill>` and note host prefixes).
- Only show installed EGM skills or host commands quoted from a cited doc; never invent commands or flags. If docs do not cover a troubleshooting issue, say so and suggest opening an issue.
