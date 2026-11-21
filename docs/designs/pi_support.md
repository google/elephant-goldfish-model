<!--
Copyright 2026 Google LLC.
SPDX-License-Identifier: Apache-2.0
-->

# Pi harness support

Proposed first-class support for [Pi](https://github.com/badlogic/pi-coding-agent)
via a Pi package manifest and installation guide. Refs #276, the
consolidated Pi support tracker (#468 was consolidated into #276 on
2026-11-18).

## Problem

Pi implements the Agent Skills specification and distributes resources
through npm and git packages. Pi core ships **no** fresh-context subagent
tool; delegation comes from a third-party subagent extension, and only
Gentle Agents in `gentle-pi` 4.5.1 has been checked. That tool is the
mechanism Goldfish reviews require, so Pi support is conditional on the
user installing such an extension. There is no documented install path for
EGM in Pi today, so Pi users must hand-copy skills and repair persona
paths manually.

### Packaging choice versus the copied-distribution alternative

Issue #276 originally proposed a copied distribution at `distributions/pi/`
with thin Pi adapters over untouched canonical `agents/*.md` (the
Claude-distribution two-layer pattern). This design instead proposes a root
`package.json` manifest with `pi.skills: ["./skills"]` so Pi discovers the
canonical skill files in place, with `agents/` and `resources/` resolved at
their canonical locations and no copied skill text. The trade-off is
recorded for maintainer evaluation: no fork to keep in sync versus
reliance on Pi's manifest discovery and path resolution behaving as
specified.

## Design

### Package manifest (no fork of skill text)

Add a root `package.json`:

```json
{
  "name": "egm",
  "version": "0.1.1",
  "keywords": ["pi-package"],
  "pi": {
    "skills": ["./skills"]
  }
}
```

Pi discovers every `skills/<name>/SKILL.md` through the package; `agents/`,
`resources/document_standards/`, and `docs/` stay at the canonical repo-root
locations. Users install with:

```sh
pi install git:github.com/google/elephant-goldfish-model@<tag>
```

or add the same source to the `packages` list in `~/.pi/agent/settings.json`
for user-global availability in every Pi session. `pi skills`-style
discovery follows the Agent Skills spec, so the `disable-model-invocation:
true` frontmatter behaves identically to Claude Code.

### Invocation

Pi registers one slash command per skill, like omp:
`/skill:egm-brainstorm <idea>`, `/skill:egm-draft`,
`/skill:egm-review <path>`, `/skill:egm-resolve`, `/skill:egm-review-loop`,
`/skill:egm-bootstrap`, `/skill:egm-drift-report`. Arguments after the
command are appended to the loaded skill instructions as the user request.

### Fresh-context delegation

Skills detect a Pi session and spawn reviewers through the `subagent` tool
supplied by a third-party subagent extension (Pi core ships none; verified
with Gentle Agents `gentle-pi` 4.5.1). The orchestrating skill instructs
each general-purpose child to read its persona file
(`agents/<persona>.md`, resolved from the package root) before reviewing.
Named subagent registration is not required: the general-purpose fallback
that `SKILL.md` already prescribes works. The extension's `subagent` tool
supports nested delegation, but EGM should keep direct dispatch from the
root context as the default because reviewer persona files forbid
workspace writes and the synthesizer nesting is unnecessary at Pi's
context sizes. Isolation observed so far is directory-based, not
harness-enforced; reviewer read-only behavior and a parent-only marker
plus negative-mutation probe remain Stage-2 verification gates, as
required by #276.

### Documentation

- New `docs/pi.md` covering install, invocation, delegation, and artifact
  locations (Pi writes artifacts to the user's working directory; there is
  no per-session scratchpad to avoid).
- An install-table row and a support-status entry in `docs/harnesses.md`.

### Shared skill text patch

Each `SKILL.md` names the harness delegation tools it expects (Codex:
`spawn_agent`, Claude: `Agent`, Antigravity: `invoke_subagent`). Add Pi's
`subagent` to that sentence and to the docs-routing note so a Pi session
resolves fresh-context dispatch without ambiguity. This is the only change
to shared skill text.

## Goals

- One-command install of the full plugin in Pi (skills + personas + standards).
- `/egm-brainstorm`, `/egm-draft`, and `/egm-review` run end-to-end with
  fresh-context reviewers.
- No duplicated or forked skill content.

## Non-Goals

- No new reviewer personas, skills, or changes to review logic.
- No Pi npm-gallery publication in this change (separable follow-up).
- No extension, theme, or prompt resources in the Pi package beyond skills.

## Verification

- Pi v1.5.0 (macOS): `/skill:egm-drift-report` invocation verified; the
  skill loaded and followed its workflow end to end in a project instance.
- Full end-to-end transcripts of `/egm-brainstorm`, `/egm-draft`, and
  `/egm-review` with fresh-context reviewers to be attached to the
  implementation PR.
- `pytest tests/unit` must pass with the added `package.json` present.
