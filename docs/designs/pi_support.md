<!--
Copyright 2026 Google LLC.
SPDX-License-Identifier: Apache-2.0
-->

# Pi harness support

Proposed first-class support for [Pi](https://github.com/badlogic/pi-coding-agent)
via a Pi package manifest and installation guide. Refs #468.

## Problem

Pi implements the Agent Skills specification, distributes resources through
npm and git packages, and provides a fresh-context subagent tool
(`subagent`) — the mechanism Goldfish reviews require. There is no documented
install path for EGM in Pi today, so Pi users must hand-copy skills and
repair persona paths manually.

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

Skills detect a Pi session and spawn reviewers through Pi's `subagent` tool.
The orchestrating skill instructs each general-purpose child to read its
persona file (`agents/<persona>.md`, resolved from the package root) before
reviewing. Named subagent registration is not required: the general-purpose
fallback that `SKILL.md` already prescribes works. Pi's `subagent` tool
supports nested delegation, but EGM should keep direct dispatch from the
root context as the default because reviewer persona files forbid workspace
writes and the synthesizer nesting is unnecessary at Pi's context sizes.

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
