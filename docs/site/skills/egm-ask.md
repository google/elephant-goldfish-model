---
title: Ask for help
description: Find out what to run next or how to fix an EGM setup problem, without changing files.
---

## What it does

The assistant answers a question about EGM. To suggest a next step, it checks which EGM files are in your workspace, such as `concepts_brief.md` or `goldfish_review_report.md`, and compares them with the workflow in the getting started guide. It suggests at most three steps.

It only reads. It does not edit files, run commands other than listing and reading files, or start another skill.

## When to use it

Use Ask for help when you are not sure which skill comes next, which skill fits a task, or why a skill did not work in your coding assistant. Questions that are not about EGM are out of scope.

## What you get

A short answer in the conversation. It names the skill to run, with the command written the way your coding assistant expects. A file in your workspace is treated as a hint, not as proof that a step finished, so the assistant may ask you to confirm.

## Example

```text
/egm-ask What do I do after the review?
```

## Full instructions

The assistant follows the [Ask for help skill instructions](../../../skills/egm-ask/SKILL.md) in the repository.
