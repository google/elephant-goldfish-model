<!--
Copyright 2026 Google LLC.
SPDX-License-Identifier: Apache-2.0
-->

# Muse integration

Muse loads EGM through its Claude-compatible plugin path: no Muse-native
manifest is needed. The plugin validates with all seven skills and all nine
reviewer adapters supported.

## Install and locate the plugin

Install the whole plugin, including its personas and standards, from a local
path:

```sh
git clone https://github.com/google/elephant-goldfish-model.git
muse plugins install ./elephant-goldfish-model --scope user
muse plugins approve egm
```

`marketplace add` on this repository discovers zero plugins: Muse reads the
Codex catalog (`.agents/plugins/marketplace.json`) first and skips its entry,
so it never falls through to the Claude catalog. Install from a local path
instead, and keep the source free of symlinks (remove scratch directories
such as `.venv/` first; the installer rejects symlink entries). Approval is
required once: skills stay active without review while
the plugin is enabled, but the nine reviewer agent definitions need
`approve` before activation.

Start a fresh session after installation. The skills surface as
`plugin:egm:egm-*` with user-invocable-only activation; confirm with
`muse skills list --source plugin`. Use each skill's discovered absolute
`SKILL.md` path; do not assume a particular cache directory, version, or
checkout location.

From `<plugin>/skills/<skill>/SKILL.md`, the plugin root is three parent
directories above the file. Resolve bundled `agents/`, `resources/`, and
`docs/` paths against that root. Resolve `references/` against the active
skill's directory. Resolve user documents and generated artifacts against
the user's working directory. Never substitute similarly named files in the
user's project for bundled personas or standards.

Offline pre-check without installing: `muse plugins validate <path>`
reports the plugin valid with 7 supported skills and 9 supported agents.
Warnings are expected (`multiple-manifests` picks the Claude manifest over
the Codex one; Claude-only fields such as presentation metadata, `color`,
and unknown agent frontmatter keys are ignored). Installing or discovering
the plugin alone does not establish end-to-end workflow support.

If the user's prompt or agent instructions file (`AGENTS.md`) has a line
`EGM artifact directory: <path>`, write briefs, drafts, and reports to that
folder: resolve a relative path against the working directory, and create the
folder if it does not exist.

## Fresh-context reviewers

Muse imports the nine Claude reviewer adapters as supported agent
definitions (`egm/egm-design`, `egm/egm-comprehension`, and so on), but
every agent tool projection is unsupported: Claude tool allowlists do not
restrict Muse reviewers, so do not assume reviewers are read-only. Inspect
the available native subagent tool schema before dispatching; tool names can
be namespaced and vary by Muse version.

Use a named reviewer agent when the session exposes it, and pass absolute
paths to the persona, standards, target document, and explicitly selected
reading list. Do not pass the parent transcript, private reasoning, or
answers the document is supposed to explain. When named agents are
unavailable, fall back to a general-purpose subagent that reads
`agents/<persona>.md` first. On Muse 1.4.14 the named `egm/egm-*`
definitions report `trusted_enabled` in the plugin inventory but spawning
one is rejected (`agent_definition_unavailable`), so the general-purpose
fallback is the working path in practice.

Require the reviewer to read its persona, target, and every supplied standard
before returning findings. A missing read or inaccessible file is an incomplete
review, not a clean result. Verify native tool results when the host exposes
them; a parent-written completion summary is not equivalent evidence.

Wait for actual reviewer completion before synthesizing findings. Propagate
failures and timeouts; a launched reviewer is not a completed review. If
nesting is unavailable, dispatch reviewers directly from the parent while
preserving the same isolation. If the available tool cannot establish a fresh
context, stop the Goldfish review and report that limitation.

Fresh conversation context does not isolate the filesystem, configured memory
services, or project instructions. Do not retrieve conversation history or
memory to supply missing design context. An isolation test should use a unique
parent-only marker and check the actual child result, not the parent's claim.

## Questions and artifacts

The shared skills' question payloads describe the intended interaction, not a
literal Muse API. Use a structured question tool only when it is available
and permitted in the current mode, mapping to its actual schema. Otherwise
ask one plain-text question and wait for the answer. Preserve the skill's
readiness and section approval gates; tool unavailability is not approval.

Link generated artifacts with absolute-path Markdown links such as
`[design draft](/absolute/project/design_draft.md)`. For paths containing
spaces use `[design draft](</absolute/my project/design_draft.md>)`.
Do not use `file://` links in Muse chat.

## Verification

Run the offline packaging checks with `pytest tests/unit`. The end-to-end
workflow fixture (brainstorm, draft, and uninterrupted review through the
installed plugin) passed on Muse 1.4.14 on 2026-10-30 with the
general-purpose reviewer fallback described above; see the [harness test
record](https://github.com/google/elephant-goldfish-model/blob/main/TESTING.md#harness-test-record).
Installing or discovering the plugin alone does not establish end-to-end
workflow support.
