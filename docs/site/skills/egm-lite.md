---
title: Lite
description: Fast-track small iterations, spec revisions, refactors, and bug fixes.
---

## What it does

The assistant executes a rapid, decoupled 5-phase engineering protocol for small changes without the overhead of a full design specification lifecycle:

1. **Critique Pause**: Probes code invariants and tags untested assumptions before touching code.
2. **Checklist**: Generates a lightweight task list in `egm_lite_checklist.md`.
3. **Execution**: Implements approved changes and verifies local test passes.
4. **Adversarial Review**: Spawns an isolated Goldfish subagent to audit the code diff against race conditions, edge cases, and missing tests.
5. **Resolution Gate**: Contextual triage of subagent findings into proposed fixes or evidence-backed contests.

## When to use it

Use Lite for small, rapid iterations, specification revisions, code refactors, or bug fixes where writing a full multi-document specification is unnecessary.

## What you get

A tested code change accompanied by an execution checklist in `egm_lite_checklist.md` and an adversarial review pass.

## Example

```text
/egm-lite Fix lookup latency in RequestHandler by caching validated sessions
```

## Full instructions

The assistant follows the [Lite skill instructions](../../../skills/egm-lite/SKILL.md) in the repository.
