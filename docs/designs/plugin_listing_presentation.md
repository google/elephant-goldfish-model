# Plugin 0.1.1 listing and package presentation

- **Author:** @n3wth
- **Status:** Proposed. Maintainer scope approval is pending.
- **Date:** 2026-11-04
- **Scope issue:** #122. Original candidate: PR #302. Separate review units replace that PR.
- **Candidate commit:** `b903f35`, which adds neutral intake tests to `53077c3d64c42fc906f18373892a8e63a1ce9d6e` without package changes.

## Overview

Use concise, consistent text across plugin manifests and their generated copies.
Use the publisher's Google privacy destination in the plugin listing and retain the repository license for terms.
Keep the existing GitHub support destination and website URL.
Prepare version 0.1.1 with starter prompts, per-skill default prompts, PNG icons, and the portable manifest schema declaration.

This design covers listing presentation. It does not establish publisher policy approval or native application support.

## The Problem

The current plugin summaries use internal workflow terms and long descriptions.
The directory privacy link differs from the publisher privacy policy.
Readers need a clear description of the plugin's purpose before installation.

The original PR #302 exceeds the minor-patch limits.
It changes all seven canonical skill descriptions and their generated copies.
This proposal supplies a separate design review path. It does not claim a scope exception.

## Goals

- Describe idea development, document preparation, and independent review in plain language.
- Use one short description for each skill across canonical and generated files.
- Set the OpenAI listing category to Productivity.
- Keep `https://egm.dev` as the website destination.
- Keep the repository issues page as the support destination.
- Use `https://policies.google.com/privacy` for `privacyPolicyUrl` and retain `https://github.com/google/elephant-goldfish-model/blob/main/LICENSE` for `termsOfServiceUrl`.
- Keep manifest files schema-valid and generated Claude files equal to package output.
- Add three plugin starter prompts and a default prompt for each of the seven skills.
- Preserve EGM-prefixed skill names and stable skill identifiers.
- Bundle seven 256x256 PNG skill icons, reference them in OpenAI YAML metadata, and retain the SVG sources.
- Declare the Agent Plugins 1.0.0 schema in the portable manifest and align host versions at 0.1.1.
- Test incomplete prompts, an unrelated request, and a nonsoftware proposal with user-supplied review criteria.

## Non-Goals

- Change skill instructions, reviewer permissions, or execution logic.
- Add a host, executor, tool, or network service.
- Treat directory publication as proof of native workflow support.
- Change the website documentation system or hosting.
- Claim that Google officially supports the project.
- Replace the software license with a terms-of-service claim.

## Open Questions

- The publisher must check that the linked policy pages apply to the plugin.
- A maintainer must approve the contribution scope and stage labels.
- Reviewers must check that shorter descriptions remain useful for skill selection.

## Critical User Journeys

### Understand the listing

- **Given:** A reader opens the plugin listing.
- **When:** The reader reads its summary and skill list.
- **Then:** The reader can identify the plugin's main tasks without internal reviewer terminology.
- **Then:** The listing does not imply support beyond the existing executor and host limits.

### Inspect policy and support information

- **Given:** A reader checks the developer and policy fields.
- **When:** The reader opens a website, support, privacy, or terms link.
- **Then:** Each field opens its stated destination without a broken repository path.

## Technical Plan

Update the canonical root manifest first.
Use the metadata values at the pinned candidate commit above, not the mutable PR head.
That commit defines the listing fields, capabilities, and all seven replacement descriptions.
Update compatibility manifests only where the existing schema supports the field.
Keep platform-specific fields and the local executor requirement.
Do not add fields that the manifest schemas reject.

Shorten the frontmatter descriptions in the seven canonical skill files.
Keep each skill's name, workflow body, and relative reference paths unchanged.
Add default prompts and PNG icon paths in each skill's `agents/openai.yaml`.
The workflow bodies remain unchanged. The new metadata changes how users discover and invoke those workflows.
Keep EGM-prefixed skill names and the existing brand colors.
Add the seven PNG files to the package builder's resource inventory.
Retain the SVG sources for the existing artwork and palette checks.
Retain the schema declaration in `.plugin/plugin.json`. Omit `$schema` from root `plugin.json` for `omp` compatibility.
Align the root, Claude, Codex, Cursor, and portable host versions at 0.1.1.
Regenerate the Claude runtime with the existing package builder.
Do not edit generated copies independently.

