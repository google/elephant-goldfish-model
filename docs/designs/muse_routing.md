# Muse session routing in skill preambles

Status: Proposed. Scope alignment for #252.
Author: @AshokTechie. Date: 2026-11-22.

## Problem Statement & Motivation

Every EGM skill preamble routes Codex and ChatGPT Work sessions to `docs/codex.md` and Claude Code/Cowork sessions to `docs/claude.md`. While EGM supports Muse and bundles `docs/muse.md` (merged in #250), skills currently lack an equivalent preamble routing instruction for Muse.

As a result:
1. Muse sessions do not automatically discover or read `docs/muse.md` unless the user explicitly prompts the model with the path.
2. Crucial operational guardrails defined in `docs/muse.md`—including single-question turns, artifact path resolution, fallback subagent delegation, and reviewer isolation—are missed by the runtime.
3. The `EGM artifact directory:` override mechanism relies on harness guides and cannot be respected in Muse without routing to `docs/muse.md`.

## Proposed Scope (Goals vs. Non-Goals)

### Goals
- Add standard preamble routing to all canonical EGM skills (`skills/*/SKILL.md`) immediately following the Claude Code directive:
  ```markdown
  In Muse, read [Muse integration](../../docs/muse.md) first.
  ```
- Ensure `docs/muse.md` is packaged in runtime bundles and allowlists.
- Maintain automated link resolution and prompt dependency checks in `tests/unit/test_harnesses.py`.
- Preserve the 24,000-byte skill body limit across all skills under Antigravity test suites.

### Non-Goals
- Altering Muse's underlying runtime architecture or subagent delegation mechanisms.
- Changing tool projection behavior for Muse reviewers.
- Modifying skill execution workflows or introducing new personas.

## Design Details

### Preamble Placement & Relative Path Resolution
Skills reside at `skills/<name>/SKILL.md`. In each skill preamble, immediately below the Claude Code directive, a relative Markdown link directs Muse agents to the integration guide:
```markdown
When running in Codex or ChatGPT Work, first read [Codex integration](../../docs/codex.md).
In Claude Code or Cowork, read `${CLAUDE_PLUGIN_ROOT}/docs/claude.md` first.
In Muse, read [Muse integration](../../docs/muse.md) first.
```
Muse resolves relative paths against the plugin root. Unit tests verify that every skill link resolves to an existing file on disk.

### Packaging & Runtime Boundaries
`docs/muse.md` is registered in `scripts/pack_plugin.py` under the packaging file list so standalone and packaged archives distribute the guide alongside the skills.

## Verification & Acceptance Criteria

1. **Static Analysis & Link Integrity**:
   - `test_bundled_prompt_dependencies_and_harness_guides` asserts that every `skills/*/SKILL.md` contains exactly one relative link to `docs/muse.md` and that the file exists.
   - `test_skill_body_fits_antigravity` asserts that adding the preamble line does not push any skill body beyond the 24,000-byte threshold.
2. **Offline Unit Suite**:
   - All unit tests in `tests/unit/` pass cleanly without external network or API keys.
3. **Live Harness Verification (Stage 2)**:
   - On a pinned Muse runtime, verify that a skill invocation loads `docs/muse.md` without requiring explicit user prompting and respects the configured `EGM artifact directory:`.
