# Multi-Harness Support: Hermes Agent, OpenClaw, and Delta

* **Author:** Sriram (@Seburan)
* **Date:** 2026-10-23
* **Status:** Draft / RFC
* **Refs:** [#116](https://github.com/google/elephant-goldfish-model/issues/116)

## 1. Overview

The Elephant-Goldfish Model (EGM) relies on dual memory boundaries: deep persistent context for authoring ("The Elephant") and isolated, zero-context reviewers ("The Goldfish"). For EGM to remain truly model- and harness-agnostic, users running modern autonomous developer environments—specifically **Hermes Agent** (Nous Research), **OpenClaw**, and **Delta**—must be able to install and run EGM workflows (`/egm-brainstorm`, `/egm-draft`, `/egm-review`, `/egm-resolve`) without maintaining fork drift or breaking file-access contracts.

Currently, EGM packages manifests for Antigravity (`plugin.json`), Claude Code (`.claude-plugin/`), and Codex (`.codex-plugin/`, `.agents/plugins/`). However:
1. **Hermes Agent** discovers tools and skills via `~/.hermes/plugins/` using a YAML manifest pointing to markdown skills and runtime tool declarations.
2. **OpenClaw** discovers skills from workspace configuration roots (`openclaw.json` or `.openclaw/openclaw.json`), separating low-level channel tools from markdown workflows.
3. **Delta** discovers agent skills via `.delta/plugin.json` or workspace `.agents/skills/<name>/SKILL.md` mappings.

This document specifies the manifest schemas, directory discovery mappings, subagent delegation mechanics, risk mitigations, and test verification required to officially support Hermes Agent, OpenClaw, and Delta in EGM.

---

## 2. Goals vs. Non-Goals

### 2.1 In-Scope Goals
* **Universal Manifest Compatibility**: Provide canonical manifest definitions so that Hermes Agent, OpenClaw, and Delta users can install the full EGM package using standard CLI commands (`hermes plugins install <repo>`, `openclaw plugin add <repo>`, `delta skills tap add <repo>`).
* **Preserve Single-Source Text**: Adhere strictly to EGM's core principle: *No harness gets a fork of the skill text*. All harnesses share the identical root `skills/`, `agents/`, and `resources/`.
* **Subagent Delegation Mappings**: Document explicit subagent invocation mapping (Hermes task dispatch, OpenClaw sub-sessions, Delta runner delegation) ensuring Goldfish zero-context isolation requirements.
* **Test Suite Verification**: Extend `tests/unit/test_harnesses.py` to validate manifest synchronization and prevent metadata drift across all harness targets.
* **Documentation & Harness Guide**: Update `docs/harnesses.md` with installation commands, configuration snippets, delegation mechanics, and update `TESTING.md` test records.

### 2.2 Out-of-Scope Non-Goals
* **No Runtime Rewrites**: We will NOT transpile or rewrite EGM markdown skills into proprietary Python or JavaScript runtimes. Harnesses must execute native `SKILL.md` files.
* **No Cloud-Hosted Registries**: We will NOT stand up or manage proprietary cloud package registry backends. Installation uses Git repo URLs or local path taps.
* **No Custom Channel Gateway Development**: OpenClaw gateway extensions (e.g., Slack/Discord bot bridges) are out of scope. EGM focuses exclusively on the coding agent workflow layer.
* **No Multi-Device Profile Synchronization**: Syncing agent states across multiple physical devices or remote instances is deferred to the underlying harness runtime.

---

## 3. Harness Specification Matrix

| Feature / Dimension | Hermes Agent | OpenClaw | Delta |
| :--- | :--- | :--- | :--- |
| **Plugin / Skill Manifest** | `.hermes/plugin.yaml` | `.openclaw/openclaw.json` | `.delta/plugin.json` |
| **Skill Discovery Path** | `skills` (`skills/`) | `skills` (`skills/`) | `skills` (`skills/`) |
| **Subagent Tool Mapping** | Hermes task/spawn tool (`hermes.spawn`) | OpenClaw sub-session (`session.fork`) | Delta runner delegation |
| **Fresh Context Guarantee** | Isolated process / thread per subagent | Ephemeral subsession with `fork_context: false` | Fresh runner subprocess |
| **Read-Only Tool Policy** | Restrict tools to `Read`, `Grep`, `Glob` | Restrict tools to `Read`, `Grep`, `Glob` | Restrict tools to `Read`, `Grep`, `Glob` |
| **Install Command** | `hermes plugins install <repo>` | `openclaw plugin add <repo>` | `delta skills tap add <repo>` |

---

## 4. Architectural Design & Directory Structure

To maintain zero code duplication, the repository layout introduces lightweight harness compatibility adapter manifests:

```text
elephant-goldfish-model/
├── plugin.json                 # Canonical Agent Plugins 1.0.0
├── .claude-plugin/             # Claude Code & Cowork adapter
├── .codex-plugin/              # OpenAI Codex adapter
├── .hermes/                    # Hermes Agent adapter
│   └── plugin.yaml
├── .openclaw/                  # OpenClaw adapter
│   └── openclaw.json
├── .delta/                     # Delta adapter
│   └── plugin.json
├── agents/                     # Persona definitions (egm-zoom-out, egm-design, etc.)
├── skills/                     # Canonical EGM skills (egm_brainstorm, egm_draft, etc.)
├── resources/                  # Document standards & finding contracts
└── docs/
    └── harnesses.md            # Harness installation & delegation matrix
```

### 4.1 Hermes Agent Manifest (`.hermes/plugin.yaml`)
```yaml
name: egm
version: 0.1.0
description: "Elephant-Goldfish Model: spec-driven development with deep-context drafting and zero-context Goldfish reviews."
author:
  name: Google LLC
homepage: https://egm.dev
repository: https://github.com/google/elephant-goldfish-model
license: Apache-2.0
skills: skills
agents: agents
```

### 4.2 OpenClaw Manifest (`.openclaw/openclaw.json`)
```json
{
  "name": "egm",
  "version": "0.1.0",
  "description": "Elephant-Goldfish Model: spec-driven development with deep-context drafting and zero-context Goldfish reviews.",
  "author": {
    "name": "Google LLC"
  },
  "homepage": "https://egm.dev",
  "repository": "https://github.com/google/elephant-goldfish-model",
  "license": "Apache-2.0",
  "skills": "skills",
  "agents": "agents",
  "isolation": {
    "mode": "ephemeral_subsession",
    "fork_context": false
  }
}
```

### 4.3 Delta Manifest (`.delta/plugin.json`)
```json
{
  "name": "egm",
  "version": "0.1.0",
  "description": "Elephant-Goldfish Model: spec-driven development with deep-context drafting and zero-context Goldfish reviews.",
  "author": {
    "name": "Google LLC"
  },
  "homepage": "https://egm.dev",
  "repository": "https://github.com/google/elephant-goldfish-model",
  "license": "Apache-2.0",
  "skills": "skills",
  "agents": "agents"
}
```

---

## 5. Alternatives Considered

1. **Dynamic Runtime Transpiler / CLI Wrapper**:
   * *Concept*: Build a CLI utility (`egm-cli`) that translates EGM skills dynamically into proprietary plugin types or Python packages at install time.
   * *Rejection Rationale*: Violates EGM's minimalism and zero-runtime principles. Markdown-based `SKILL.md` is already an industry standard natively consumable by modern agents. Introducing runtime build steps introduces unnecessary failure modes and dependencies.
2. **Filesystem Symlinking into `.agents/skills/`**:
   * *Concept*: Symlink root `skills/` to `.agents/skills/` to satisfy harnesses expecting `.agents/`.
   * *Rejection Rationale*: Symlinks fail on Windows filesystems without administrative privileges or developer mode enabled, resulting in plain-text target pointer files. Furthermore, `.agents/` is reserved for Codex plugin catalog discovery (`.agents/plugins/marketplace.json`).
3. **Discrete Static Compatibility Manifests (Selected)**:
   * *Concept*: Maintain thin static metadata adapters (`.hermes/plugin.yaml`, `.openclaw/openclaw.json`, `.delta/plugin.json`) pointing to shared `skills/` and `agents/`.
   * *Adoption Rationale*: Retains single-source textual integrity, requires no runtime build steps, and integrates cleanly with unit test assertions against metadata drift.

---

## 6. Risks & Mitigations

* **Risk 1: Subagent Context Leaks**:
  * *Failure Mode*: A third-party harness session fork inherits the parent chat conversation, violating the zero-context Goldfish requirement.
  * *Mitigation*: Manifests and documentation mandate setting `fork_context: false` or spawning an isolated runner process. Review skills verify prompt boundaries and halt if parent context is detected.
* **Risk 2: Reviewer Tool Mutability**:
  * *Failure Mode*: A Goldfish reviewer executes code editing or bash execution tools during an audit.
  * *Mitigation*: Subagent dispatch policy explicitly restricts reviewer tools to read-only capabilities (`Read`, `Grep`, `Glob`).
* **Risk 3: Upstream Manifest Schema Drift**:
  * *Failure Mode*: External harnesses evolve their plugin schemas, causing install failures.
  * *Mitigation*: `tests/unit/test_harnesses.py` includes polymorphic schema tests ensuring canonical fields (`name`, `version`, `author`, `repository`, `license`) match `plugin.json` across all adapters.

---

## 7. Detailed Implementation Plan

### 7.1 Target Files to Create / Modify
* **Create Adapter Manifests**:
  * `.hermes/plugin.yaml`
  * `.openclaw/openclaw.json`
  * `.delta/plugin.json`
* **Modify Tests**:
  * `tests/unit/test_harnesses.py`: Refactor `read_json` to `read_manifest` using `yaml.safe_load` to support both JSON and YAML. Add new manifest paths to `COMPATIBILITY_MANIFESTS`.
* **Modify Documentation**:
  * `docs/harnesses.md`: Add Hermes Agent, OpenClaw, and Delta to the install matrix, manifest mapping, and subagent delegation table.
  * `TESTING.md`: Add test coverage rows under the Harness Test Record.

### 7.2 Verification Plan
1. **Manifest Parity & Schema Tests**:
   - Run `pytest tests/unit/test_harnesses.py` to verify that all manifests parse cleanly and match canonical metadata.
2. **Link Integrity & Frontmatter Checks**:
   - Run `pytest tests/unit/test_frontmatter.py tests/unit/test_link_integrity.py` to confirm zero broken links or invalid frontmatter.
3. **Workflow Fixture Execution**:
   - Verify `/egm-brainstorm`, `/egm-draft`, and `/egm-review` across simulated harness invocation contexts.
