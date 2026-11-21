# Review Loop Run Record and Status Ledger

*   **Author:** [@mbachaud](https://github.com/mbachaud)
*   **Status:** Draft
*   **Date:** 2026-11-15

--------------------------------------------------------------------------------

## Overview

`egm-review-loop` decides each round whether the round is clean, and when the
loop stops (`skills/egm-review-loop/SKILL.md`, §2.4). Those decisions live
only in the Elephant's context, and each round's report overwrites the one
before. This design keeps each round's report files in one folder per run and
adds a short append-only `ledger.md` that records why the loop stopped. It
changes skill text only. It adds no scripts, hooks, or runtime pieces.

This is a first step. Tracking which findings were re-opened or settled across
rounds is left to
[#344](https://github.com/google/elephant-goldfish-model/pull/344) and later
work (see Non-Goals).

Tracking issue: [#278](https://github.com/google/elephant-goldfish-model/issues/278).

## The Problem

Each round, the synthesizer writes `goldfish_review_report.md` with a Reviewer
Status table. `egm-resolve` then overwrites the same file with its annotated
layout, and the next round overwrites it again. In direct dispatch there is no
synthesizer report at all. After context compaction or a new session, no file
shows what reviewers raised in earlier rounds, or why the loop reported
"converged", stopped at the cap, or was halted.

The Elephant decides whether a round is clean before it applies that round's
fixes (§2.4). `egm-resolve` then pauses at Step 4 for human input across a turn
that can last hours or compact. Today the clean decision, the reviewer status,
and the findings that blocked the round are not written down, so they can be
lost before the loop reaches its stop check.

## Goals

*   Each round's review report and resolve report (when resolve runs) survive
    the run under round-numbered names in one run folder. None overwrites
    another.
*   Each finding heading in a round's resolve report starts with its finding
    id, so an id in the ledger can be found in the round files.
*   `ledger.md` gets one row per round, written before resolve yields to the
    user: the reviewers that completed and did not run, whether the round was
    clean, the ids of the findings that made it not clean, and the §2.4 stop
    result.
*   The ledger records how the run ended and who decided: converged, the
    user's answer at cap or churn, or a manual halt.
*   The completion message names the run folder.
*   This design does not change the convergence, cap, and churn rules in
    §2.4, or which findings count as settled. It records what those rules
    decided.

## Non-Goals

*   Changing the convergence, cap, churn, or settled rules.
*   Re-opening behavior: recording which finding in a later round matches an
    earlier one, and whether a settled finding is re-opened. #344 owns this.
    The ledger records the Elephant's clean decision and the findings that
    blocked it, not the matching behind that decision.
*   A per-finding status history (one ledger row per resolve decision). The
    per-finding outcome for a round stays in that round's resolve report.
*   Hooks, scripts, hashes, or any new runtime piece. Read-only enforcement
    stays with host tool limits
    ([#261](https://github.com/google/elephant-goldfish-model/issues/261),
    [#262](https://github.com/google/elephant-goldfish-model/issues/262)).
*   Resume. The ledger is a record for a human to read, not state the loop
    restores from.
    [#63](https://github.com/google/elephant-goldfish-model/issues/63) keeps
    its own acceptance criteria.
*   A new default output folder.
    [#110](https://github.com/google/elephant-goldfish-model/issues/110) stays
    open as is. If
    [#448](https://github.com/google/elephant-goldfish-model/issues/448)
    adds a folder per feature, the run folder goes inside it, with the same
    name.
*   Changing `egm-resolve` when it runs on its own, outside the loop. This
    includes the second `egm-resolve` call that `egm-review` offers at its
    stage checkpoint after the loop returns (see Risks and Mitigations).

## Open Questions

None at this stage. Which statuses count as settled, and whether a re-raised
settled finding goes to resolve again, were open questions in an earlier
revision. They belong to the re-opening work in #344 and to
[#433](https://github.com/google/elephant-goldfish-model/issues/433).

## Critical User Journeys (CUJs)

### CUJ 1: Check why a run converged after compaction

*   **Given**: A loop on `docs/designs/foo.md` reported "converged" after 4
    rounds, and the Elephant's context was later compacted.
*   **When**: The human opens the run folder named in the completion message.
*   **Then**: `ledger.md` has four round blocks. Rounds 3 and 4 have `yes` in
    the `clean` column and `none` in `blocking`. Round 4 has `converged` in
    `stop`. The ledger ends with a run decision block: after round 4,
    `converged`, decided by `elephant`. Each id in the `blocking` column of
    rounds 1 and 2 is a heading in that round's `round-NN-resolved.md`.

### CUJ 2: Check a run that stopped at the cap

*   **Given**: A loop reached round 5 with a Major still open, and the user
    chose to accept and proceed.
*   **When**: The human opens `ledger.md`.
*   **Then**: Round 5 has `cap` in `stop` and the open Major's id in
    `blocking`. The run decision block says `accepted`, decided by `user`, and
    its `open findings` cell lists the findings the loop showed the user when
    it asked.

### CUJ 3: Direct dispatch

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
names another, per [#118](https://github.com/google/elephant-goldfish-model/pull/118)
and `docs/harnesses.md`):

```text
<artifact dir>/review-loop-<target stem>-<YYYYMMDD-HHMMSS>/
  round-01-review.md     # review report (synthesizer-written; self-reported in direct dispatch)
  round-01-resolved.md   # egm-resolve annotated report, with finding ids
  round-02-review.md
  ...
  ledger.md              # append-only
```

If that folder already exists, the loop adds `-2`, `-3`, and so on. The loop
states the full path of the run folder when it creates it and in the Step 3
completion message, and uses that path for the whole run. It does not resolve
the artifact directory again in later rounds.

The synthesizer already writes to the report file its caller names
(`agents/synthesizer.md`, REVIEW step 4), so the loop passes
`round-NN-review.md` and the synthesizer needs no change. In direct dispatch,
the Elephant writes that file in the synthesizer's REVIEW layout, with the
self-reported line above the title.

`egm-resolve` writes `round-NN-resolved.md` and starts each finding's heading
with its id in place of `[Issue N]`, keeping the rest of today's heading:
``### [<id>] [`<ReviewerPersona>`] - Severity: <severity>``. The ids arrive in
the `FindingsList` (§2.2 step 2 already assigns them). When `ReportPath` is
set, the Step 4 message names `round-NN-resolved.md`, so the user's comments
go into the round file. Resolve also copies the round file to
`goldfish_review_report.md` when it writes it at Step 3, and again at Step 5
after marking it resolved, so that file never shows an older round. Readers of
that file see the id in place of `[Issue N]` and nothing else changes.
`egm-review`'s resolve step names that file as its fallback source of findings,
and the draft `egm-ask` design (`docs/designs/ask.md`) reads it to detect
review state. That file is the latest view; the round files are the record.

When a round has no findings, the loop does not call `egm-resolve` and writes
no `round-NN-resolved.md` for that round. This design does not change what the
loop sends to resolve.

### Data flow per round

```text
2.2 swarm ──► round-NN-review.md (synthesizer, or Elephant in direct dispatch)
     │
     ▼
consolidate (ids, not-run reviewers, clean, churn, §2.4 stop check)
     │
     ├──► ledger.md: append the round block
     ▼
2.3 egm-resolve ──► round-NN-resolved.md (copied to goldfish_review_report.md)
     │
     ▼
2.4 act on the stop result; on converged, a user answer, or a halt,
    append a run decision block to ledger.md
```

Every input to the §2.4 stop check is known before resolve runs: `clean` is
decided before the round's fixes are applied, the cap is a round count, and
churn compares a new finding with fixes applied in earlier rounds. So the loop
writes the round block before it calls `egm-resolve`, and the block survives
compaction during the Step 4 human turn. The rules are unchanged; only the
point at which their result is written down is new.

The loop is the only writer of `ledger.md`.

### Ledger format

```markdown
# Review loop ledger

**Target:** `docs/designs/foo.md`

**Run:** `review-loop-foo-20261111-140203`

**Dispatch:** synthesizer

## Round 1

| round | completed | not run | clean | blocking | stop | note |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | egm-design, egm-structural | egm-style | no | `egm-design-1-1`, `egm-structural-1-2` | continue | egm-style timed out twice |

## Round 2

| round | completed | not run | clean | blocking | stop | note |
| --- | --- | --- | --- | --- | --- | --- |
| 2 | egm-design, egm-structural, egm-style | none | yes | none | continue | |
```

A run that reaches the cap, where the user then accepts the open findings,
ends like this:

```markdown
## Run decision

| after round | outcome | decided by | open findings |
| --- | --- | --- | --- |
| 5 | accepted | user | Major: `egm-design-5-2` |
```

Rules:

*   **Round row.** One row per round, written after the Elephant consolidates
    the round's findings and before it calls `egm-resolve` (or, for a round
    with no findings, before it asks whether to run another round).
    *   `completed` and `not run` are the reviewer status from §2.2 step 3.
    *   `clean` is the §2.4 decision. If `not run` is not `none`, `clean` is
        `no`.
    *   `blocking` lists the id of each Blocker or Major finding that made the
        round not clean, or `none`. A round that is not clean only because a
        reviewer did not run has `none` here and the reviewer in `not run`.
    *   `stop` is `continue`, `converged`, `cap`, or `churn`: the result of
        the §2.4 check for that round. It is not how the run ended; the loop
        writes it before it asks the user anything.
    *   `note` is free text, used for why a reviewer did not run and, for
        churn, which finding is at the scope of which earlier fix.
    *   Ids in any cell are in backticks.
*   **Run decision block.** How the run ended goes in a one-row `Run decision`
    block, appended after the round block it follows. The loop appends one
    when the round converges (`converged`, decided by `elephant`), when the
    user answers the cap or churn question in §2.4 (`accepted`, `continued`,
    or `returned-to-drafting`, decided by `user`), and when the user declines
    another round or otherwise stops the loop (`halted`, decided by `user`).
    For a cap or churn answer, `open findings` copies the short list of open
    findings by severity that §2.4 already writes before it asks; otherwise it
    is empty. Every outcome except `continued` ends the run. A ledger whose
    last block is a round block has no recorded ending: the run was abandoned
    or the session ended.
*   **Append-only.** The loop appends each round block and each run decision
    block when it is decided, and never edits earlier blocks.

### Completion message

Step 3's summary adds the path of the run folder. The loop writes it in chat
on every ending, including before it exits back to a programmatic caller such
as `egm-review`, so the caller's own stage message does not replace it.

## Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Append-only is a written convention. The Elephant could edit an earlier block. | State it as a limit in the skill text. Earlier blocks are also checkable against the round files, which the ledger does not replace. |
| In direct dispatch the Elephant writes `round-NN-review.md`, so the record shows the decisions are consistent with what was recorded, not what reviewers said. | Mark the file and the ledger header self-reported, and state the limit in the skill text. |
| With the synthesizer, `round-NN-review.md` is the synthesizer's consolidated text, not the reviewers' raw output, so a finding it dropped or merged leaves no trace in the run folder. | State it as a limit. The trace runs from the ledger to the review report, not to raw reviewer output. |
| The ledger records which findings blocked a round, not why other findings did not (for example, a finding the Elephant judged already settled). A wrong match is not visible from the ledger. | State it as a limit. Recording matches across rounds is the re-opening work in #344. A reader can still compare each round's review report with the earlier resolve reports by hand. |
| Compaction or a session ending during resolve. Fixes may be applied with no record of the user's decisions. | The round block is written before resolve, so the clean decision, the blocking ids, and the stop result survive. Per-finding decisions are in `round-NN-resolved.md` once resolve marks it resolved at Step 5. Resuming the round is #63's scope. |
| Two runs on the same target start in the same second. | Numeric suffix on an existing folder name. |
| `egm-review` calls `egm-resolve` again at its stage checkpoint, after the loop returns. Those decisions are not in the run folder. | State it as a limit. That call is outside the loop and out of scope here. |
| #344, [#287](https://github.com/google/elephant-goldfish-model/pull/287), and #433 edit the same text (§2.4, `review.md`, `synthesizer.md`, and the `egm-resolve` report template). | Whichever lands second rebases. The changes here are additive: round file names, one ledger write per round, one per ending, and the id in each resolve finding heading. |

## Alternatives Considered

### Alternative A: Append every round to one report file

*   **Pros**: One file per run.
*   **Cons**: The synthesizer writes a whole file per call, so appending needs
    the Elephant to merge reports, which is the overwrite risk this design
    removes. One long file is harder to diff per round.
*   **Reason for Rejection**: Rejected by author: separate round files keep
    the review report apart from Elephant-written text, and need no merge
    step.

### Alternative B: Round files only, no ledger

*   **Pros**: No new file format.
*   **Cons**: The clean decision, the blocking findings, and the stop result
    are the Elephant's judgments, written in no round file. The run's ending
    is not written anywhere.
*   **Reason for Rejection**: Rejected by author: without the ledger, the run
    folder shows what reviewers said but not why the loop stopped.

### Alternative C: A per-finding ledger with cross-round matching

*   **Pros**: Records every resolve decision, links a re-raised finding to its
    first id, and lets a reader check how each finding became settled.
*   **Cons**: Needs matching rules, a status mapping for every resolve outcome,
    and a pre-resolve findings file. It overlaps the re-opening rules #344
    is changing.
*   **Reason for Rejection**: Deferred at maintainer request. An earlier
    revision of this design proposed it. It can follow once #344 settles the
    re-opening rules, building on the run folder and ledger here.

--------------------------------------------------------------------------------

## Non-Functional Requirements

*   **Security & Privacy**: Round files and the ledger can quote confidential
    target text, including in the ledger's `note` and `open findings` columns.
    They are kept until the user deletes them, like other EGM outputs.
    `docs/privacy.md` gets one line naming the run folder and saying that it
    can quote target text. When the artifact directory is inside a repository,
    users may want to ignore run folders in version control. This design does
    not change `.gitignore`.
*   **Performance & Latency**: Up to two files per round plus the ledger: 11
    at the default cap of 5 rounds, and two more for each round the user
    continues past it. Writing the ledger adds one short table per round and
    one per ending to the Elephant's output.
*   **Rollout & Rollback**: Skill text only. Standalone `egm-resolve` and
    `egm-review` keep their current file names. Rollback is a revert of the
    implementation PR.

--------------------------------------------------------------------------------

### Additional Resources

*   `skills/egm-review-loop/SKILL.md` §2.2–2.4 (since
    [#168](https://github.com/google/elephant-goldfish-model/pull/168))
*   `skills/egm-resolve/SKILL.md` Steps 3–5
*   `agents/synthesizer.md` REVIEW mode
*   `skills/egm-review/SKILL.md`, Critic Review and Implementation Readiness
    subflows
*   `docs/harnesses.md`, "Artifact Directory"
    ([#118](https://github.com/google/elephant-goldfish-model/pull/118))
*   `docs/privacy.md`
*   Related:
    [#344](https://github.com/google/elephant-goldfish-model/pull/344)
    (re-open a contested finding when its evidence no longer holds; owns
    re-opening behavior),
    [#287](https://github.com/google/elephant-goldfish-model/pull/287)
    (aligns `review.md` and `synthesizer.md` with the skills),
    [#63](https://github.com/google/elephant-goldfish-model/issues/63)
    (resume),
    [#110](https://github.com/google/elephant-goldfish-model/issues/110)
    (dedicated output folder),
    [#433](https://github.com/google/elephant-goldfish-model/issues/433)
    (evidence basis on each finding; asks whether an owner question blocks a
    clean round),
    [#448](https://github.com/google/elephant-goldfish-model/issues/448)
    (one folder per feature, which would hold the run folder)

### Future Improvements

*   **Per-finding history**: Alternative C, once #344 settles re-opening. It
    would add a row per resolve decision with a link to the finding's first
    id, and could list findings the user passed over without a decision in
    the completion message.
*   **K9 checker**: A read-only Goldfish persona that reads only the run folder
    and the target, checks the Elephant's recorded decisions against the
    round reports, and reports to the human on every exit.
*   **Resume**: #63 could later decide whether the run folder is enough state
    to resume from. This design does not assume it.

--------------------------------------------------------------------------------

## Detailed Implementation Plan

### Target Files to Create/Modify

#### 1. `skills/egm-review-loop/SKILL.md` (Modify)

*   **Type / Scope**: Skill instructions.
*   **Proposed Changes**:
    *   New "Run Record" section: run folder name, location, and collision
        suffix; file names; the ledger format (round block and run decision
        block); and the stated limits from Risks and Mitigations.
    *   §2.2: pass `round-NN-review.md` in the run folder to the synthesizer.
        In direct dispatch, the Elephant writes that file and marks it
        self-reported. After consolidating, append the round block to
        `ledger.md` before calling resolve.
    *   §2.3: pass `ReportPath` (`round-NN-resolved.md`) to `egm-resolve`.
    *   §2.4: append a run decision block on converged, on the user's answer
        at cap or churn, and on a halt.
    *   Step 3: add the run folder path to the completion summary, and write
        it for programmatic callers too, before exiting.

#### 2. `skills/egm-resolve/SKILL.md` (Modify)

*   **Type / Scope**: Skill instructions.
*   **Proposed Changes**: Optional input `ReportPath`. When it is given, write
    the annotated report there, start each finding's heading with its id in
    place of `[Issue N]`, and name it in the Step 4 message. Copy it to
    `goldfish_review_report.md` at Step 3, and again at Step 5 after marking
    it resolved. Standalone behavior is unchanged.

#### 3. `skills/egm-review-loop/test_scenarios.yaml` (Modify)

*   **Type / Scope**: Behavioral eval scenarios.
*   **Proposed Changes**: Scenarios for: round files are not overwritten
    across rounds; direct dispatch marks the round review file and the ledger
    header self-reported; the round block is written before resolve and
    records `completed`, `not run`, `clean`, `blocking`, and `stop`; a
    reviewer that did not run makes the round not clean; a round with no
    findings skips resolve and still gets a round block; each ending
    (converged, each answer at cap or churn, and a halt) appends a run
    decision block with who decided, and a cap answer copies the open
    findings; the completion message names the run folder.

#### 4. `skills/egm-review-loop/TEST.md` (Modify)

*   **Type / Scope**: Test description.
*   **Proposed Changes**: Describe the new scenarios.

#### 5. `skills/egm-resolve/test_scenarios.yaml` (Modify)

*   **Type / Scope**: Behavioral eval scenarios.
*   **Proposed Changes**: With `ReportPath`, each finding heading in the
    report starts with its id and `goldfish_review_report.md` is also
    written. Without it, behavior matches today.

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

### Verification Plan

*   **Compilation/Build**: `python3 scripts/pack_plugin.py --target claude
    --output <dir>` builds the runtime package without error. `main` no
    longer holds a generated copy to update
    ([#387](https://github.com/google/elephant-goldfish-model/issues/387)).
*   **Unit Tests**: `pytest tests/unit`, including packaging, frontmatter,
    link integrity, scenario coverage, and the 24,000-byte skill load limit
    (`skills/egm-review-loop/SKILL.md` is 10,325 bytes today; the Run Record
    section is short enough to stay inline).
*   **Static Analysis & Linting**: N/A beyond the unit checks; skill text
    only.
*   **Test Coverage Requirement**: Each new rule in the "Run Record" section
    has at least one scenario in item 3 or 5.
*   **E2E/Integration**: Run `egm-review-loop` on a sample design doc for at
    least three rounds, once with the synthesizer and once in direct
    dispatch. Check that no round file is overwritten, that every round has
    one round block written before its resolve report, that each `blocking`
    id is a heading in that round's resolve report, that the ledger ends with
    a run decision block, and that the completion message names the run
    folder.

--------------------------------------------------------------------------------

<!-- Provenance: Indicates initial structural drafting via EGM. -->

*Drafted with EGM*
