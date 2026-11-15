# Native In-Place OpenSpec Integration for EGM

* **Author:** Elise Ewing ([@eewing314](https://github.com/eewing314))
* **Status:** Draft RFC
* **Date:** 2026-11-15

## Overview

Developers using `@fission-ai/openspec` store active feature specifications as multi-file change bundles under `openspec/changes/<slug>/` (`proposal.md`, `design.md`, `tasks.md`, and `specs/<capability>/spec.md` deltas) and merge completed requirement deltas into canonical domain specifications under `openspec/specs/<capability>/spec.md` via `openspec archive`. Today, the Elephant-Goldfish Model (`google/elephant-goldfish-model`) assumes a single Markdown file split by line numbers (`FeatureRange` vs. `DetailedRange`) and checked into `docs/designs/`.

This design integrates OpenSpec directly in place—without PR #382's import/export translation bridge, checkbox snapshot diffing, Export Fidelity Goldfish, duplicate Python validator, or copied OpenSpec standard files inside EGM—through four coordinated changes:
1. **CLI-backed `skills/egm-draft-openspec/`**: Requires the `openspec` CLI (`./node_modules/.bin/openspec` or `PATH`, prompting installation if absent), pulls templates and project rules live from `openspec new change`, `openspec status --change "<slug>" --json`, and `openspec instructions <artifact> --change "<slug>" --json`, always authors `design.md` alongside `proposal.md`, `specs/<capability>/spec.md`, and `tasks.md` to satisfy EGM's Alternatives, Risks, and Zero-Decision standards, and validates via the `openspec` CLI.
2. **Multi-file bundle support across Goldfish subagents & review skills**: Updates `agents/*.md`, `egm-review`, `egm-review-loop`, and `egm-resolve` to accept either a single EGM design file or a named multi-file bundle (`proposal.md`, `design.md`, `tasks.md`, and `0..N` `specs/<capability>/spec.md` files, plus read-only canonical `openspec/specs/<capability>/spec.md` base specs for patched capabilities), citing findings by `(RelativeFilePath, SectionOrHeading, LineRange)` and fencing `egm-resolve` writes strictly to `openspec/changes/<slug>/`.
3. **Zero copied OpenSpec standards via `egm-structural` skip, format-neutral `egm-style` guard, and main-flow CLI validation**: On OpenSpec bundles, `egm-review` skips `egm-structural` (delegating structural/schema validation to `openspec status`, `openspec instructions apply`, and `openspec validate` in the main Elephant flow after Stage 7 returns and after `egm-resolve` edits), while **keeping `egm-style`** via a 2-sentence format-neutral rule in `agents/style.md` that preserves RFC-2119 keywords (`SHALL`, `MUST`, `SHOULD`, `MAY`), requirement/scenario headers and Given/When/Then markers, and Markdown task checkboxes (`- [ ]`, `- [x]`) while still auditing prose and claim calibration.
4. **Dual-format `egm-drift-report`**: Audits both default EGM design/README directories (`docs/designs/*.md`, package `README.md` contracts) and canonical `openspec/specs/<capability>/spec.md` behavioral specifications (including hybrid repos containing both).

## Analysis

Evaluating this architecture against `google/elephant-goldfish-model` and `@fission-ai/openspec` v1.2.0 confirms that delegating OpenSpec template and structural authority to the live `openspec` CLI while keeping EGM subagents focused on architecture, comprehension, claim calibration, and implementation readiness eliminates both PR #382's translation complexity and the maintenance burden of mirroring OpenSpec's schema inside EGM.

### 1. Skipping `egm-structural`, Keeping Format-Neutral `egm-style`, and Running Main-Flow `openspec` CLI Checks

* **Why keeping `egm-style` with a format-neutral guard helps OpenSpec bundles**:
  * In `agents/style.md`, `egm-style` audits marketing hyperbole, buzzwords, filler words, and **Defensive Caveats & Uncalibrated Claims** (`DROP | CALIBRATE | RELOCATE | KEEP`). Both free-form OpenSpec prose (`proposal.md`, `design.md`, `tasks.md` details) and behavioral delta statements (`specs/<capability>/spec.md`, where agents frequently write unmeasurable requirements like *"The system SHALL handle large payloads quickly"*) benefit directly from claim calibration and fluff removal.
  * Adding a 2-sentence, format-neutral rule to `agents/style.md` (with zero OpenSpec-specific coupling)—instructing it never to flag or rewrite RFC-2119 normative keywords (`SHALL`, `MUST`, `SHOULD`, `MAY`), structured requirement or Given/When/Then headers/markers (`Requirement:`, `Scenario:`, `WHEN`, `THEN`, `AND`, `FROM:`, `TO:`), or Markdown checkboxes (`- [ ]`, `- [x]`)—lets `egm-style` tighten prose and flag vague claims across OpenSpec, Gherkin, RFCs, and default EGM docs alike.
  * **Residual risk & mitigation**: When `egm-resolve` edits a requirement line in `specs/<capability>/spec.md` to calibrate a vague claim, wrapping text onto two lines before `SHALL`/`MUST` or altering a `MODIFIED`/`REMOVED` header would break OpenSpec. Running `openspec validate` in the main flow at the end of `egm-resolve` (and querying `openspec instructions specs --change "<slug>" --json` live before `egm-resolve` touches `specs/`) catches any line-1 `SHALL`/`MUST` regression immediately before finishing resolution.
* **Skipping `egm-structural` in favor of main-flow `openspec` CLI checks**:
  * Goldfish subagents are read-only (`Read`, `Grep`, `Glob`) and cannot execute `openspec`. Skipping `egm-structural` on OpenSpec paths avoids maintaining a shadow `openspec-change-standard.md` inside EGM.
  * After Stage 7 subagents (`egm-design`, `egm-style`) return—and again in `egm-resolve` Step 5 after approved edits are written—the main Elephant thread runs sanitized `openspec` CLI checks (`OPENSPEC_TELEMETRY=0 NO_COLOR=1` from `<OPENSPEC_ROOT>`):
    1. `openspec status --change "<slug>" --json` (verifies change metadata and artifact completion).
    2. `openspec instructions apply --change "<slug>" --json` (verifies column-0 `- [ ]` / `- [x]` checkboxes in `tasks.md`).
    3. `openspec validate "<slug>" --type change --strict --no-interactive --json` whenever `specs/*/*.md` delta files exist (skipping `--type change` only on valid zero-delta refactors where `specs/` is absent).
  * *Accepted boundary*: Upstream `openspec validate` checks syntax inside `changes/<slug>/specs/` while `openspec archive` remains the authoritative check for exact `MODIFIED`/`REMOVED`/`RENAMED` header string matches against `openspec/specs/<capability>/spec.md` (though `egm-design` and `egm-codebase-details` also read both files in context).

### 2. Multi-File Bundle Abstraction Across Subagents and Skills

* **3 fixed files + `0..N` capability delta files + read-only base specs**:
  * An OpenSpec change bundle `openspec/changes/<slug>/` maps to three fixed filenames (`proposal.md`, `design.md`, `tasks.md`) plus `0..N` capability delta files (`specs/<capability>/spec.md`).
  * Whenever `changes/<slug>/specs/<capability>/spec.md` patches an existing capability (`MODIFIED`, `REMOVED`, `RENAMED`), the matching canonical `openspec/specs/<capability>/spec.md` file accompanies the bundle as a **read-only Base Spec** across Stages 5–9 (including Stage 6 `egm-comprehension`, which needs the base capability spec to read patch blocks cold while still excluding codebase source files).
* **Stage-by-stage bundle routing**:
  * **Stages 5 & 8 (`egm-zoom-out`, plus `egm-inventive-catalyst` in Stage 5)**: Audit `FeatureScope = [proposal.md, design.md, specs/*/spec.md]` (+ read-only touched `openspec/specs/<cap>/spec.md`), excluding `tasks.md` so implementation file lists do not trigger `zoom-out-standard.md` Anti-Weeds findings.
  * **Stage 6 (`egm-comprehension`)**: Audits `FeatureScope` + `DetailedScope` (`tasks.md`) alongside read-only touched `openspec/specs/<cap>/spec.md` base specs (with codebase `GoldfishContext` withheld).
  * **Stage 7 (`egm-design`, `egm-style` + main-flow `openspec` CLI validation)**: Audits `FeatureScope` (+ `GoldfishContext`), skipping `egm-structural`, then merges `openspec validate` / `openspec instructions apply` CLI diagnostics into `critic_report.md`.
  * **Stage 9 (`egm-implementation-readiness`, `egm-codebase-details`, `egm-style`)**: Audits `DetailedScope = [tasks.md]` while mounting `FeatureScope` (`proposal.md`, `design.md`, `specs/*/spec.md`) as mandatory read-only baseline context. In `tasks.md`, top-level tasks use column-0 `- [ ] X.Y <summary>` checkboxes with indented **non-checkbox** bullets (`  - Files: Create | Modify | Delete ...`, `  - Details: ...`, `  - Verify: ...`) so Stage 9's Zero-Decision Rule passes without corrupting OpenSpec's checkbox count.
* **Prompt & coordinate updates in `agents/*.md`, `egm-review-loop`, and `egm-resolve`**:
  * Update single-file phrasing across `agents/*.md` so subagents accept either a single file or a named multi-file bundle and emit `Affected Scope: <relative_file_path> (lines X-Y or section heading)`.
  * Enforce a hard write fence in `egm-resolve` restricting mutations to `openspec/changes/<slug>/**` (never editing `openspec/specs/**` or `openspec/changes/archive/**`), and write all EGM review scratch reports outside `openspec/changes/<slug>/`.

### 3. CLI Subprocess Hygiene & Harness Requirements

* **Uniform CLI requirement**: Both `egm-draft-openspec` and OpenSpec mode in `egm-review` / `egm-resolve` check `./node_modules/.bin/openspec` and then `PATH` for `openspec` (`>= 1.2.0`). If `openspec` is missing, EGM halts and instructs the user to install `@fission-ai/openspec` (`npm install -g @fission-ai/openspec@latest`). `docs/harnesses.md` and `docs/privacy.md` note that OpenSpec workflows require a shell-capable harness with `openspec` installed and always pass `OPENSPEC_TELEMETRY=0 NO_COLOR=1` from `<OPENSPEC_ROOT>` (stripping any leading non-JSON notice lines before parsing `--json`).
* **Drafting stages in `egm-draft-openspec`**: `egm-draft-openspec` queries `openspec status --change "<slug>" --json` and `openspec instructions <artifact> --change "<slug>" --json` to inherit `openspec/config.yaml` `context:` and `rules:`, requires `proposal`, `specs`, `design`, and `tasks` (gating once per artifact stage—4 approval gates total—rather than once per capability file), and fails fast if a custom `openspec/schemas/` topology omits or renames those four artifacts. `egm-brainstorm` stays format-agnostic, adding only a 1-line Step 4 handoff note mentioning `/egm-draft-openspec` when `openspec/` is present.

### 4. Dual-Format `egm-drift-report` Mechanics

* **Default EGM + OpenSpec + hybrid repository support**:
  * Explicit paths audit default EGM design/README directories (`docs/designs/`, `src/`), OpenSpec canonical specs (`openspec/` or `openspec/specs/`), or an explicitly named active change directory (`openspec/changes/<slug>/`).
  * Zero-argument invocations detect `docs/designs/` and `openspec/specs/`: using whichever exists, presenting a single-select gate (`Audit docs/designs/`, `Audit openspec/specs/`, `Audit both`) in hybrid repos where both exist, or prompting for a directory if neither exists.
* **Traversal, scoping, and report clarity**:
  * In `docs/designs/`, skip index files (`README.md`, `SITEMAP.md`) while keeping `README.md` contract checks active in source directories.
  * In `openspec/` or `openspec/specs/`, recursively walk `openspec/specs/<capability>/spec.md` while excluding `openspec/changes/**` (and flagging capabilities with `[x]` tasks in active unarchived `openspec/changes/*/` folders as in-flight rather than unexpected drift).
  * Use full relative paths in headings (`## openspec/specs/<capability>/spec.md`) to avoid `## spec.md` collisions, suppress symbol-level reverse-coverage and file-link prompts on behavioral `openspec/specs/`, and delegate per-capability codebase searches to read-only subagents when available.

## Goals vs. Non-Goals

* **In-Scope Goals:**
  * Draft, review, resolve, and drift-audit OpenSpec specifications directly in place under `openspec/changes/<slug>/` and `openspec/specs/<capability>/spec.md` with zero intermediate translation files, zero bundled Python validators, and zero copied OpenSpec standard files in EGM.
  * Ship `skills/egm-draft-openspec/` backed by the installed `openspec` CLI (`new change`, `status --json`, `instructions --json`, `validate`), requiring `design.md` (with `Rejected by author:` alternatives, risks, and no unresolved open questions) alongside `proposal.md`, `specs/<capability>/spec.md`, and Zero-Decision `tasks.md`.
  * Generalize `agents/*.md`, `egm-review`, `egm-review-loop`, and `egm-resolve` to support named multi-file bundles (`proposal.md`, `design.md`, `tasks.md`, `specs/*/spec.md`, plus read-only base `openspec/specs/<cap>/spec.md`), keeping `egm-style` via a format-neutral RFC-2119/Gherkin/checkbox guard, skipping `egm-structural` on OpenSpec bundles, and running `openspec` CLI validation in the main Elephant thread after Stage 7 returns and after `egm-resolve` edits.
  * Update `egm-drift-report` to work across default EGM design/README directories, OpenSpec `openspec/specs/<capability>/spec.md` trees, and hybrid repositories containing both.
* **Out-of-Scope Non-Goals:**
  * Copying OpenSpec schema/grammar standards into `resources/document_standards/` or shipping a fallback validation mode when `openspec` CLI is not installed.
  * Creating new reviewer subagent personas in `agents/`.
  * Supporting custom `openspec/schemas/` DAGs that omit or rename `proposal`, `specs`, `design`, or `tasks` in v1.
  * Adapting `egm-lite` (which omits `design.md`) for OpenSpec (deferred to a fast-follow PR).
  * Modifying `egm-bootstrap`.

## Alternatives Weighed

* **Bidirectional Import/Export Translation Bridge, Checkbox Snapshot Diffing, Export Fidelity Goldfish, and Bundled Python Validator (GitHub PR #382)**: Rejected by author: translating between single-file EGM docs and multi-file `openspec/changes/<slug>/` folders creates stateful synchronization fragility, Day-2 checkbox drift, extra subagent passes to audit translation fidelity, and a duplicate Python validator.
* **Copying OpenSpec Standards into `resources/document_standards/` or Adding a 9th `agents/openspec_structural.md` Subagent**: Rejected by author: copying OpenSpec's grammar into EGM risks drift against upstream `@fission-ai/openspec`, and read-only subagents cannot run `openspec validate`. Skipping `egm-structural` on OpenSpec bundles while running `openspec validate` + `openspec instructions` in the main Elephant flow delegates all OpenSpec format authority to the live CLI with zero new subagents.
* **Skipping `egm-style` Completely on OpenSpec Bundles**: Rejected by author during refinement: `proposal.md`, `design.md`, `tasks.md`, and `specs/` all benefit from `egm-style`'s fluff removal and claim calibration (`DROP | CALIBRATE | RELOCATE | KEEP`), and adding a 2-sentence format-neutral guard for RFC-2119 keywords, scenario headers/markers, and task checkboxes preserves OpenSpec syntax without embedding OpenSpec-specific rules in `agents/style.md`.
* **No-CLI Static Fallback Mode for OpenSpec Reviews**: Rejected by author: teams working in OpenSpec repositories already use the `openspec` CLI; requiring `openspec` (`./node_modules/.bin/openspec` or `PATH`) uniformly across `egm-draft-openspec` and OpenSpec reviews avoids maintaining duplicate static validation logic.
* **Cloning a Separate `egm-review-openspec` Skill**: Rejected by author: duplicating `egm-review`'s 5-stage orchestration creates workflow drift against core EGM review updates.
* **Updating `egm-bootstrap` or Bundling `egm-lite` OpenSpec Support in v1**: Rejected by author: `egm-bootstrap` (`README.md` package contracts) is orthogonal to behavioral `openspec/specs/`, and `egm-lite` OpenSpec adaptation (without `design.md`) is deferred to a fast-follow PR.

## Key Decisions & Staging for Next Steps

1. **Zero Copied OpenSpec Standards + Format-Neutral `egm-style` Guard**: EGM stores no OpenSpec template or grammar files; `egm-review` skips only `egm-structural` on OpenSpec bundles, keeps `egm-style` with a 2-sentence format-neutral guard in `agents/style.md` (protecting RFC-2119 keywords, `Requirement:`/`Scenario:`/`WHEN`/`THEN` markers, and `- [ ]` checkboxes), queries `openspec instructions <artifact> --change "<slug>" --json` live when creating/editing OpenSpec artifacts, and runs `openspec` CLI validation in the main flow after Stage 7 returns and after `egm-resolve` writes fixes.
2. **Uniform `openspec` CLI Requirement**: Both `egm-draft-openspec` and OpenSpec mode in `egm-review` / `egm-resolve` check `./node_modules/.bin/openspec` then `PATH`, halting with an install instruction if missing, and execute all CLI calls from `<OPENSPEC_ROOT>` with `OPENSPEC_TELEMETRY=0 NO_COLOR=1` and `--no-interactive --json`.
3. **Multi-File Bundle Support Across Subagents & Review Skills**: Update `agents/*.md`, `egm-review`, `egm-review-loop`, and `egm-resolve` to accept named multi-file bundles (`proposal.md`, `design.md`, `tasks.md`, `0..N` `specs/<cap>/spec.md` deltas + read-only base `openspec/specs/<cap>/spec.md`), routing `FeatureScope` (`proposal.md`, `design.md`, `specs/*`) to Stages 5/7/8, `FeatureScope + DetailedScope + Base Specs` to Stage 6, and `DetailedScope` (`tasks.md` with indented non-checkbox file/detail bullets) + read-only `FeatureScope` to Stage 9, with `egm-resolve` fenced to `openspec/changes/<slug>/**` and scratch reports stored outside `openspec/changes/<slug>/`.
4. **Dual-Format `egm-drift-report` & Minimal `egm-brainstorm` Handoff**: Update `egm-drift-report` to audit default EGM design/README directories, OpenSpec `openspec/specs/<cap>/spec.md` trees, and hybrid repos (skipping `openspec/changes/**` unless a single active change folder is explicitly passed), and add a 1-line pointer in `egm-brainstorm` Step 4 mentioning `/egm-draft-openspec` when `openspec/` exists.
