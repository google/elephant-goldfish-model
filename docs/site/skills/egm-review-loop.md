---
title: Custom review
description: Choose reviewers and standards for your document.
---

## What it does

You choose the document, the reviewers, and the standard that each reviewer applies. Fresh reviewers read the document. The assistant applies the fixes you approve. The review repeats until two rounds in a row find no serious problem, or until it reaches five rounds. At five rounds, the assistant asks you how to continue.

The seven built-in reviewers check structure, writing style, clarity for a new reader, design decisions, readiness to build, technical detail, and unnecessary complexity. You can also give a reviewer your own standard as a file.

## When to use it

Use Custom review when you want to choose the reviewers and the standards. It reviews design documents, READMEs, feature specifications, and plans. It also reviews other documents, for example a project proposal or a brief. Also use it to review one part of a long document.

## What you get

A report of the findings (`goldfish_review_report.md`) and a document that contains the fixes you approved.

## Example

```text
/egm-review-loop
Review study-space-plan.md.
Help me choose reviewers and standards
for the opening schedule and responsibilities.
```

## Full instructions

The assistant follows the [Custom review skill instructions](../../../skills/egm-review-loop/SKILL.md) in the repository.
