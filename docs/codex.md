<!--
Copyright 2026 Google LLC.
SPDX-License-Identifier: Apache-2.0
-->

# Codex integration

## Check capabilities before starting

The OpenAI archive contains `egm-in-chat` alongside the full EGM skills in one
`egm` plugin. Check the current chat's tools before intake, artifact creation,
or reviewer dispatch. Web and desktop labels do not establish capabilities.

- For document work from pasted text or uploads, use `egm-in-chat`. It needs
  no shell or subagents and labels its critique as same-context.
- Full EGM workflows require readable bundled resources and writable artifacts.
  Before any Goldfish stage, also verify a native subagent tool can start a
  fresh context, following the isolation rules below. Never simulate reviewers
  or silently substitute same-context critique for independent review.
- Repository workflows additionally require access to the requested repository
  and command execution. Do not assume that installing the plugin grants either.

If a required capability is absent, stop that full workflow before starting,
name what is missing, and offer `egm-in-chat` if it is in the installed skill
inventory. Continue with same-context document work only if the user chooses it.
Repository-based installs that expose only the eight canonical skills must not
claim the document skill is installed.

## Install and locate the plugin

For the desktop app, install the [published EGM plugin](https://chatgpt.com/plugins/plugins_6aeb90f47ec88191a3c107e01d3eb357). This listing is desktop-only.

For Codex CLI, install the whole plugin, including its personas and standards:

```sh
codex plugin marketplace add google/elephant-goldfish-model
codex plugin add egm@egm
```

Start a fresh session after installation. Select the installed `egm` skill
from the available skills. Use its discovered absolute `SKILL.md` path;
do not assume a particular cache directory, version, or checkout location.

From `<plugin>/skills/<skill>/SKILL.md`, the plugin root is three parent
directories above the file. Resolve bundled `agents/`, `resources/`, and
`docs/` paths against that root. Resolve `references/` against the active
skill's directory. Resolve user documents and generated artifacts against
the user's working directory. Never substitute similarly named files in the
user's project for bundled personas or standards.

If the user's prompt or agent instructions file (`AGENTS.md`) has a line
`EGM artifact directory: <path>`, write briefs, drafts, and reports to that
folder. Resolve a relative path against the working directory. If a path from
`AGENTS.md` resolves outside the working directory, after following symbolic
links, ask the user to confirm it before creating the folder or writing there.
If they decline or no one can confirm, use the working directory and say why.
Create the folder if it does not exist.

In ChatGPT Work, a skill may be exposed through a cloud resource identifier
while supporting files live in the installed local bundle. Use the installed
path supplied by the skill inventory or installation metadata for those files;
do not construct cloud resource identifiers for arbitrary supporting paths.
If no installed path is available, report the missing capability instead of
guessing a cache location. Read reviewer filenames and frontmatter from the
bundle: a role such as `egm-design` maps to `agents/design_critic.md`, not
`agents/design.md`. Confirm each resolved path before dispatch.

## Fresh-context reviewers

Inspect the available native subagent tool schema. Tool names can be
namespaced and vary by Codex version. When `spawn_agent` exposes
`fork_context`, explicitly set `fork_context: false` for every Goldfish.
When the schema instead exposes `fork_turns`, use `fork_turns: "none"`.
This applies to reviewers launched by a synthesizer too. Use a general-purpose agent
and pass absolute paths to the persona, standards, target document, and
explicitly selected reading list. Do not pass the parent transcript, private
reasoning, or answers the document is supposed to explain.

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

The `fork_context: false` and `fork_turns: "none"` options concern parent
conversation turns. They do not prove that Codex excludes host instruction
files. Issue [#237](https://github.com/google/elephant-goldfish-model/issues/237)
reports that Codex CLI 0.166.0 injected project and user `AGENTS.md` files
despite `fork_turns: "none"`. Treat instruction-file exclusion as unverified
unless a separate child-context probe confirms it for the tested host version.

## Questions and artifacts

The shared skills' question payloads describe the intended interaction, not a
literal Codex API. Use a structured question tool only when it is available
and permitted in the current mode, mapping to its actual schema. Otherwise
ask one plain-text question and wait for the answer. Preserve the skill's
readiness and section approval gates; tool unavailability is not approval.

Link generated artifacts with absolute-path Markdown links such as
`[design draft](/absolute/project/design_draft.md)`. For paths containing
spaces use `[design draft](</absolute/my project/design_draft.md>)`.
Do not use `file://` links in Codex chat.

## Verification

Run the offline packaging checks with `pytest tests/unit`. The opt-in native
workflow tests are documented in [TESTING.md](https://github.com/google/elephant-goldfish-model/blob/main/TESTING.md). They require
an authenticated Codex CLI and consume model usage. Installing or discovering
the plugin alone does not establish end-to-end workflow support.

## ChatGPT

Install the [published EGM plugin](https://chatgpt.com/plugins/plugins_6aeb90f47ec88191a3c107e01d3eb357) in the ChatGPT desktop app. This listing is desktop-only; it does not establish support for cloud Work sessions.

### Test a local package

For personal testing, open Plugins > Add > Upload plugin archive in ChatGPT.
Package the runtime files from the repository root:

```sh
python3 scripts/pack_plugin.py --target openai --output /tmp/egm-chatgpt
```

Use a fresh output directory. The candidate `egm-openai.zip` contains all nine
skills under the existing `egm` identity. Upload the same archive for private
testing in ChatGPT web and desktop, then use **Try in chat** in clean threads.
The published listing remains desktop-only until a revised release is approved
and published; these source changes do not update it.
Keep repository marketplace catalogs and development files outside this archive.
The candidate omits the plugin-wide local-executor requirement: document work
needs none, while full workflows check their requirements before starting.
The portable manifest's OpenAI extension and Codex compatibility manifest
retain matching listing metadata. The Claude build and repository-based coding
harness installs have eight canonical skills, including engineering `egm-lite`.
The OpenAI archive adds document-first `egm-in-chat` to those eight; both new
workflows are part of the v0.2.0 candidate.
Keep `.claude-plugin/` outside the OpenAI archive: its agent adapters belong
to the Claude Code integration. Public directory plugins cannot include hooks.

Before merge or publication, record the archive checksum, package version,
host version or test date, installation, skill discovery, and observed tools
for each surface. Complete document brainstorm, draft, and same-context review
on both. In a chat without the required tools, invoke a full skill and verify
it stops with a capability explanation. In a capable desktop chat, run
`egm-brainstorm`, `egm-draft`, and `egm-review` through the installed package,
retaining native reviewer-isolation evidence. Mark unperformed checks `not run`.
Offline packaging checks do not establish that this gate passed.

Enterprise, Business, and Edu workspaces can import the plugin via Admin > Plugins > Add > Import marketplace.
Set the repository URL to `https://github.com/google/elephant-goldfish-model` and marketplace path to `.agents/plugins`.
Skills are accessible via `@egm` for direct interaction.
Check the native tools in the current chat before starting a Goldfish review.
Some ChatGPT Work sessions expose native `spawn_agent` with `fork_turns: "none"`.
Use the fresh-context instructions above when those tools are available. If
they are absent, stop and report that isolation is unavailable; never simulate
reviewers in the parent context. Availability in one Work session does not
establish support across every ChatGPT mode or account.
