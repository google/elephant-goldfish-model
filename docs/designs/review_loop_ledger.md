# Review Loop Run Record and Status Ledger

*   **Author:** [@mbachaud](https://github.com/mbachaud)
*   **Status:** Draft
*   **Date:** 2026-11-11

--------------------------------------------------------------------------------

## Overview

`egm-review-loop` decides across rounds which findings are settled, fixed, or
re-opened, and when the loop has converged (`skills/egm-review-loop/SKILL.md`,
§2.2–2.4). Those decisions live only in the Elephant's context. This design
keeps each round's files on disk and adds an append-only `ledger.md`, so a
human can later check how a run reached "converged". It changes skill text
only. It adds no scripts, hooks, or runtime pieces.

Tracking issue: [#278](https://github.com/google/elephant-goldfish-model/issues/278).

## The Problem

Each round, the synthesizer writes `goldfish_review_report.md` with a Reviewer
Status table. `egm-resolve` then overwrites the same file with its annotated
layout, which has no status table and no finding ids. In direct dispatch there
is no synthesizer report at all. After context compaction or a new session, no
file shows what reviewers raised in earlier rounds, how each finding was
handled, or why the loop reported "converged".

The Elephant also makes the judgments that decide convergence: which reviewer
findings are the same finding, whether a new finding is "the same issue at the
same scope" as an earlier one, whether a round is clean, and whether a change
is churn. Today none of those judgments is written down.

Proposed solution: write each round's files under round-numbered names in one
folder per run, including the consolidated findings list with ids. Add a ledger
that records each decision as a row, links a re-raised finding to its first id,
and ends each round with a summary row.

## Goals

*   Each round's reviewer report, consolidated findings list, and resolve
    report survive the run under round-numbered names. None overwrites
    another.
*   Every finding id can be traced to the reviewer-written text it came from.
*   `ledger.md` records one row per decision: finding id, `same-as` id,
    severity, status, who decided, a short reason, and cited evidence for
    contests. Rows sit under a heading for their round.
*   A finding raised again in a later round can be traced to its first id with
    one text search.
*   Each round ends with one summary row: reviewer status, clean or not, the
    stop decision, and the count of findings by status. A reader can check that
    the counts add up without opening the round reports.
*   The completion message says how many findings closed without a fix, so
    "converged" cannot hide them.
*   The convergence, cap, and churn rules in §2.4 keep their current wording.
    The design only writes down which statuses count as settled (see Open
    Questions).

## Non-Goals

*   Changing the convergence, cap, or churn rules.
*   Hooks, scripts, hashes, or any new runtime piece. Read-only enforcement
    stays with host tool limits (#261, #262).
*   Resume. The ledger is a record for a human to read, not state the loop
    restores from. #63 keeps its own acceptance criteria.
*   A new default output folder. #110 stays open as is.
*   K9, a read-only checker persona that audits the ledger. It could be a
    follow-up once this record exists.
*   Changing `egm-resolve` when it runs on its own, outside the loop. This
    includes the second `egm-resolve` call that `egm-review` offers at its
    stage checkpoint after the loop returns (see Risks and Mitigations).

## Open Questions

*   **Settled statuses (needs a maintainer decision):** §2.4 settles findings
    that are "contested or recorded without a fix". This design treats
    `user-rejected` and user-confirmed `escalated` as settled for convergence.
    An `escalated` finding that the user never saw (bypassed by auto accept
    or "continue") stays unsettled. Is that the intended reading of §2.4? The
    alternative is to leave `user-rejected` unsettled too, which means a
    finding the user declined to fix blocks convergence every round it is
    raised again.
*   **Re-raised settled findings:** §2.4 says not to re-open a settled finding
    that is raised again, but does not say whether it still goes to
    `egm-resolve`. This design records it in the ledger with the settled status
    carried forward and leaves it out of the `FindingsList` sent to resolve.
    Is that acceptable, or should resolve see it again?

## Critical User Journeys (CUJs)

### CUJ 1: Check a converged run after compaction

*   **Given**: A loop on `docs/designs/foo.md` reported "converged" after 4
    rounds, and the Elephant's context was later compacted.
*   **When**: The human opens the run folder named in the completion message.
*   **Then**: `ledger.md` has four round blocks. The summary rows for rounds 3
    and 4 have `yes` in the `clean` column. Every id in
    `round-03-findings.md` and `round-04-findings.md` has one final-status row
    in its round block. Each summary's counts match its rows, and each id's
    `source` entry points to a heading in that round's `round-NN-review.md`.

### CUJ 2: Trace a re-opened finding

*   **Given**: `egm-design-1-2` was fixed in round 1. In round 3,
    `egm-structural-3-1` raises the same issue at the same scope.
*   **When**: The Elephant consolidates round 3's findings.
*   **Then**: The ledger gets a `re-opened` row for `egm-structural-3-1` with
    `same-as: egm-design-1-2`, decided by `elephant`, with the reason for the
    match. A second row records how resolve handled it this round. Searching
    the ledger for `egm-design-1-2` returns the whole history, and the last
    match is the current status.

### CUJ 3: A settled finding is raised again

*   **Given**: `egm-style-1-4` was contested in round 1 with cited evidence.
    In round 2, `egm-style-2-1` raises the same issue.
*   **When**: The Elephant consolidates round 2's findings.
*   **Then**: The ledger gets one row for `egm-style-2-1` with
    `same-as: egm-style-1-4`, status `contested`, decided by `elephant`, reason
    "settled in round 1; not re-opened (§2.4)", and evidence
    `see egm-style-1-4`. The finding is not sent to resolve, and it does not
    make the round unclean.

### CUJ 4: Direct dispatch

*   **Given**: The harness cannot nest subagents, so the loop dispatches
    reviewers directly and there is no synthesizer report.
*   **When**: A round's reviewers return.
*   **Then**: The Elephant writes `round-NN-review.md` from the reviewer
    outputs, with a first line stating that the file is self-reported. The
    ledger header reads `**Dispatch:** direct (self-reported)`.

## Technical Plan (Architecture)

### Run folder

At the start of the first round, the loop creates one folder for the run inside
the artifact directory (the working directory unless `EGM artifact directory:`
names another, per #118 and `docs/harnesses.md`):

```text
<artifact dir>/review-loop-<target stem>-<YYYYMMDD-HHMMSS>/
  round-01-review.md     # reviewer-written report (self-reported in direct dispatch)
  round-01-findings.md   # consolidated FindingsList with ids, written before resolve
  round-01-resolved.md   # egm-resolve annotated report, with ids and Reviewer Status
  round-02-review.md
  ...
  ledger.md              # append-only
```

If that folder already exists, the loop adds `-2`, `-3`, and so on. The loop
states the full path of the run folder when it creates it, at the start of
every round, and in the Step 3 completion message, and uses that path for the
whole run. It does not resolve the artifact directory again in later rounds.

The synthesizer already writes to the report file its caller names
(`agents/synthesizer.md`, REVIEW step 4), so the loop passes
`round-NN-review.md` and the synthesizer needs no change.

`egm-resolve` writes `round-NN-resolved.md` and keeps the finding ids and the
Reviewer Status table. It also writes `goldfish_review_report.md` as today.
`egm-review`'s resolve step names that file as its fallback source of findings,
and the draft `egm-ask` design (`docs/designs/ask.md`) reads it to detect
review state. That file is the latest view; the round files are the record.

### Consolidated findings file

The synthesizer's report has no ids, and the synthesizer deduplicates across
reviewers. The Elephant assigns ids when it consolidates (§2.2 step 2). So
before calling resolve, the loop writes `round-NN-findings.md`, one row per
finding:

```markdown
| id | reviewer | severity | scope | source | same-as |
| --- | --- | --- | --- | --- | --- |
| egm-structural-3-1 | egm-structural | Major | §Goals | "Goals miss failure case" (review heading) | egm-design-1-2 |
| egm-design-3-1 | egm-design | Major | §Technical Plan | "Scope note ignored", "Unclear scope" (merged) | |
```

*   `<reviewer>` in an id is the reviewer name the loop was given in
    `Reviewers` (for example `egm-design` when `egm-review` calls the loop).
*   `source` names the heading or headings in `round-NN-review.md` the finding
    came from, so a reader can check the mapping against reviewer-written
    text. When the Elephant merges duplicates raised in the same round, it
    gives them one id and lists every source heading.
*   This file is written before resolve yields to the user, so the ids and
    matches survive compaction during resolve.

### Data flow per round

```text
2.2 swarm ──► round-NN-review.md (synthesizer, or Elephant in direct dispatch)
     │
     ▼
consolidate: merge duplicates, assign ids, match against ledger (same-as),
decide clean ──► round-NN-findings.md
     │                       │
     │ new + re-opened       │ settled re-raises: ledger rows only
     ▼                       │
2.3 egm-resolve ──► round-NN-resolved.md + goldfish_review_report.md
     │ returns a decision per id (outcome, who decided, reason, evidence)
     ▼
2.4 loop appends the round block to ledger.md, then decides stop/continue
```

The loop is the only writer of `ledger.md`. Resolve returns decisions and the
loop records them, so the ledger has one author per run.

### Matching rules for `same-as`

*   **Root id.** `same-as` holds the id the finding had when it was first
    raised, never an intermediate one. One search for the root id returns the
    full history, and the last matching row is the current status. It is empty
    for a new finding.
*   **One root per finding.** If a finding could match two roots, match the
    one with the same affected scope. If it is still ambiguous, treat the
    finding as new and say so in the reason. A new finding is not settled, so
    the doubt counts against convergence, not for it.
*   **Splits.** If a later round raises two findings that each match one
    earlier finding, both get that root as `same-as`, with their own rows.
*   **Stated judgment.** The match is the Elephant's judgment. The reason
    column states why, so a later reader or checker can dispute it.

### Ledger format

```markdown
# Review loop ledger

**Target:** `docs/designs/foo.md`
**Run:** `review-loop-foo-20261111-140203`
**Dispatch:** synthesizer

## Round 3

| id | same-as | severity | status | decided by | reason | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| egm-structural-3-1 | egm-design-1-2 | Major | re-opened | elephant | Same gap in §Goals after the round 1 fix | |
| egm-structural-3-1 | egm-design-1-2 | Major | fixed | user | Accepted proposed fix | |
| egm-style-3-1 | egm-style-1-4 | Major | contested | elephant | Settled in round 1; not re-opened (§2.4) | see egm-style-1-4 |
| egm-design-3-1 | | Major | contested | elephant | Reviewer missed the scope note | `skills/egm-review-loop/SKILL.md` §2.4 |
| egm-design-3-2 | | Nit | accepted-risk | elephant | Nit declined | |

| round | completed | not run | clean | stop | findings | fixed | contested | accepted-risk | escalated | user-rejected | re-opened |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | egm-design, egm-structural, egm-style | | no | continue | 4 | 1 | 2 | 1 | 0 | 0 | 1 |
```

Round 3 is not clean: `egm-structural-3-1` is a re-opened Major, and
`egm-design-3-1` is a new Major that was not settled when the clean decision
was made, before resolve. The re-raised `egm-style-3-1` does not block, because
it was already settled.

Rules:

*   **Final status.** Each id in `round-NN-findings.md` gets exactly one row
    with a final status: `fixed`, `contested`, `accepted-risk`, `escalated`,
    or `user-rejected`. A re-opened finding also gets one `re-opened` row
    before its final row.
*   **Summary row.** `findings` is the number of rows in
    `round-NN-findings.md`. `fixed + contested + accepted-risk + escalated +
    user-rejected` must equal `findings`. `re-opened` is counted separately.
    `clean` is decided from the review results before fixes are applied, as
    §2.4 already requires. `stop` is `continue`, `converged`, `cap`, or
    `churn`. For churn, the reason column of the affected rows names the fix
    that would be reverted.
*   **Evidence.** A `contested` row records the evidence the contest cited (a
    file and symbol, or a decision in the document). #344 needs that evidence
    to survive compaction. A re-raised settled row may point to its root with
    `see <root id>` instead of copying the evidence.
*   **Append-only.** The loop appends one round block after resolve returns
    and never edits earlier blocks.

### Mapping resolve outcomes to statuses

| Resolve outcome | Status | Decided by | Settled |
| --- | --- | --- | --- |
| PROPOSE FIX, applied (auto accept, accepted in breakdown, or custom instruction) | `fixed` | `user` | no |
| PROPOSE FIX, skipped, or "continue / no changes" | `user-rejected` | `user` | yes (pending Open Question 1) |
| CONTEST, kept | `contested` | `elephant` | yes |
| CONTEST, overruled and fixed | `fixed` | `user` | no |
| ESCALATE, user confirmed no change | `escalated` | `user` | yes (pending Open Question 1) |
| ESCALATE, fact added to the document | `fixed` | `user` | no |
| ESCALATE, bypassed by auto accept or "continue" | `escalated` | `elephant` | no |
| DECLINE (Nit recorded without a fix) | `accepted-risk` | `elephant` | yes |
| Re-raised settled finding (§2.4 match) | prior settled status | `elephant` | yes |
| Re-raised fixed finding (§2.4 match) | `re-opened`, then its new final status | `elephant`, then per row above | per final status |

**Default rule.** Some outcomes have no row above, for example a custom
instruction that touches a CONTEST item, or a comment on the report file. For
these, if the target text changed for the finding, record `fixed` by `user`.
If not, record the no-fix status of its category: PROPOSE FIX →
`user-rejected`, CONTEST → `contested`, ESCALATE → `escalated` by `elephant`
(unsettled), DECLINE → `accepted-risk`. Resolve does not exit while a
breakdown item is still under "Discuss", so that case does not reach the
ledger.

**Completion message.** Step 3's summary adds one line: the counts of
`user-rejected`, `escalated`, `contested`, and `accepted-risk` findings
closed without a fix, and the run folder path.

### Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Append-only is a written convention. The Elephant could edit an earlier block. | State it as a limit in the skill text. Earlier blocks are also checkable against the round files, which the ledger does not replace. A K9 checker could verify this later. |
| In direct dispatch the Elephant writes `round-NN-review.md`, so the record shows the decisions are consistent with what was recorded, not what reviewers said. | Mark the file and the ledger header self-reported, and state the limit in the skill text. |
| The Elephant makes a wrong `same-as` match. | Every match has a stated reason in the ledger, and ambiguous matches are treated as new (unsettled). A human can dispute a match from the ledger alone. |
| Compaction or a session ending during resolve. Fixes may be applied with no ledger block for that round. | `round-NN-findings.md` is written before resolve, so ids and matches survive. A round with a findings file and no ledger block has no recorded decisions. The skill tells the reader to compare the target against that round's resolve report. Resuming the round is #63's scope. |
| `user-rejected` findings let the loop converge with nothing fixed. | They are counted in every summary row and in the completion message. Whether they count as settled is Open Question 1. |
| Two runs on the same target start in the same second. | Numeric suffix on an existing folder name. |
| `egm-review` calls `egm-resolve` again at its stage checkpoint, after the loop returns. Those decisions are not in the ledger. | State it as a limit. That call is outside the loop and out of scope here. |
| #344 and #287 edit the same text (§2.4, `review.md`, `synthesizer.md`). | Whichever lands second rebases. The ledger's evidence field is designed to fit #344's rule, and the doc changes here are additive to #287's. |

## Alternatives Considered

### Alternative A: Append every round to one report file

*   **Pros**: One file per run.
*   **Cons**: The synthesizer writes a whole file per call, so appending needs
    the Elephant to merge reports, which is the overwrite risk this design
    removes. One long file is harder to diff per round.
*   **Reason for Rejection**: Rejected by author: separate round files keep
    reviewer-written text apart from Elephant-written text, and need no merge
    step.

### Alternative B: A mutable ledger with one row per finding

*   **Pros**: The current status is always in one place.
*   **Cons**: Each update erases the earlier decision.
*   **Reason for Rejection**: Rejected by author: it loses the decision history
    a check after compaction needs. With `same-as` on the root id, the
    current status is still one search away in the append-only form.

### Alternative C: `same-as` points to the previous id

*   **Pros**: Records the exact link the Elephant matched.
*   **Cons**: Finding the history needs one search per hop.
*   **Reason for Rejection**: Rejected by author: the root id finds the latest
    row in one search, and the reason column still records which earlier
    finding was matched.

### Alternative D: Round facts only in each round report

*   **Pros**: No summary rows in the ledger.
*   **Cons**: Checking the counts means opening every round report.
*   **Reason for Rejection**: Rejected by author: the summary row costs one
    line per round and lets a reader check the counts from the ledger alone.

--------------------------------------------------------------------------------

## Non-Functional Requirements

*   **Security & Privacy**: Round files and the ledger can quote confidential
    target text, including in the ledger's `reason` and `evidence` columns.
    They are kept until the user deletes them, like other EGM outputs.
    `docs/privacy.md` gets one line naming the run folder and saying that it
    can quote target text. When the artifact directory is inside a repository,
    users may want to ignore run folders in version control. This design does
    not change `.gitignore`.
*   **Performance & Latency**: Three files per round plus the ledger, so 16
    files for a 5-round run. Writing the findings file and the ledger block
    adds two short tables per round to the Elephant's output.
*   **Rollout & Rollback**: Skill text only. Standalone `egm-resolve` and
    `egm-review` keep their current file names. Rollback is a revert of the
    implementation PR.

--------------------------------------------------------------------------------

### Additional Resources

*   `skills/egm-review-loop/SKILL.md` §2.2–2.4 (since
    [#168](https://github.com/google/elephant-goldfish-model/pull/168))
*   `skills/egm-resolve/SKILL.md` Steps 2–5
*   `agents/synthesizer.md` REVIEW mode
*   `skills/egm-review/SKILL.md`, Critic Review and Implementation Readiness
    subflows
*   `docs/harnesses.md`, "Artifact Directory"
    ([#118](https://github.com/google/elephant-goldfish-model/pull/118))
*   `docs/privacy.md`
*   Related:
    [#344](https://github.com/google/elephant-goldfish-model/pull/344)
    (re-open a contested finding when its evidence no longer holds; edits the
    same §2.4 text),
    [#287](https://github.com/google/elephant-goldfish-model/pull/287)
    (aligns `review.md` and `synthesizer.md` with the skills),
    [#63](https://github.com/google/elephant-goldfish-model/issues/63)
    (resume),
    [#110](https://github.com/google/elephant-goldfish-model/issues/110)
    (dedicated output folder)

### Future Improvements

*   **K9 checker**: A read-only Goldfish persona that reads only the run folder
    and the target, checks the Elephant's recorded decisions against the
    reviewer-written round reports, and reports to the human on every exit.
*   **Resume**: #63 could later decide whether the run folder is enough state
    to resume from. This design does not assume it.

--------------------------------------------------------------------------------

## Detailed Implementation Plan

### Target Files to Create/Modify

#### 1. `skills/egm-review-loop/SKILL.md` (Modify)

*   **Type / Scope**: Skill instructions.
*   **Proposed Changes**:
    *   New "Run Record" section: run folder name, location, and collision
        suffix; file names; findings-file and ledger formats; matching rules;
        summary row; status mapping with the default rule; and the stated
        limits from Risks and Mitigations.
    *   §2.2: pass `round-NN-review.md` in the run folder to the synthesizer.
        In direct dispatch, the Elephant writes that file and marks it
        self-reported. When consolidating, merge duplicates, assign ids, match
        against the ledger, and write `round-NN-findings.md`. Leave re-raised
        settled findings out of the `FindingsList`.
    *   §2.3: pass `ReportPath` (`round-NN-resolved.md`) to `egm-resolve`.
    *   §2.4: list the settled statuses. After resolve returns, append the
        round block to `ledger.md`, then decide stop or continue.
    *   Step 3: add the run folder path and the counts of findings closed
        without a fix to the completion summary.

#### 2. `skills/egm-resolve/SKILL.md` (Modify)

*   **Type / Scope**: Skill instructions.
*   **Proposed Changes**: Optional input `ReportPath`. When it is given, write
    the annotated report there, keep each finding's id and the Reviewer Status
    table, and also write `goldfish_review_report.md`. The Step 5 handoff
    returns, for each finding id, the outcome, who decided, a short reason,
    and cited evidence for contests. Standalone behavior is unchanged.

#### 3. `skills/egm-review-loop/test_scenarios.yaml` (Modify)

*   **Type / Scope**: Behavioral eval scenarios.
*   **Proposed Changes**: Scenarios for: a re-opened finding gets a `same-as`
    row with the root id; a settled re-raise is recorded and not sent to
    resolve; an ambiguous match is treated as new; the summary counts add up
    to the rows in the findings file; direct dispatch marks the round review
    file self-reported; round files are not overwritten; the completion
    message names the run folder and the no-fix counts.

#### 4. `skills/egm-review-loop/TEST.md` (Modify)

*   **Type / Scope**: Test description.
*   **Proposed Changes**: Describe the new scenarios.

#### 5. `skills/egm-resolve/test_scenarios.yaml` (Modify)

*   **Type / Scope**: Behavioral eval scenarios.
*   **Proposed Changes**: With `ReportPath`, the report keeps ids and the
    Reviewer Status table, `goldfish_review_report.md` is also written, and
    the handoff returns a decision per id. Without it, behavior matches today.

#### 6. `skills/egm-resolve/TEST.md` (Modify)

*   **Type / Scope**: Test description.
*   **Proposed Changes**: Describe the new scenario.

#### 7. `docs/designs/review.md` (Modify)

*   **Type / Scope**: Design doc.
*   **Proposed Changes**: Additive note on the run folder and round files.
    Coordinate with #287.

#### 8. `docs/designs/synthesizer.md` (Modify)

*   **Type / Scope**: Design doc.
*   **Proposed Changes**: Note that the loop names a round-numbered report
    file. Coordinate with #287.

#### 9. `docs/privacy.md` (Modify)

*   **Type / Scope**: Data handling notice.
*   **Proposed Changes**: One line: review-loop runs keep round files and a
    ledger in a run folder in the artifact directory until the user deletes
    them, and those files can quote target text.

#### 10. `docs/designs/README.md` (Modify)

*   **Type / Scope**: Design index.
*   **Proposed Changes**: Register this document.

#### 11. `distributions/claude/` (Modify)

*   **Type / Scope**: Generated runtime copy.
*   **Proposed Changes**: Regenerate with `scripts/pack_plugin.py` after items
    1, 2, and 9. Do not edit the copies by hand.

### Verification Plan

*   **Compilation/Build**: `python3 scripts/pack_plugin.py --target claude`,
    then sync into `distributions/claude/`.
*   **Unit Tests**: `pytest tests/unit`, including runtime bundle parity,
    frontmatter, and link integrity.
*   **Static Analysis & Linting**: N/A beyond the unit checks; skill text
    only.
*   **Test Coverage Requirement**: Each new rule in the "Run Record" section
    has at least one scenario in item 3 or 5.
*   **E2E/Integration**: Run `egm-review-loop` on a sample design doc for at
    least three rounds, once with the synthesizer and once in direct
    dispatch. Check that no round file is overwritten, that every id in each
    findings file has one final row, that each summary's counts match its
    rows, and that the completion message names the run folder.

--------------------------------------------------------------------------------

<!-- Provenance: Indicates initial structural drafting via EGM. -->

*Drafted with EGM*
