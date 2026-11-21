<!--
Copyright 2026 Google LLC.
SPDX-License-Identifier: Apache-2.0
-->

# Pi integration

[Pi](https://github.com/badlogic/pi-coding-agent) loads EGM as a Pi package:
one manifest entry exposes the seven skills; personas and document standards
stay at the repo-root `agents/` and `resources/` locations.

## Install

```sh
pi install git:github.com/google/elephant-goldfish-model@<tag>
```

Or add the same source to the `packages` list in
`~/.pi/agent/settings.json` to make the skills available in every Pi
session, project and global. Start a fresh session after installation and
run `/reload` if Pi was already running.

Confirm discovery: the seven skills appear as slash commands
(`/skill:egm-brainstorm`, `/skill:egm-draft`, `/skill:egm-review`,
`/skill:egm-resolve`, `/skill:egm-review-loop`, `/skill:egm-bootstrap`,
`/skill:egm-drift-report`). `disable-model-invocation: true` means Pi hides
them from automatic skill selection, matching upstream behavior; invoke them
explicitly. Arguments after the command are passed to the skill as the user
request, for example `/skill:egm-review docs/designs/webhooks.md`.

## Path resolution

From `skills/<skill>/SKILL.md`, resolve bundled `agents/`,
`resources/document_standards/`, and `docs/` paths against the package root
(the directory that contains `package.json`). Resolve `references/` against
the active skill's directory. Resolve user documents and generated artifacts
against the user's working directory. Pi does not use a per-session
scratchpad for package resources.

## Fresh-context reviewers

Skills spawn reviewers through Pi's `subagent` tool. Pi's default
general-purpose child has no conversation history from the parent, which is
the Goldfish isolation requirement. Each child first reads its persona file
(for example `agents/zoom_out.md`) from the package root, then reviews. Use
direct dispatch from the root context; Pi can nest subagents, but EGM's
reviewer personas forbid workspace writes and the direct-dispatch fallback
that the skills already prescribe is the default.

Reviewer reads are read-only by persona instruction, not by tool policy; if
your Pi configuration grants children write access, prefer the read-only
child profile where your setup offers one.

## Artifacts

Write `concepts_brief.md`, `design_draft.md`, review reports, and drift
reports to the user's working directory. Approved specifications belong
under `docs/designs/` in the user's project.
