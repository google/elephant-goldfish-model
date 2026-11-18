---
title: EGM
description: Choose the useful next workflow from your task, progress, and available tools.
---

## Start here

Use `/egm` when you know what you want to do but are unsure which EGM skill
fits. In a host with a skill picker, select **EGM**. Some hosts namespace the
command as `/egm:egm`.

Describe the task or provide the document, brief, or diff. EGM selects an
existing workflow and starts its next valid phase. It resumes active work
instead of restarting it and keeps each workflow's approval pauses.

Small engineering changes use Lite. Larger ideas start with Brainstorm;
aligned briefs go to Draft. Existing designs, review findings, codebase
documentation, and drift checks go to their matching skills. When the optional
`egm-in-chat` skill is installed, document-only work can use it with clearly
labelled same-context critique.

EGM checks the tools actually available for the current phase. It names
missing capabilities and never simulates independent reviewers. You can
still choose any specialist skill directly.

## Example

```text
/egm Here is our design and the review findings. Help me work through them.
```

## Full instructions

Read the [EGM routing instructions](../../../skills/egm/SKILL.md).