The long listing description must not serve as the sole record of execution limits.
The installation documentation retains the isolated-reviewer requirement, partial cloud support, and host permission boundaries.
The project support disclaimer remains in the repository and website.
Publisher review must check the wording and policy destinations before merge.

## Alternatives Considered

### Change compatibility manifests only

This option changes the visible listing quickly but leaves canonical metadata inconsistent.
The existing consistency tests reject that state.

### Keep the current long skill descriptions

This option preserves detailed trigger language but keeps internal stage names in a user-facing catalog.
The selected candidate uses short descriptions while retaining the full workflow text in each skill.

### Separate each skill description into a minor PR

This option creates artificial scope boundaries and makes copy consistency harder to review.
Keep all seven descriptions in one listing and prompt PR.

### Ship listing text without prompts or PNG assets

This option reduces the package diff but leaves discovery and first invocation as separate review decisions.
The release uses separate review units for listing text and prompts, PNG assets, and publisher policy destinations.
Each unit includes its tests and generated files. The feature units retain the Stage 2 gates.
Default prompts expose existing workflows. They do not bypass missing-input checks or grant permission to edit documents.

### Retain only SVG icon references

This option avoids seven additional source assets. The candidate instead supplies fixed-size PNG assets for the host picker and retains the canonical SVG artwork.
The PNG files provide a separate host asset format, not evidence that the host fixes the generic-icon problem.
Keep native icon rendering as an explicit verification gap.

The portable schema declaration and aligned versions describe this same package candidate.
Check the schema and generated resource inventory together rather than introducing a separate package system.

## Non-Functional Requirements

- Preserve manifest schema validity and package contents outside the planned metadata updates and seven added PNG assets.
- Do not add runtime requests or dependencies.
- Retain public policy and support links that a reader can open without repository write access.
- Revert rejected metadata fields and regenerate the runtime if the publisher rejects them.

## Detailed Implementation

The pinned candidate changes 55 files: 31 source, host, and test files plus 24 generated Claude files.
Fourteen files are PNG assets: seven canonical files and seven generated copies.
The seven canonical skill bodies remain unchanged.

### Source, host, and test files (31)

- `.claude-plugin/marketplace.json`.
- `.claude-plugin/plugin.json`.
- `.codex-plugin/plugin.json`.
- `.cursor-plugin/plugin.json`.
- `.plugin/plugin.json`.
- `README.md`.
- `plugin.json`.
- `scripts/pack_plugin.py`.
- `skills/egm-bootstrap/SKILL.md`.
- `skills/egm-bootstrap/agents/openai.yaml`.
- `skills/egm-bootstrap/assets/icon.png`.
- `skills/egm-brainstorm/SKILL.md`.
- `skills/egm-brainstorm/agents/openai.yaml`.
- `skills/egm-brainstorm/assets/icon.png`.
- `skills/egm-draft/SKILL.md`.
- `skills/egm-draft/agents/openai.yaml`.
- `skills/egm-draft/assets/icon.png`.
- `skills/egm-drift-report/SKILL.md`.
- `skills/egm-drift-report/agents/openai.yaml`.
- `skills/egm-drift-report/assets/icon.png`.
- `skills/egm-resolve/SKILL.md`.
- `skills/egm-resolve/agents/openai.yaml`.
- `skills/egm-resolve/assets/icon.png`.
- `skills/egm-review-loop/SKILL.md`.
- `skills/egm-review-loop/agents/openai.yaml`.
- `skills/egm-review-loop/assets/icon.png`.
- `skills/egm-review/SKILL.md`.
- `skills/egm-review/agents/openai.yaml`.
- `skills/egm-review/assets/icon.png`.
- `tests/integration/test_codex.py`.
- `tests/unit/test_packaging.py`.

