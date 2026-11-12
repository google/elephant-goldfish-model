---
title: Resolve findings
description: Check the findings and agree on changes.
---

## What it does

The assistant collects the review findings in `goldfish_review_report.md` and suggests a fix for each one. Findings that need your knowledge come first.

You choose what happens next:

- Comment on the report to accept, reject, or question a finding.
- Accept all the suggested fixes.
- Go through the findings one at a time.
- Continue without changes.

## When to use it

Use Resolve findings after a review. Run it in the conversation that wrote the document, because that assistant knows the reasons for each decision.

## What you get

An updated document that contains the changes you approved.

## Example

```text
/egm-resolve
```

## Full instructions

The assistant follows the [Resolve findings skill instructions](../../../skills/egm-resolve/SKILL.md) in the repository.
