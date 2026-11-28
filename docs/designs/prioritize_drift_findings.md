# Prioritize evidence-backed drift findings

- **Status:** Proposal. Maintainer scope approval and design review pending.
- **Date:** 2026-11-28
- **Tracking:** [#522](https://github.com/google/elephant-goldfish-model/issues/522)

## Problem statement

The `/egm-drift-report` skill ([`skills/egm-drift-report/SKILL.md`](../../skills/egm-drift-report/SKILL.md))
compares design documents against the codebase and writes `{YYYY-MM-DD}_DRIFT_REPORT.md`
in the working directory as a flat bulleted list under `## <DESIGN_DOC_NAME>`.
That format tells maintainers that differences exist, but omits three things
needed to act on them:

1. **Remediation order**: Every discrepancy is listed at the same weight, so
   maintainers cannot tell whether a finding blocks correctness or is minor
   wording drift.
2. **Paired evidence**: Findings do not require side-by-side citations of the
   design requirement and the corresponding code state.
3. **Direction of fix**: The report does not distinguish a missing
   implementation from an intentional deviation, nor propose whether to update
   the code, update the design, or record an accepted deviation.

### Example ambiguity in current specs

In the current repository, two findings can appear side by side with no clear
remediation order:

1. **Unimplemented evaluation runner vs. benchmark wording**:
   [`docs/designs/review.md`](review.md) (lines 186, 189, 192) describes
   `test_scenarios.yaml` as an evaluation benchmark suite evaluating model
   precision and recall, while [`docs/designs/drift_report.md`](drift_report.md)
   (line 119) notes that `tests/unit/test_scenario_coverage.py` validates
   structure only and no in-repo runner executes the assertions.
2. **Protocol output format drift**: [`docs/designs/drift_report.md`](drift_report.md)
   (lines 88–94) specifies `file:line` references in report items, whereas
   [`skills/egm-drift-report/SKILL.md`](../../skills/egm-drift-report/SKILL.md)
   (lines 49–56) specifies a generic bulleted list without `file:line` or
   priority fields.

## Scope

This specification defines evidence-backed prioritization and classification
for `/egm-drift-report` under
[#522](https://github.com/google/elephant-goldfish-model/issues/522), following
the [two-stage contribution workflow](../../CONTRIBUTING.md#track-2-feature--architectural-change-two-stage-alignment)
(Stage 1: this design doc; Stage 2: skill and test updates).

### Goals

- Order drift findings by priority (`P0`, `P1`, `P2`) with an explicit
  rationale for why higher-priority items should be addressed first, plus a
  top-level summary of `P0`/`P1` findings across all scanned documents.
- Require each finding to cite both the **design requirement** (document path
  and section or line, or verified absence for undocumented code) and **code
  evidence** (source path, symbol/line, or verified absence).
- Separate **divergence category** (reusing the existing four categories plus
  wording drift) from **disposition** (**missing implementation** vs.
  **intentional deviation** vs. **ambiguous**), and propose one concrete next
  step: a **code change**, a **design correction**, or a **decision to record
  an accepted deviation**.
- Keep `/egm-drift-report` read-only with respect to repository source and
  design files, leaving all remediation edits for human approval.

### Non-goals

- Automating code edits, design document rewrites, or pull request creation
  without explicit human approval (left to a separate workflow).
- Checking an individual implementation diff against its approved design
  (owned by [#436](https://github.com/google/elephant-goldfish-model/issues/436)).
- Reconciling the existing documentation discrepancy backlog (owned by
  [#271](https://github.com/google/elephant-goldfish-model/issues/271)).

## Proposed design

### Report and finding structure

Update the `{YYYY-MM-DD}_DRIFT_REPORT.md` output contract in
[`skills/egm-drift-report/SKILL.md`](../../skills/egm-drift-report/SKILL.md)
and [`docs/designs/drift_report.md`](drift_report.md) to start with a
cross-document `## Priority Summary` listing `P0` and `P1` findings, followed
by per-document sections ordered from `P0` to `P2`:

```markdown
## Priority Summary

- [P0] `<DESIGN_DOC_NAME>`: <Short finding title> (Disposition: <...>; Action: <...>)
- [P1] `<DESIGN_DOC_NAME>`: <Short finding title> (Disposition: <...>; Action: <...>)

## <DESIGN_DOC_NAME>

### [P0 | P1 | P2] <Short finding title>
- **Category**: Missing feature | Incomplete model | Logic shortcut | Architectural divergence | Wording drift
- **Disposition**: Missing implementation | Intentional deviation | Ambiguous
- **Design requirement**: `<design-doc-path>:<line-or-section>` — <requirement> | `verified absence in <design-doc-path>`
- **Code evidence**: `<source-path>:<line-or-symbol>` — <observed behavior> | `verified absence in <expected-path>`
- **Priority rationale**: <why this rank applies>
- **Proposed action**: Code change | Design correction | Record accepted deviation — <specific next step for human approval>
```

Documents with zero discrepancies continue to report `No drift detected.` To
keep reports concise on large scans, `P2` wording-drift items in the same
document may be grouped into a single `P2` entry listing the affected lines.

### Prioritization and classification rules

1. **Priority levels** (chosen over `Blocker | Major | Nit` review labels to
   reflect remediation urgency in a backlog scan, matching `P0`–`P2` triage):
   - **P0 (Contract or safety break)**: Implemented behavior contradicts a
     required guardrail, drops data, or silently bypasses a documented gate.
   - **P1 (Functional gap)**: A designed feature, model field, or validation
     step is missing or incomplete, or an intentional architectural change
     leaves the spec misleading.
   - **P2 (Wording or non-blocking drift)**: Naming, examples, or status
     descriptions diverge without changing runtime behavior.
2. **Distinguishing missing implementations from intentional deviations**:
   - Classify disposition as **Missing implementation** when the design
     specifies behavior that is absent in code with no replacement mechanism or
     documented supersession. Propose a **Code change** (or ask the maintainer
     to descope the requirement).
   - Classify disposition as **Intentional deviation** when code implements a
     coherent alternative, newer pattern, or explicit guardrail not yet
     reflected in the design. Propose a **Design correction** or **Record
     accepted deviation**.
   - Classify disposition as **Ambiguous** when intent cannot be determined
     from code and docs alone, and ask the maintainer to choose between code
     alignment and design update.
3. **Recording accepted deviations**: When a maintainer decides to keep an
   intentional deviation without rewriting the main spec, they record it inline
   under an `## Accepted Deviations` section in the target design document
   (with date, rationale, and tracking issue). Subsequent `/egm-drift-report`
   scans check `## Accepted Deviations` and do not re-flag recorded items.
4. **Human approval boundary**: `/egm-drift-report` only writes
   `{YYYY-MM-DD}_DRIFT_REPORT.md`. It never modifies `skills/`, `agents/`,
   source files, or `docs/designs/` during a drift scan.

## Alternatives considered

1. **Keep the flat bulleted list and add only a `[P0|P1|P2]` prefix**: Rejected
   because a bare priority tag does not require paired design/code evidence or
   distinguish missing implementations from intentional deviations, leaving
   maintainers to re-read both files before deciding whether to edit code or
   docs.
2. **Add a separate accepted-deviations registry file or automated fix script**:
   Rejected as unnecessary overhead for Stage 1/2: a separate registry creates
   another file to keep in sync, and automated edits cross the human-approval
   Non-Goal. Recording accepted deviations inline in the target design doc
   keeps spec and exceptions together.

## Risks and mitigations

- **Output buffer growth on large scans**: Structured blocks use more lines
  than single bullets. *Mitigation*: Keep `## Priority Summary` limited to `P0`
  and `P1` items, allow grouping `P2` wording-drift items per document, and
  preserve sequential per-document processing.
- **Misclassified intent**: A scanner might guess wrong when code diverges from
  a spec. *Mitigation*: Provide the explicit `Ambiguous` disposition and leave
  all edits to human approval.
- **Stale accepted deviations**: Inline `## Accepted Deviations` entries could
  outlive their rationale. *Mitigation*: Require a date and tracking issue on
  each entry so maintainers can revisit them during periodic cleanups.

## Validation plan

Because `tests/unit/test_scenario_coverage.py` validates scenario schema
structure only and no in-repo runner executes `test_scenarios.yaml` assertions
([`docs/designs/drift_report.md`](drift_report.md), line 119), Stage 2
validation combines offline checks with a recorded manual run:

1. **Offline unit checks (`pytest tests/unit`)**: Verify frontmatter, relative
   Markdown links, table formatting, scenario schema coverage, and unit
   assertions that [`skills/egm-drift-report/SKILL.md`](../../skills/egm-drift-report/SKILL.md)
   defines `## Priority Summary`, `Category`, `Disposition`, `Design requirement`,
   `Code evidence`, `Priority rationale`, and `Proposed action`.
2. **Controlled drift scenario**: Define a scenario in
   [`skills/egm-drift-report/test_scenarios.yaml`](../../skills/egm-drift-report/test_scenarios.yaml)
   and manual verification steps in
   [`skills/egm-drift-report/TEST.md`](../../skills/egm-drift-report/TEST.md)
   covering both a missing implementation and an intentional deviation. Record
   a live `/egm-drift-report` run on that case in the Stage 2 PR's
   `## Verification` section confirming priority ordering, paired citations,
   distinct dispositions/actions, and zero edits outside the report artifact.

## Implementation files (Stage 2 target)

- [`skills/egm-drift-report/SKILL.md`](../../skills/egm-drift-report/SKILL.md):
  Update step 4 report format and prioritization/classification guidance.
- [`skills/egm-drift-report/test_scenarios.yaml`](../../skills/egm-drift-report/test_scenarios.yaml)
  and [`skills/egm-drift-report/TEST.md`](../../skills/egm-drift-report/TEST.md):
  Add controlled drift scenario and manual verification instructions.
- [`docs/designs/drift_report.md`](drift_report.md): Update "Execution
  Protocol" and "Two-Way Reconciliation" to match.
