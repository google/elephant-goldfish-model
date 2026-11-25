# Feature-Scoped EGM Artifact Folders

* **Author:** [@Aaravkhanal](https://github.com/Aaravkhanal) (draft for review)
* **Status:** Draft — Stage 1 proposal; maintainer scope approval pending
* **Date:** 2026-11-23
* **Issue:** [#448](https://github.com/google/elephant-goldfish-model/issues/448)

--------------------------------------------------------------------------------

## Overview

EGM's brainstorm, draft, and review workflows currently use fixed artifact
filenames. Starting a second feature in the same project can overwrite the first
feature's brief or draft. This design gives each feature a stable folder under
`egm/` (or under the configured artifact-directory root), so a user can return
to a feature by naming its folder and related workflow reports stay together.

Tracking issue: [#448](https://github.com/google/elephant-goldfish-model/issues/448).
The feature folder is an organization layer for workflow artifacts. It does not
change the content of the artifacts, create branches, or move approved designs
out of `docs/designs/`.

## The Problem

The current workflows write names such as `concepts_brief.md`,
`design_draft.md`, and `goldfish_review_report.md` into the working directory
or the configured artifact directory. Those names identify the workflow stage,
not the feature. A second `/egm-brainstorm` can overwrite a first brief, and a
later `/egm-draft` cannot tell which brief to continue without the user
renaming or moving files.

The repository already supports an `EGM artifact directory: <path>` override
([#118](https://github.com/google/elephant-goldfish-model/pull/118)). That
chooses a root for artifacts; it does not separate multiple features under
that root. Review-loop run folders are a separate concern: #278 and its active
design PR #462 preserve individual runs. When the feature-folder design is
implemented, a review-loop run folder should live inside the selected feature
folder, so both levels remain useful.

## Goals

* Give each feature a stable folder named `NNN-short-name`, with a minimum
three-digit number and a two-to-four-word lowercase kebab-case name.
* Have `/egm-brainstorm` propose a name and let the user change it before the
folder is created.
* Keep brainstorm, draft, review, review-loop, and resolve artifacts for one
feature together, and make the selected folder explicit in chat.
* Let a user resume an older feature by naming its folder or an artifact inside
it. When no folder is named, use and announce the highest-numbered feature
folder as described in #448.
* Use `egm/` as the default feature-folder root for these workflows. Treat an
`EGM artifact directory: <path>` setting as the parent of the numbered feature
folders, preserving the configured path and outside-workspace confirmation
rules.
* Continue to discover legacy root-level `concepts_brief.md` and
`design_draft.md` files when no numbered feature folder exists.
* Never overwrite an existing feature folder or user artifact during number
allocation, path selection, or collision handling.
* Keep approved designs at `docs/designs/<name>.md` and leave the Git working
tree, branches, and `.gitignore` under user control.

## Non-Goals

* Changing artifact formats, workflow stages, review criteria, approval gates,
or the behavior of `egm-bootstrap` and `egm-drift-report`.
* Replacing the `EGM artifact directory` setting or deciding a project-wide
artifact default for every EGM skill. Issue #110 remains the place to decide
cross-host defaults; this proposal defines the numbered-folder root only for
the five feature workflows in #448.
* Moving, renaming, or deleting legacy artifacts automatically.
* Creating Git branches, commits, worktrees, or modifying `.gitignore`.
* Replacing host artifact panes or adding a runtime, script, manifest, or
locking service.
* Resuming a workflow from a different conversation without the user selecting
its folder. Cross-session state restoration remains outside this design.

## User Journeys

### CUJ 1: Start a second feature without overwriting the first

* **Given**: `egm/001-feature-colors/` contains a brief and draft.
* **When**: The user starts `/egm-brainstorm` for a different feature.
* **Then**: The skill proposes `egm/002-pattern-categories/`, lets the user
  edit the short name, and writes the new brief there after the existing
  workflow's approval gate. The first feature's files remain unchanged.

### CUJ 2: Continue the latest feature

* **Given**: `egm/001-feature-colors/` and
  `egm/002-pattern-categories/` exist.
* **When**: The user invokes `/egm-draft` without naming a brief or folder.
* **Then**: The skill selects and states the full path to
  `egm/002-pattern-categories/`, reads that feature's brief, and writes its
  draft into the same folder.

### CUJ 3: Return to an older feature

* **Given**: Two numbered feature folders exist and the user wants to return
  to `egm/001-feature-colors/`.
* **When**: The user names that folder or a file inside it.
* **Then**: The named folder takes precedence over the highest-numbered-folder
  default, and subsequent artifacts for that workflow remain in the named
  folder.

### CUJ 4: Continue a legacy workflow

* **Given**: The project has a root-level `concepts_brief.md` and no numbered
  feature folders.
* **When**: The user starts `/egm-draft` without specifying another path.
* **Then**: The skill finds the legacy brief and continues using the existing
  location. It does not move or duplicate the file without the user's choice.

### CUJ 5: Keep review-loop history within its feature

* **Given**: The user reviews a design in a selected feature folder.
* **When**: `/egm-review-loop` starts a run.
* **Then**: The run-specific folder described by #278 is created under that
  feature folder. Per-round reports do not overwrite other runs or features.

## Technical Plan

### Folder layout

The default layout for a new feature is:

```text
egm/
├── 001-feature-colors/
│   ├── concepts_brief.md
│   ├── design_draft.md
│   ├── zoom_out_report.md
│   └── goldfish_review_report.md
└── 002-pattern-categories/
    ├── concepts_brief.md
    └── review-loop-feature-design-20261123-140500/
        ├── round-01-review.md
        ├── round-01-resolved.md
        └── ledger.md
```

If the user sets `EGM artifact directory: .dev/docs`, feature folders are
created under `.dev/docs/`, for example
`.dev/docs/001-feature-colors/`. The setting remains relative to the working
directory and keeps the existing confirmation requirement for a path outside
the workspace after symbolic-link resolution. It is the parent for the
numbered folders, not the feature folder itself. The skill must state this
interpretation when it selects a path.

### Path selection and lifecycle

The shared path-resolution contract distinguishes a new feature from a
continuation. A new brainstorm must not silently reuse the latest existing
feature folder.

1. **Explicit feature folder or artifact file.** Use the named folder. If the
   user names an EGM artifact file inside a numbered feature folder, use that
   file's parent as the feature folder. An explicitly named legacy artifact
   outside a numbered folder remains at its named path. A review target such
   as `docs/designs/foo.md` is input, not an artifact destination; do not put
   generated reports beside it solely because it was named.
2. **Feature selected earlier in the same conversation.** Reuse the path
   already stated for that feature; do not re-scan and silently switch to a
   newer folder.
3. **New feature.** `/egm-brainstorm` always allocates the next unused folder.
   A direct `/egm-draft` invocation also allocates a folder when the user
   supplies a new feature brief or describes new work without selecting an
   existing folder. The skill proposes the path and asks the user to accept or
   edit the name before creating it.
4. **Continuation without an explicit selection.** Select the highest-numbered
   valid folder under the resolved root and tell the user its full path before
   reading or writing its artifacts. This rule applies when the user is
   continuing work and has not named another feature.
5. **No numbered folder.** For an existing legacy brief or draft, keep using
   the legacy location. For a review target with no matching feature folder,
   derive a proposed short name from the target and ask the user to accept or
   edit it before creating the folder. `egm-resolve` requires a report or
   feature path; if neither is available, it asks for one rather than creating
   an empty feature folder.

The root is `./egm/` unless the user supplied an artifact-directory setting.
An explicit user path takes precedence over the numbered-folder default.
Relative configured paths resolve against the working directory. Existing
outside-workspace confirmation behavior from #265 remains in force.

The folder number is one greater than the largest valid numbered folder at the
resolved root, padded to at least three digits. The number is not truncated
after `999`. The short name is two to four words, lowercase kebab-case, with
characters outside the supported slug set removed or normalized before the
user sees the proposed path. The user can edit the slug before folder
creation.

Before creating a folder, the skill re-checks that the candidate path does not
exist. If it exists, the skill rescans and proposes the next unused number; it
never writes into an existing folder merely because the slug matches. If a
collision occurs after selection, the skill stops before writing, explains the
collision, and asks the user to select or confirm a new path. No concurrency
guarantee is claimed across simultaneous sessions.

For follow-on workflows, the selected feature folder stays fixed for the
conversation. A user returning in a new conversation can name the folder or
one of its artifacts. The highest-numbered-folder rule is a convenience for
starting from the latest feature, not a persistent active-feature marker.

### Artifact ownership by skill

| Workflow | Feature-folder behavior |
| --- | --- |
| `egm-brainstorm` | Propose a numbered folder and user-editable slug before its first write; save `concepts_brief.md` there. |
| `egm-draft` | Read the brief or selected notes from the chosen feature; write `design_draft.md` beside the feature's other artifacts. A final approved design remains in `docs/designs/<name>.md`. |
| `egm-review` | Save stage reports and `goldfish_review_report.md` in the selected feature folder. A review target outside the folder remains at its original path. |
| `egm-review-loop` | Place each unique run folder under the selected feature folder, following the per-run naming and ledger decisions in #278/#462. |
| `egm-resolve` | Read and update the report in the selected feature folder; retain existing standalone behavior when the user explicitly supplies a legacy report path. |

Do not change the report's content or the human approval gates. Every stage
continues to write only after its current workflow allows that write. When
`egm-brainstorm` or `egm-review-loop` delegates artifact writing to the
synthesizer, the parent passes the resolved artifact destination in the
synthesizer's task, as required by #267. A child does not infer the feature
folder from the user's prompt or from an unpassed workspace setting.

### Legacy compatibility

When no numbered feature folder exists, the five workflows continue to search
their existing legacy locations, including root-level
`concepts_brief.md` and `design_draft.md`. If a legacy artifact is selected,
the workflow continues beside it for that feature. It does not silently move,
copy, or rename legacy files into `egm/`. Starting a separate new brainstorm
creates a numbered folder and leaves the legacy artifacts intact.

This is a gradual adoption path: existing projects continue to work, while
new feature work gains a separate folder. If a user explicitly supplies a
folder or file, that path wins over automatic selection.

### Data flow

```mermaid
sequenceDiagram
    actor User
    participant Skill as EGM workflow skill
    participant Root as Artifact root
    participant Feature as Numbered feature folder
    participant Run as Review-loop run folder

    User->>Skill: Start feature workflow or name existing artifact
    Skill->>Root: Resolve configured root or default ./egm/
    Skill->>Feature: Select explicit, current, highest-numbered, or new folder
    Skill->>User: State selected path; ask to confirm/edit a new slug
    User-->>Skill: Confirm or name a folder/file
    Skill->>Feature: Read and write feature artifacts at existing approval gates
    Skill->>Run: For review-loop, create a unique per-run child folder
```

## Alternatives Considered

### Feature folders at the repository root

This avoids introducing a root directory name, but places numbered folders
beside source and documentation directories. Rejected for this proposal; one
`egm/` directory is easier to ignore and is consistent with the existing
artifact-directory convention.

### Timestamp-only folder names

Timestamps reduce collisions across branches but are harder to read and type.
The proposal keeps a short numeric sequence and handles an observed collision
by rescanning without overwriting. Simultaneous-session reservation remains a
known limit; a timestamp suffix can be considered later if real collisions
occur.

### One file per feature in a shared folder

Names such as `concepts_brief-feature-colors.md` avoid subdirectories but
scatter the many review reports and round files for a feature. A directory
keeps a feature's artifacts together.

### Automatic migration of legacy artifacts

Moving or copying files can break links and user conventions, and creates
ambiguity when several legacy files exist. Rejected; legacy artifacts remain
where they are unless the user explicitly selects or moves them.

### Git worktree per feature

Worktrees can isolate branches, but this proposal concerns artifact
organization and should work for users who do not use Git branches or
worktrees. EGM leaves Git state alone.

## Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| A user may expect `EGM artifact directory` to be the final output directory, not a parent. | Explain that feature-scoped workflows create a numbered child directory; keep this behavior limited to the five scoped workflows and document it in every affected guide. |
| Choosing the highest-numbered folder may select an older or unrelated feature. | State the selected path before reading or writing; explicit folder/file input always wins. |
| Two sessions may calculate the same next number. | Recheck before creation, never overwrite, rescan when a collision is observed, and stop for user input if a collision appears after selection. Do not claim atomic reservation. |
| Existing users may have root-level artifacts or custom layouts. | Keep legacy lookup and in-place continuation; do not migrate or delete files. |
| Review reports can include confidential target text. | Use the existing privacy guidance. Make no retention, upload, or sharing changes; folders remain local artifacts under the chosen root. |
| #278/#462 may choose a different per-run output location before #448 lands. | Keep run folders nested under the selected feature folder and reconcile the implementation order with maintainers before Stage 2. |

## Open Questions for Maintainers

1. Is `egm/` an acceptable default parent for these five workflows while #110
   remains open for the broader question of a default location for all EGM
   artifacts?
2. Is the configured `EGM artifact directory` the parent of numbered feature
   folders for these workflows, as #448 proposes, while other skills retain
   their current direct-output behavior?
3. For `/egm-review` on an existing design outside `egm/`, is deriving a
   feature-folder slug from the target filename and asking before creation the
   right default when no matching feature folder exists?
4. Should this feature-folder proposal merge before the #278/#462 run-folder
   implementation so review-loop run folders can be designed directly beneath
   a selected feature, or should the two designs merge independently and
   coordinate only in implementation?

## Detailed Implementation Plan

### Files to modify

| File | Change |
| --- | --- |
| `skills/egm-brainstorm/SKILL.md` | Allocate and confirm a feature folder before writing the brief; pass the exact brief path to the synthesizer; name the selected path in the handoff. |
| `skills/egm-draft/SKILL.md` | Resolve the selected feature folder, read legacy briefs as fallback, and keep drafts with their source feature. |
| `skills/egm-review/SKILL.md` | Save stage outputs in the selected feature folder while keeping the reviewed target in place. |
| `skills/egm-review-loop/SKILL.md` | Pass the selected feature folder as the parent for per-run artifacts and pass the exact report path to the synthesizer; reconcile with the then-current #278/#462 implementation. |
| `skills/egm-resolve/SKILL.md` | Resolve the report path from the selected feature folder and preserve explicit legacy report paths. |
| `skills/*/test_scenarios.yaml` for the five workflows | Cover new folder creation, explicit selection, highest-numbered fallback, legacy lookup, collision refusal, and report placement. |
| `skills/*/TEST.md` for the five workflows | Document the added path-selection scenarios. |
| `docs/claude.md`, `docs/codex.md`, `docs/copilot.md`, `docs/cursor.md`, `docs/muse.md`, `docs/opencode.md`, and `docs/harnesses.md` | Explain the feature-folder root, override nesting, explicit selection, and legacy fallback without changing host-specific capabilities. |
| `docs/getting_started.md`, `docs/site/getting-started.md`, `docs/site/workflow.md`, and `README.md` | Show where a feature's brief, draft, and review files live and how to return to an older feature. Keep examples consistent. |
| `tests/unit/test_harnesses.py`, host-guide tests, and link/integrity checks | Assert the shared path contract and generated-guide consistency where applicable. |
| `distributions/claude/` | Regenerate packaged documentation and skills with the repository packager; do not hand-edit generated copies. |

No implementation changes are proposed in this Stage 1 document. The final
Stage 2 list must be checked against the actual merged #278/#462 design and
current generated-runtime rules before implementation starts.

### Verification plan for Stage 2

* Add path scenarios for: first feature allocation; user-edited name; second
  feature without overwriting the first; explicit return to an older folder;
  highest-numbered selection; artifact-directory override nesting; relative
  paths; legacy input fallback; explicit file path; outside-workspace approval;
  and a pre-existing candidate collision.
* Verify report output from `egm-review`, `egm-review-loop`, and `egm-resolve`
  stays in the selected feature folder while the target remains unchanged.
  Confirm that brainstorm and review-loop synthesizer tasks name their exact
  permitted output path as required by #267.
* Verify approved designs still publish to `docs/designs/` and that this
  feature does not change `.gitignore` or Git branch state.
* Run `python -m pytest tests/unit`, site checks for touched site pages, runtime
  parity checks, and `git diff --check`.
* Check generated Claude distribution parity from a fresh packager output.
* Exercise one complete brainstorm → draft → review path in a disposable
  project, then start a second feature and confirm the first one's files are
  unchanged. Record any harness-specific limits; static scenarios alone do not
  prove live host path handling.

--------------------------------------------------------------------------------

### References

* [Issue #448: feature folders](https://github.com/google/elephant-goldfish-model/issues/448)
* [Issue #110: workflow output location](https://github.com/google/elephant-goldfish-model/issues/110)
* [PR #118: configurable artifact directory](https://github.com/google/elephant-goldfish-model/pull/118)
* [Issue #278 / PR #462: review-loop run records](https://github.com/google/elephant-goldfish-model/issues/278)
* [Issue #265: confirmation for paths outside the workspace](https://github.com/google/elephant-goldfish-model/issues/265)
* [Issue #267: synthesizer write boundary](https://github.com/google/elephant-goldfish-model/issues/267)
* [Issue #63: workflow resume](https://github.com/google/elephant-goldfish-model/issues/63)
