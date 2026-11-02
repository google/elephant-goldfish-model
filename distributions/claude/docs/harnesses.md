# Harnesses

EGM is one set of skills and personas. This repository serves as the
plugin source for each supported harness. No harness gets a fork of the skill
text.

## Install

| Harness | Install |
| --- | --- |
| Antigravity CLI | `agy plugin install https://github.com/google/elephant-goldfish-model` |
| Antigravity App | Run `/plugin` or see [installation instructions](#antigravity-app-and-antigravity-for-ides) |
| Antigravity for IDEs | Run `/plugin` or see [installation instructions](#antigravity-app-and-antigravity-for-ides) |
| Antigravity IDE (standalone) | Not supported; see [installation instructions](#antigravity-app-and-antigravity-for-ides) |
| Claude Code | `claude plugin marketplace add google/elephant-goldfish-model && claude plugin install egm@egm` |
| Claude Cowork | Install from claude.ai/plugins or the Cowork plugin panel via marketplace `google/elephant-goldfish-model` |
| Codex | `codex plugin marketplace add google/elephant-goldfish-model && codex plugin add egm@egm` |
| ChatGPT | Personal testing: Plugins > Add > Upload plugin archive; see [packaging](codex.md#chatgpt). Workspace import: Admin > Plugins > Add > Import marketplace, repo URL `https://github.com/google/elephant-goldfish-model`, path `.agents/plugins` |
| Pi | `pi install <checkout>/distributions/pi`, then two setup steps; see [installation instructions](#pi) |
| omp | `omp plugin marketplace add google/elephant-goldfish-model && omp plugin install egm@egm` |

Install the whole plugin. Skill-only installers that copy `skills/` alone
break EGM, because the skills read `agents/` and
`resources/document_standards/` at run time.

### Antigravity App and Antigravity for IDEs

- **Antigravity App**: Run `/plugin`, ask the agent `Install https://github.com/google/elephant-goldfish-model`, or manually install into `~/.gemini/config/plugins/egm/` using the commands below.
- **Antigravity for IDEs (Extension for Visual Studio Code)**: Run `/plugin`, ask the agent `Install https://github.com/google/elephant-goldfish-model`, or manually install into `~/.gemini/config/plugins/egm/` using the commands below.
- **Antigravity IDE (Standalone)**: Not supported at this time. Although the plugin and skills load from `~/.gemini/config/plugins/egm/`, standalone Antigravity IDE (tested on macOS and Linux) does not expose the fresh-context subagent tool (`invoke_subagent`) required for Goldfish reviews (`/egm-brainstorm` and `/egm-review`).

The Antigravity App and Antigravity for IDEs share the global plugin directory
`~/.gemini/config/plugins/<name>/`. For a fresh manual installation without the
`agy` CLI, copy the full runtime bundle into `~/.gemini/config/plugins/egm/`
(copying into an existing plugin directory can leave obsolete files behind, so
remove `~/.gemini/config/plugins/egm` first when updating):

```sh
git clone https://github.com/google/elephant-goldfish-model.git
cd elephant-goldfish-model
mkdir -p ~/.gemini/config/plugins/egm
cp -R plugin.json README.md LICENSE skills agents resources docs assets ~/.gemini/config/plugins/egm/
```

Reload the window (or restart the Antigravity App), then confirm that `egm`
appears in the plugin list and that its skills (`/egm-brainstorm`, `/egm-draft`,
`/egm-review`) are available.

### Pi

[Pi](https://pi.dev) is a terminal coding agent that loads skills, prompt
templates, extensions, and themes from a package. EGM ships a Pi package at
`distributions/pi/`. Pi substitutes no plugin-root variable, so that package
carries its own copies of the shared bundle and is installed from the checkout:

```sh
git clone https://github.com/google/elephant-goldfish-model.git
cd elephant-goldfish-model
pi install "$PWD/distributions/pi"
```

`pi list` shows the package, and `/skill:egm-brainstorm` runs a skill once the
session is trusted. The skills keep `disable-model-invocation: true`, so Pi does
not offer them for automatic selection.

Goldfish reviews need a fresh-context subagent tool. Pi core ships no subagent
tool, so Goldfish reviews require a third-party Pi subagent extension — EGM has
checked only Gentle Agents in `gentle-pi` 4.5.1, tests no other, and the review
skills stop when no such tool is present. That extension, not Pi, decides where
agent definitions live and how a child session is spawned, so inspect the tool
schema your session exposes instead of assuming names. Where the extension
registers agents from a directory, install the nine reviewer definitions from
this package there:

```sh
# Example: the agent directory Gentle Agents reads. Confirm the path in the
# extension's own documentation before relying on it.
mkdir -p ~/.pi/agent/agents
ln -s "$PWD/distributions/pi/subagents/"*.md ~/.pi/agent/agents/
```

Copying the files instead of linking them also works; a copied reviewer then
depends on the absolute paths its task receives rather than on its own location.

Pi has no plugin-root substitution. Pi reports each skill's own absolute path,
so the bundle root is three directories above `skills/<skill>/SKILL.md`. To name
the root up front instead, add one line to `~/.pi/agent/APPEND_SYSTEM.md` or a
project `AGENTS.md`:

```text
EGM Pi bundle root: /absolute/path/to/elephant-goldfish-model/distributions/pi
```

Resolve `agents/`, `resources/`, and `docs/` against that root, and
`references/` against the invoked skill's directory. When a reviewer is
launched, pass absolute persona, standard, and target paths in its task.

What differs from the other hosts:

- The shared skill preambles name Claude and Codex only. In a Pi session, read
  the Pi rows in the tables below before the first EGM skill.
- Claude's `Read`, `Grep`, and `Glob` are `read`, `grep`, and `find` in Pi. Pi
  also has `ls` and `bash`, and Windows hosts expose `powershell` instead of
  `bash`.
- A reviewer definition's `tools` list is read by the extension, which passes
  the child process a tool selection. Where the extension does that, read-only
  reviewers have no editing, shell, or MCP tools; confirm it from the schema you
  inspect. Pi runs tools with the permissions of the Pi process, so this is not
  a filesystem sandbox.

## Manifests

Root `plugin.json` is the canonical source for plugin identity, version,
description, and publisher metadata. It follows the portable Agent Plugins
1.0.0 format; the `$schema` key is omitted because omp routes manifests that
declare it to a strict validator that rejects `disable-model-invocation`.
Update shared values there first, then update the compatibility
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
| Pi | `distributions/pi/package.json` | `skills` path | Definitions in `distributions/pi/subagents/`, installed into the subagent extension's agent directory |
| omp | `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` (Claude-compatible fallback) | `skills/` (default) | Personas from `agents/`/`.claude-plugin/agents/` register as native `task` agents |

Persona prompts live in `agents/`, the directory Antigravity
scans for subagents. Each persona has `name` and `description` frontmatter, so
harnesses that load `agents/*.md` register them as named subagents
(`egm-design`, `egm-zoom-out`, and so on).

When you add a reviewer persona, add a Claude adapter under
`.claude-plugin/agents/` and list it in `.claude-plugin/plugin.json`, and add a
Pi definition under `distributions/pi/subagents/`.
The adapter reads the shared persona and sets Claude's read-only tools and
context isolation. This avoids imposing Claude tool names on other hosts.
The Pi package holds copies of the canonical `skills/`, `agents/`,
`resources/`, and `docs/` files, because Pi resolves package resources inside the
package root. Refresh them with
`python3 scripts/check_pi_distribution.py --write`; `--check` reports drift and
metadata divergence from `plugin.json` without writing.
In Claude Code, `/plugin` > Errors will report that the default `agents/` folder is ignored because the manifest sets `"agents"`; this warning is expected and harmless (see [Claude integration](claude.md#claude-code-warning-default-agents-folder-is-ignored)).

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
| Pi | No native tool; a third-party subagent extension supplies one (checked: `subagent_run` in Gentle Agents) | Yes, where the extension registers agent definitions | No; the main context dispatches reviewers |
| omp | `task` tool | Yes | Yes |

Where a harness has no named persona, the skill spawns a general-purpose
subagent and tells it to read `agents/<file>.md` first. If a harness cannot
nest subagents, use direct dispatch instead of the synthesizer.

A Goldfish review needs a fresh context. If a harness has no subagent tool,
the review skills stop instead of running in the same context. Check actual
tool availability rather than inferring it from the product name. This applies
to standalone Antigravity IDE, to ChatGPT modes that do not expose native
fresh-context delegation, and to Pi without a subagent extension.

## Artifact Directory

Skills write briefs, drafts, and reports to the working directory, or to the
harness's artifact directory if it has one. In Claude Code, Claude Cowork,
Codex, ChatGPT, and Pi, you can name another folder. Add this line to your prompt,
or to an agent instructions file that your harness loads (`CLAUDE.md` or
`AGENTS.md`, in the project or at user level):

```text
EGM artifact directory: .dev/docs
```

A relative path is relative to the working directory. Design docs and other
project files do not move. Claude Code reads a project `AGENTS.md` only when
the project has no `CLAUDE.md`. To keep the files out of git, add the folder to
`.gitignore`.

## Support Status & Contributing Other Harnesses

**Antigravity**, **Claude Code**, and **Codex** pass automated installation, reviewer isolation, and end-to-end workflow fixtures.

**Claude Cowork** ([#105](https://github.com/google/elephant-goldfish-model/issues/105)) and **ChatGPT Work** ([#106](https://github.com/google/elephant-goldfish-model/issues/106)) have working installation paths with open cloud trace verification gaps.

**omp** ([#186](https://github.com/google/elephant-goldfish-model/issues/186)) has a working installation path. Skills are invoked as `/skill:egm-<command>` (omp registers one command per skill; it has no `/egm-*` namespace). Community-verified on omp v18.12.6: all seven skills discover and resolve, and all nine reviewer personas register as subagents. End-to-end workflow fixtures are not yet automated for omp.

**Pi** has a documented installation path and no end-to-end proof, and Pi
support is conditional on a package Google does not test, pin, or license-review.
Pi core ships no subagent tool, so Goldfish reviews require a third-party Pi
subagent extension — EGM has checked only Gentle Agents in `gentle-pi` 4.5.1,
tests no other, and the review skills stop when no such tool is present.

Verified on 2026-11-02: the package installs from an isolated Pi config
directory, and all seven `egm-*` skills load and answer as `/skill:egm-*`. One
`egm-comprehension` reviewer spawned in REVIEW mode against a real 396-line
design document and returned 18 findings.

Not verified: no full `/egm-*` workflow ran end to end, and no parent-only
canary shows that parent conversation was excluded. The isolation above is
directory-based rather than enforced by Pi: that child still loaded the
machine's `~/.agents/skills` catalogue, and Pi has no per-agent equivalent of
Claude's `omitClaudeMd`, so a reviewer child starts a fresh conversation but
still loads the working directory's `AGENTS.md` and `CLAUDE.md`. The extension,
not Pi, decides where agent definitions live and how a child session is spawned,
so one working example does not establish another extension. Pi therefore stays
out of the supported list.

See the [harness test record](https://github.com/google/elephant-goldfish-model/blob/main/TESTING.md#harness-test-record) for tested surfaces and limits.

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
   (as outlined in the [Pull Request Template](https://github.com/google/elephant-goldfish-model/blob/main/.github/PULL_REQUEST_TEMPLATE.md)).