The manifests define listing text, policy links, supported prompts, the schema declaration, and version 0.1.1.
The README distinguishes software workflows from configurable reviews of other documents.
The seven `SKILL.md` changes update frontmatter descriptions only.
The seven YAML changes add default prompts and PNG paths while preserving skill names.
The package builder includes the new PNG files.
The unit tests check schema declarations, prompt identifiers, skill names, PNG dimensions, and resource equality.
The native tests cover incomplete starter prompts, an unrelated request, and a nonsoftware proposal.

### Generated Claude files (24)

Regenerate these files with the existing package builder. Do not edit them independently.

- `distributions/claude/.claude-plugin/plugin.json`.
- `distributions/claude/README.md`.
- `distributions/claude/plugin.json`.
- `distributions/claude/skills/egm-bootstrap/SKILL.md`.
- `distributions/claude/skills/egm-bootstrap/agents/openai.yaml`.
- `distributions/claude/skills/egm-bootstrap/assets/icon.png`.
- `distributions/claude/skills/egm-brainstorm/SKILL.md`.
- `distributions/claude/skills/egm-brainstorm/agents/openai.yaml`.
- `distributions/claude/skills/egm-brainstorm/assets/icon.png`.
- `distributions/claude/skills/egm-draft/SKILL.md`.
- `distributions/claude/skills/egm-draft/agents/openai.yaml`.
- `distributions/claude/skills/egm-draft/assets/icon.png`.
- `distributions/claude/skills/egm-drift-report/SKILL.md`.
- `distributions/claude/skills/egm-drift-report/agents/openai.yaml`.
- `distributions/claude/skills/egm-drift-report/assets/icon.png`.
- `distributions/claude/skills/egm-resolve/SKILL.md`.
- `distributions/claude/skills/egm-resolve/agents/openai.yaml`.
- `distributions/claude/skills/egm-resolve/assets/icon.png`.
- `distributions/claude/skills/egm-review-loop/SKILL.md`.
- `distributions/claude/skills/egm-review-loop/agents/openai.yaml`.
- `distributions/claude/skills/egm-review-loop/assets/icon.png`.
- `distributions/claude/skills/egm-review/SKILL.md`.
- `distributions/claude/skills/egm-review/agents/openai.yaml`.
- `distributions/claude/skills/egm-review/assets/icon.png`.

Add the 14 PNG assets listed above. Delete no source files. Change no dependencies.

### Review units and merge order

- PR #314 updates the publisher privacy destination across manifests while retaining the repository license for terms. It targets `main` and requires publisher approval.
- PR #316 contains listing text, skill descriptions, plugin starter prompts, schema metadata, versions, and Cursor manifest checks. It targets `main`.
- PR #317 contains per-skill OpenAI default prompts and their package and native prompt tests. It targets the #316 branch.

The policy PR is independent. Maintainers can reject it without blocking the other units.
The feature PRs remain gated until this design merges and issue #122 receives implementation approval.
Merge #316 to `main` before #317.
After #316 merges, rebase #317 onto `main`, retarget its PR, and repeat checks and review.
Do not merge #317 into the temporary parent branch.
The listing review restores the existing support disclaimer and partial-cloud limit in the listing text.
Empirical checks show that PNG skill icons do not change what the host picker shows, so the implementation retains the SVG skill icons.
This split follows the maintainer request for distinct purposes and smaller diffs. It does not create a minor-patch exception for the feature.

### Required approvals

1. Obtain maintainer scope approval and the `design-ready` issue label for Stage 1.
2. Merge this design and obtain the `pr-ready` issue label before the implementation merges.
3. Update canonical metadata and compare supported fields across manifests.
4. Regenerate the Claude runtime and inspect the exact diff.
5. Run unit tests, package both targets, and review the listing text.
6. Complete independent human review and publisher review of the policy destinations.

These label names follow the current repository PR template.
Review readiness does not establish scope approval or permission to merge the replacement feature PRs.
Issue #122 remains the publication scope reference. This design does not complete its publication requirements.

## Required Tests

