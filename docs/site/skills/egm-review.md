---
title: Review
description: Review a software design with independent reviewers.
---

## What it does

Fresh reviewers read your design document in five stages. The stages check these items in order:

1. The overall approach.
2. How clear the document is to a new reader.
3. The design decisions.
4. The overall approach again, after your changes.
5. Whether someone can build from the document.

You choose how the review runs:

- Stop after each stage for your decisions.
- Run every stage and write one report.
- Review the design only.
- Review the implementation plan only.

## When to use it

Use Review for a software design document. For another type of document, use [Custom review](/skills/egm-review-loop).

## What you get

One report for each stage, or one combined report. A review uses several AI agents, so it uses more of your model allowance than a normal conversation.

## Example

```text
/egm-review design_draft.md
```

## Full instructions

The assistant follows the [Review skill instructions](../../../skills/egm-review/SKILL.md) in the repository.
