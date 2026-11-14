# OpenCode

## Overview
Experimental OpenCode V1 adapter that installs an EGM bundle into a fresh destination directory.

## Interface
- [adapters/opencode/install.py:ROOT] Resolves the repository root from the installer location.
- [adapters/opencode/install.py:HOST_VERSION] Pins the OpenCode host version recorded in `installation.json`.
- [adapters/opencode/install.py:REVIEWERS] Lists the seven Goldfish reviewer personas registered as subagents.
- [adapters/opencode/install.py:name] Reads the canonical `egm-<skill>` name from a persona or skill frontmatter header.
- [adapters/opencode/install.py:install] Creates a new installation bundle and refuses overwrites, returning the generated `opencode.json` path.

## Invariants
- [adapters/opencode/install.py:install] Refuses an existing path or symlink, paths inside the source tree, backslashes, template or glob characters, and paths matching the `.env` read rules.
- [adapters/opencode/install.py:install] Registers reviewer agents with read-only permissions, `grep` denied, and bundle-scoped external directory access.
- [adapters/opencode/install.py:install] Registers the `egm` orchestrator with `ask` defaults, skill and task allowlists, and bundle-scoped external directory access.
- [adapters/opencode/install.py:install] Refuses to continue when a reviewer persona or canonical skill name is missing.

## Side Effects
- [adapters/opencode/install.py:install] Copies `skills/`, `agents/`, `resources/`, `docs/`, `plugin.json`, `LICENSE`, `README.md`, and `TESTING.md` into a new `bundle/` directory.
- [adapters/opencode/install.py:install] Writes `opencode.json` with agent permissions, default agent, skill paths, and slash commands.
- [adapters/opencode/install.py:install] Creates one skill symlink per canonical `egm-*` skill under the installation root.
- [adapters/opencode/install.py:install] Writes `installation.json` with the plugin name, version, host version, status, and SHA-256 hashes for every bundle file.

## Verification
- Run: `python3 -m pytest tests/unit/test_opencode_adapter.py`
