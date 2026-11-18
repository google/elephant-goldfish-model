---
title: Ask
description: Check where you are in the workflow, choose the right skill, or troubleshoot an issue.
---

## What it does

The assistant answers questions about EGM and about your current workspace without changing files or running other skills:

1. **Next step**: Checks which EGM artifacts exist on disk (such as `concepts_brief.md`, `design_draft.md`, checked-in designs under `docs/designs/`, or review reports) and suggests what to run next.
2. **Skill choice**: Reads installed skill descriptions and recommends the command that matches your goal.
3. **Troubleshooting**: Cites the relevant setup or harness guide when a command, subagent, or permission check fails.

## When to use it

Use Ask when starting in an unfamiliar workspace, returning to a project after a break, choosing between skills, or diagnosing a harness issue without disturbing an in-progress workflow gate.

## What you get

A short, read-only reply in chat with your detected stage, a direct answer citing the relevant EGM documentation, and up to three suggested commands formatted for your assistant.

## Example

```text
/egm-ask What should I run next?
```

## Full instructions

The assistant follows the [Ask skill instructions](../../../skills/egm-ask/SKILL.md) in the repository.
