# Harnesses

EGM is one set of skills and personas. This repository serves as the
plugin source for each supported harness. No harness gets a fork of the skill
text.

## Install

| Harness | Install |
| --- | --- |
| Antigravity | `agy plugin install https://github.com/google/elephant-goldfish-model` (or `/plugin` in the IDE) |
| Claude Code | `claude plugin marketplace add google/elephant-goldfish-model && claude plugin install egm@egm` |
| Claude Cowork | Install from claude.ai/plugins or the Cowork plugin panel via marketplace `google/elephant-goldfish-model` |
| Codex | `codex plugin marketplace add google/elephant-goldfish-model && codex plugin add egm@egm` |
| ChatGPT | Personal testing: Plugins > Add > Upload plugin archive; see [packaging](codex.md#chatgpt). Workspace import: Admin > Plugins > Add > Import marketplace, repo URL `https://github.com/google/elephant-goldfish-model`, path `.agents/plugins` |

Install the whole plugin. Skill-only installers that copy `skills/` alone
break EGM, because the skills read `agents/` and
`resources/document_standards/` at run time.

## Manifests

Root `plugin.json` is the canonical source for plugin identity, version,
description, and publisher metadata. It declares the portable Agent Plugins
1.0.0 schema. Update shared values there first, then update the compatibility
manifests; unit tests reject metadata drift. Keep platform-specific fields in
their existing manifests until installation tests justify removing them.

Marketplace files are discovery catalogs pointing to this package, not copies
of its skills. In particular, `.agents/plugins/` contains the Codex catalog,
while `agents/` contains reviewer personas. All hosts share the same `skills/`,
`agents/`, and `resources/` content.

| Harness | Manifest | Skills | Subagents |
| --- | --- | --- | --- |
| Antigravity | `plugin.json` | `skills/` (default) | `agents/` (default) |
| Claude Code | `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | `skills/` (default) | Claude adapters and orchestrators listed in `plugin.json` `agents` |
| Claude Cowork | `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | `skills/` (default) | Subagents run inside Cowork; hooks n/a |
| Codex | `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json` | `skills` path | Not shipped; general-purpose subagent reads the persona file |
| ChatGPT | `plugin.json`, `.codex-plugin/plugin.json`; `.agents/plugins/marketplace.json` for workspace import | `skills` path | Detect native tools in the current session; general-purpose agent reads the persona |

Persona prompts live in `agents/`, the directory Antigravity
scans for subagents. Each persona has `name` and `description` frontmatter, so
harnesses that load `agents/*.md` register them as named subagents
(`egm-design`, `egm-zoom-out`, and so on).

When you add a reviewer persona, add a Claude adapter under
`.claude-plugin/agents/` and list it in `.claude-plugin/plugin.json`.
The adapter reads the shared persona and sets Claude's read-only tools and
context isolation. This avoids imposing Claude tool names on other hosts.

## Delegation

Skills say "spawn a subagent" and name a persona. Each harness maps that
phrase to its own tool:

| Harness | Subagent tool | Named personas | Nesting |
| --- | --- | --- | --- |
| Antigravity | `invoke_subagent` | Yes | Yes |
| Claude Code | Agent (Task) tool | Yes | Up to 3 levels by default |
| Claude Cowork | Cowork subagents | Yes | Subagents run inside Cowork |
| Codex | Native spawn/wait tools; inspect the available schema | No | Detect at runtime; direct dispatch fallback |
| ChatGPT | Native spawn/wait tools when exposed by the current Work session | No | Detect at runtime; direct dispatch fallback |

Where a harness has no named persona, the skill spawns a general-purpose
subagent and tells it to read `agents/<file>.md` first. If a harness cannot
nest subagents, use direct dispatch instead of the synthesizer.

A Goldfish review needs a fresh context. If a harness has no subagent tool,
the review skills stop instead of running in the same context. Check actual
tool availability rather than inferring it from the product name. This applies
to ChatGPT modes that do not expose native fresh-context delegation.

## Support Status & Contributing Other Harnesses

**Antigravity**, **Claude Code**, and **Codex** pass automated installation, reviewer isolation, and end-to-end workflow fixtures.

**Claude Cowork** ([#105](https://github.com/google/elephant-goldfish-model/issues/105)) and **ChatGPT Work** ([#106](https://github.com/google/elephant-goldfish-model/issues/106)) have working installation paths with open cloud trace verification gaps.

See the [harness test record](../TESTING.md#harness-test-record) for tested surfaces and limits.

We welcome contributors who want to help verify and expand harness support.

### Contributing Support for New Harnesses

A harness counts as supported after `/egm-brainstorm`, `/egm-draft`, and
`/egm-review` run end to end through its plugin install. When contributing
support for another harness:

1. Add the appropriate manifest or configuration file to the repository root
   (e.g., matching the harness's plugin/extension standard).
2. Document install steps, manifest mapping, and delegation mechanics in this guide
   (`docs/harnesses.md`).
3. Verify that `/egm-brainstorm`, `/egm-draft`, and `/egm-review` run end to end,
   and attach verification notes or execution transcripts in your Pull Request description
   (as outlined in the [Pull Request Template](../.github/PULL_REQUEST_TEMPLATE.md)).