- Run the complete repository unit suite.
- Build OpenAI and Claude packages with `scripts/pack_plugin.py`.
- Check manifest schema validity and shared metadata equality.
- Check generated Claude byte equality against canonical package output.
- Check all host versions against 0.1.1 and check the declared Agent Plugins 1.0.0 schema.
- Check all seven default prompts for the expected skill identifier.
- Check PNG signatures, 256x256 dimensions, icon paths, retained SVG sources, and package resource equality.
- Check that skill bodies and existing reference paths do not change.
- Run the opt-in native tests against the exact OpenAI ZIP and retain its checksum and installed-file comparison.
- Check that incomplete starter prompts do not invent documents or launch reviewers.
- Invoke the actual starter prompts without extra statements about missing input or approval. Require the response to ask for the missing input.
- Check that an unrelated arithmetic request does not launch a review.
- Check that two isolated reviewers read the nonsoftware proposal and criteria without changes to the proposal.
- Open the website, support, privacy, and terms destinations.
- Obtain publisher review of policy applicability and category selection.

Passing offline tests does not establish native installation or full cloud review support.
Custom icon rendering remains unverified. PNG resource checks do not prove that Codex shows those icons.
The implementation cannot merge until its scope, design, publisher, and human review requirements pass.

Use these commands from the repository root with the documented test environment:

```sh
python -m pytest tests/unit -q
python3 scripts/pack_plugin.py --target openai --output <temporary-directory>
python3 scripts/pack_plugin.py --target claude --output <temporary-directory>
git diff --check
git diff 0dfb5bf b903f35 -- skills/
```

Regenerate the Claude runtime with the Claude package command, then replace the checked-in runtime with the generated `egm-claude` directory.
`tests/unit/test_frontmatter.py` checks metadata structure.
`tests/unit/test_packaging.py` checks the generated runtime against canonical package output.
Review each `SKILL.md` diff to check that only the frontmatter description changes.
The YAML metadata and PNG additions are separate planned changes within the skill directories.

Run paid native tests only through explicit opt-in at the implementation candidate:

```sh
EGM_CODEX_RELEASE_ZIP=/absolute/path/to/egm-openai-0.1.1.zip \
  EGM_CODEX_LIVE=1 python -m pytest tests/integration/test_codex.py \
  -k 'starter_prompt or nonsoftware or unrelated_prompt' -v
```

### Reported candidate evidence

The revised starter tests invoke the listing prompts alone, without statements about missing input or permission.
At `b903f35`, three native starter cases pass in 50.28 seconds with Codex CLI 0.166.0.
The final answers request the missing input. No reviewer launches or Markdown documents appear.
The unit suite passes 336 tests and skips two optional native probes.
The tested ZIP's SHA256 is `47178bb1b08d3b3ef4b663991bbd4b6542a64f91edfcaa30b9a7c2552d1c2df2`.
A fresh package build matches this archive. The revision changes tests only, so package bytes remain unchanged.

The PR #302 description reports these results for `53077c3d64c42fc906f18373892a8e63a1ce9d6e`.
This design update records that report. It does not rerun the tests or inspect the native traces.

- Unit suite: 336 pass and two optional native host probes skip.
- Exact-ZIP native subset above: five pass in 103.67 seconds.
- Three incomplete-prompt cases do not launch reviewers or invent documents.
- The arithmetic request stays outside the review workflow.
- Two fresh-context reviewers read the supplied proposal and criteria, find absent owner and financial information, and leave the proposal unchanged.
- The report states that schema validation, archive integrity, checksums, interface parity, and reproducible artifact comparison pass.
- The report states that the final OpenAI ZIP matches the archive used for those five native tests.

The report also records two earlier software workflow and isolation tests, which pass in 457.62 seconds on an earlier candidate.
Those tests do not rerun after the schema and label changes. They do not establish seven exact-head native passes.
Custom icon rendering, publisher policy applicability, directory publication, and web-host support remain unverified by these tests.

## Design Review Record

A fresh-context reviewer applies the EGM Design Critic and Implementation Readiness rubrics to the earlier proposal.
This revision expands the scope to the pinned 0.1.1 candidate and inventories all 55 changed files.
The earlier review does not establish approval of the expanded scope.
Independent review of this revision, publisher policy review, and the full EGM protocol remain pending.
