---
title: Check for drift
description: Compare documents with the current source code.
---

## What it does

The assistant reads each design document or README in a folder and compares it with the code. It reports only the differences: features that are missing, parts that are incomplete, and places where the code uses a different approach.

## When to use it

Use Check for drift after implementation.

## What you get

A dated report file (`{YYYY-MM-DD}_DRIFT_REPORT.md`) that lists the
differences for each document. A document with no differences shows "No drift detected."

## Example

```text
/egm-drift-report docs/designs
```

## Full instructions

The assistant follows the [Check for drift skill instructions](../../../skills/egm-drift-report/SKILL.md) in the repository.
