---
title: Lite
description: Fast-track small iterations, spec revisions, refactors, and bug fixes.
---

## What it does

The assistant executes a rapid, decoupled 5-phase engineering protocol for small changes without the overhead of a full multi-document specification lifecycle:

1. **Critique Pause**: Probes code invariants and tags untested assumptions before touching code.
2. **Checklist & Automatic Spec Review**: Generates a lightweight task list in `egm_lite_checklist.md` and automatically spawns a fresh-context Goldfish subagent to audit the checklist before implementation begins.
3. **Execution**: Records the starting review baseline, implements the approved checklist items, and verifies local test passes.
4. **Optional Diff Re-Review**: On request (`review` or `goldfish`), spawns an isolated Goldfish subagent to audit the workspace changes against race conditions, edge cases, and missing tests.
5. **Resolution Gate**: Triages pre-implementation specification findings or post-implementation diff findings into proposed fixes or evidence-backed contests before updating the checklist or executing changes.

## When to use it

Use Lite for small, rapid iterations, specification revisions, code refactors, or bug fixes where writing a full multi-document specification is unnecessary.

## What you get

A tested change accompanied by an execution checklist in `egm_lite_checklist.md`, an automatic pre-implementation Goldfish specification review, and an optional post-implementation Goldfish diff re-review.

## Example

```text
/egm-lite Fix lookup latency in RequestHandler by caching validated sessions
```

## Full instructions

The assistant follows the [Lite skill instructions](../../../skills/egm-lite/SKILL.md) in the repository.
