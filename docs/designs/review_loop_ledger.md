# Review Loop Run Record and Status Ledger

*   **Author:** [@mbachaud](https://github.com/mbachaud)
*   **Status:** Draft
*   **Date:** 2026-11-15

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
is churn. Moreover, `egm-resolve` pauses at Step 4 for human input across a
turn that can last hours or compact before Step 5 returns, so any pre-resolve
judgment kept only in context (`clean`, reviewer status, and `same-as` match
reasons) can be lost before the round finishes. Today none of those judgments
is written down.

Proposed solution: write each round's files under round-numbered names in one
folder per run, including a consolidated findings file written before resolve
that records finding ids, `same-as` root ids, match reasons, reviewer statuses,
and the `clean` decision. Add a ledger that records each decision as a row,
links a re-raised finding to its first id, and ends each round with a summary
row.

## Goals

*   Each round's reviewer report, consolidated findings list, and resolve
    report (when resolve runs) survive the run under round-numbered names.
    None overwrites another.
*   Every finding id can be traced to the review report it came from (written
    by the synthesizer, or self-reported in direct dispatch).
*   Every judgment the Elephant makes before `egm-resolve` yields to the user
    (`completed` and `not run` reviewers, `clean`, `same-as` root id, the
    reason for each match, and any churn judgment) is written to
    `round-NN-findings.md` before resolve starts.
*   `ledger.md` records one row per decision: finding id, `same-as` id,
    severity, status, who decided, a short reason, and cited evidence for
    contests. Rows sit under a heading for their round.
*   A finding raised again in a later round can be traced to its first id with
    one whole-cell text search (the root id with a space on each side),
    avoiding collisions such as `1-1` matching `1-10`.
*   Each round ends with one summary row: reviewer status, clean or not, the
    stop decision, and the count of findings by status. A reader can check that
    the counts add up without opening the round reports.
*   The ledger records how the run ended and who decided: converged, the
    user's answer at cap or churn, or a manual halt.
*   The completion message says how many findings closed without a fix and
    how many were left undecided, and lists the id of each undecided Blocker
    or Major finding, so "converged" cannot hide them.
*   This design does not change the convergence, cap, and churn rules in
    §2.4. It records what those rules decide and writes down which statuses
    count as settled (see Open Questions).

## Non-Goals

*   Changing the convergence, cap, or churn rules.
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
*   K9, a read-only checker persona that audits the ledger. It could be a
    follow-up once this record exists.
*   Changing `egm-resolve` when it runs on its own, outside the loop. This
    includes the second `egm-resolve` call that `egm-review` offers at its
    stage checkpoint after the loop returns (see Risks and Mitigations).

## Open Questions

1.  **Explicit rejections as settled (needs a maintainer decision):** §2.4
    settles findings that are "contested or recorded without a fix". This
    design treats an explicit per-item decision by the user as settled for
    convergence: `user-rejected` (a PROPOSE FIX item the user skipped in the
    breakdown, or declined by comment or custom instruction) and `escalated`
    (an ESCALATE item the user confirmed needs no change). Is that the
    intended reading of §2.4? The alternative is to leave both unsettled,
    which means a finding the user explicitly declined to fix blocks
    convergence every round it is raised again. Items the user never decided
    are not part of this question: a PROPOSE FIX or ESCALATE item bypassed by
    "continue", "no changes", or "auto accept" gets `passed-over` and stays
    unsettled.
    [#433](https://github.com/google/elephant-goldfish-model/issues/433) asks
    a related question: whether an owner question, which it maps to ESCALATE
    by default, counts against a clean round. Both answers decide when an
    ESCALATE item blocks convergence, so they are best decided together. If
    #433 decides that owner questions do not block, the `passed-over` rule
    for ESCALATE items here follows that decision.
2.  **Re-raised settled findings:** §2.4 says not to re-open a settled finding
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
    and 4 have `yes` in the `clean` column, matching the `**Clean:** yes`
    header in `round-03-findings.md` and `round-04-findings.md`. Every id in
    those findings files has one final-status row in its round block. Each
    summary's counts match its rows, and each id's `source` entry points to a
    heading in that round's `round-NN-review.md`. The ledger ends with a run
    decision row: after round 4, `converged`, decided by `elephant`.

### CUJ 2: Trace a re-opened finding without prefix collisions

*   **Given**: `egm-design-1-1` and `egm-design-1-10` were both raised in round
    1, and `egm-design-1-1` was fixed. In round 3, `egm-structural-3-1` raises
    the same issue at the same scope as `egm-design-1-1`.
*   **When**: The Elephant consolidates round 3's findings.
*   **Then**: `round-03-findings.md` records `same-as: egm-design-1-1` and the
    reason for the match before resolve runs. After resolve, the ledger gets a
    `re-opened` row for `egm-structural-3-1` with `same-as: egm-design-1-1`,
    decided by `elephant`, copying that match reason, followed by a second row
    recording how resolve handled it this round. Searching `ledger.md` for
    `egm-design-1-1` with a space on each side returns every row for
    `egm-design-1-1` (where it sits in `id` in round 1 and in `same-as` in
    later rounds) without matching `egm-design-1-10`, and the last matching
    row is the current status (for a split root, the last row of each split
    id).

### CUJ 3: A settled finding is raised again

*   **Given**: `egm-style-1-4` was contested in round 1 with cited evidence.
    In round 2, `egm-style-2-1` raises the same issue.
*   **When**: The Elephant consolidates round 2's findings.
*   **Then**: `round-02-findings.md` records `egm-style-2-1` with
    `same-as: egm-style-1-4` and reason "Settled in round 1; not re-opened
    (§2.4)". The finding is not sent to resolve, and it does not make the round
    unclean. After resolve finishes for the rest of the round, the ledger gets
    one row for `egm-style-2-1` with `same-as: egm-style-1-4`, status
    `contested`, decided by `elephant`, reason "Settled in round 1; not
    re-opened (§2.4)", and evidence `see same-as`.

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
names another, per [#118](https://github.com/google/elephant-goldfish-model/pull/118)
and `docs/harnesses.md`):

```text
<artifact dir>/review-loop-<target stem>-<YYYYMMDD-HHMMSS>/
  round-01-review.md     # review report (synthesizer-written; self-reported in direct dispatch)
  round-01-findings.md   # consolidated FindingsList, match reasons, and clean/reviewer state
  round-01-resolved.md   # egm-resolve annotated report, with finding ids
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
`round-NN-review.md` and the synthesizer needs no change. In direct dispatch,
the Elephant writes that file in the synthesizer's REVIEW layout, with the
self-reported line above the title.

`egm-resolve` writes `round-NN-resolved.md` and starts each finding's heading
with its id in place of `[Issue N]`, keeping the rest of today's heading:
``### [<id>] [`<ReviewerPersona>`] - Severity: <severity>``. The ids arrive in
the `FindingsList`. The report does not repeat the Reviewer Status table,
because resolve does not receive reviewer status; `round-NN-findings.md`
records it. When `ReportPath` is set, the Step 4 message names
`round-NN-resolved.md`, so the user's comments go into the round file.
Resolve also copies the round file to `goldfish_review_report.md` when it
writes it at Step 3, so that file never shows an older round as resolved
while this one waits at Step 4, and copies it again at Step 5 after marking it
resolved. Readers of that file see the id in place of `[Issue N]` and nothing
else changes.
`egm-review`'s resolve step names that file as its fallback source of findings,
and the draft `egm-ask` design (`docs/designs/ask.md`) reads it to detect
review state. That file is the latest view; the round files are the record.

### Consolidated findings file

The synthesizer's report has no ids, and the synthesizer deduplicates across
reviewers. The Elephant assigns ids, matches against earlier rounds, checks
failed reviewers, and decides `clean` when it consolidates (§2.2 steps 2–3 and
§2.4) before calling `egm-resolve`. Because `egm-resolve` idles for human input
at Step 4 across a turn that can last hours or compact, the loop writes all of
those pre-resolve results to `round-NN-findings.md` before calling resolve:

```markdown
# Round 3 Findings

**Completed:** egm-design, egm-structural, egm-style

**Not run:** none

**Clean:** no

| id | reviewer | severity | scope | source | same-as | reason |
| --- | --- | --- | --- | --- | --- | --- |
| egm-structural-3-1 | egm-structural | Major | §Goals | "Goals miss failure case" (review heading) | egm-design-1-2 | Re-opened: same gap in §Goals after the round 1 fix |
| egm-style-3-1 | egm-style | Major | §Overview | "Tone check" (review heading) | egm-style-1-4 | Settled in round 1; not re-opened (§2.4) |
| egm-design-3-1 | egm-design | Major | §Technical Plan | "Scope note ignored", "Unclear scope" (merged) | | Merged duplicate headings in round 3 |
| egm-design-3-2 | egm-design | Nit | §Overview | "Minor wording" (review heading) | | |
```

*   `Completed`, `Not run`, and `Clean` record the reviewer status and the
    pre-fix `clean` decision (§2.4) before resolve yields to the user. If a
    reviewer is in `Not run`, `Clean` is `no`.
*   `<reviewer>` in an id is the frontmatter `name` of the reviewer's persona
    file (for example `egm-design` for `agents/design_critic.md`), so it has
    no spaces or slashes even when `Reviewers` gives a path.
*   `source` names the heading or headings in `round-NN-review.md` the finding
    came from, so a reader can check the mapping against the review report.
    When the Elephant merges duplicates raised in the same round, it
    gives them one id and lists every source heading.
*   `reason` records the Elephant's pre-resolve judgment: why a finding matched
    an earlier root id in `same-as` (including whether it is re-opened or
    already settled), why an ambiguous match was treated as new, why
    headings from the same round were merged, or why a finding is churn
    (naming the applied fix that would be reverted, §2.4).
*   If #433 lands, the table gains a `basis` column copied from the
    reviewer's report (document, referenced file, or owner question). No rule
    in this design reads it, and a change of basis between rounds does not by
    itself make a finding new: matching stays on issue and scope.
*   This file is written before resolve yields to the user, so the ids,
    `same-as` links, match and churn reasons, `not run` status, and `clean`
    decision all survive compaction during resolve.

### Data flow per round

```text
2.2 swarm ──► round-NN-review.md (synthesizer, or Elephant in direct dispatch)
     │
     ▼
consolidate: merge duplicates, assign ids, match against ledger (same-as + reason),
record completed/not-run, decide clean ──► round-NN-findings.md
     │                       │
     │ new, re-opened,       │ settled re-raises: kept in round-NN-findings.md,
     │ re-raised unsettled   │ not sent to resolve
     ▼                       │
2.3 egm-resolve              │ (resolve writes round-NN-resolved.md and
     │                       │ copies it to goldfish_review_report.md at
     │                       │ Step 3 and again at Step 5)
     │ returns one decision  │
     │ per id: outcome, who  │
     │ decided, reason,      │
     │ evidence              │
     ▼                       ▼
2.4 loop combines round-NN-findings.md + resolve decisions into ledger.md
    (settled re-raises included), then decides stop/continue
```

The loop is the only writer of `ledger.md`. Resolve returns decisions and the
loop combines them with the pre-resolve state saved in `round-NN-findings.md`,
so the ledger has one author per run and does not rely on in-context memory
across the Step 4 human turn.

**Nothing to resolve.** When a round has nothing to send to resolve (no
findings, or only settled re-raises), the loop does not call `egm-resolve` and
writes no `round-NN-resolved.md` for that round. It appends the round block to
`ledger.md` right after it writes `round-NN-findings.md`, then decides stop or
continue. It still asks the user before it starts another round (§2.4).

### Matching rules for `same-as`

*   **Root id and whole-cell search.** `same-as` holds the id the finding had
    when it was first raised, never an intermediate one. It is empty for a new
    finding. In both `round-NN-findings.md` and `ledger.md`, `id` and `same-as`
    each fill a Markdown table cell, so an id always has a space on each side.
    An id written in any other cell (`scope`, `source`, `reason`, or
    `evidence`) is always in backticks (`` `egm-design-1-1` ``), so it has a
    backtick on each side and the search does not match it. Searching for the root id with a space on each side
    (`" egm-design-1-1 "`) returns the finding's first row (via `id`) and
    every later row (via `same-as`). The trailing space stops a longer `<n>`
    (`egm-design-1-10`), and the leading space stops a longer reviewer name
    that ends with this one (`x-egm-design-1-1`). This still works when a
    formatter pads cells to align columns; a search that also requires both
    pipes (`| <id> |`) does not. The last matching row in `ledger.md` is the
    current status (for a split root, the last row of each split id; see
    Splits).
*   **One root per finding.** If a finding could match two roots, match the
    one with the same affected scope. If it is still ambiguous, treat the
    finding as new and say so in the `reason` column of `round-NN-findings.md`
    (carried into the finding's ledger row; see "Pre-resolve reasons" under
    Ledger format). A new finding is not settled, so the doubt counts against
    convergence, not for it.
*   **Splits.** If a later round raises two findings that each match one
    earlier finding, both get that root as `same-as`, with their own rows.
    The root then has one current status per split id: the last row of each.
    A later finding that matches a split root is compared with the split it
    matches by scope, and its `reason` names that split id (backticked). If
    it matches no single split, the root counts as settled only when every
    split's current status is settled.
*   **Stated judgment.** The match is the Elephant's judgment. The `reason`
    column in `round-NN-findings.md` states why before resolve runs, and the
    ledger preserves that reason so a later reader or checker can dispute it.

### Ledger format

An excerpt, with the round 1 and round 2 blocks omitted:

```markdown
# Review loop ledger

**Target:** `docs/designs/foo.md`

**Run:** `review-loop-foo-20261111-140203`

**Dispatch:** synthesizer

## Round 3

| id | same-as | severity | status | decided by | reason | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| egm-structural-3-1 | egm-design-1-2 | Major | re-opened | elephant | Re-opened: same gap in §Goals after the round 1 fix | |
| egm-structural-3-1 | egm-design-1-2 | Major | fixed | user | Accepted proposed fix | |
| egm-style-3-1 | egm-style-1-4 | Major | contested | elephant | Settled in round 1; not re-opened (§2.4) | see same-as |
| egm-design-3-1 | | Major | contested | elephant | Reviewer missed the scope note | `skills/egm-review-loop/SKILL.md` §2.4 |
| egm-design-3-2 | | Nit | accepted-risk | elephant | Nit declined | |

| round | completed | not run | clean | stop | findings | fixed | contested | accepted-risk | escalated | user-rejected | passed-over | re-opened |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | egm-design, egm-structural, egm-style | none | no | continue | 4 | 1 | 2 | 1 | 0 | 0 | 0 | 1 |
```

Round 3 is not clean: `egm-structural-3-1` is a re-opened Major, and
`egm-design-3-1` is a new Major that was not settled when the clean decision
was made, before resolve. The re-raised `egm-style-3-1` does not block, because
it was already settled.

A run that reaches the cap, where the user then accepts the open findings,
ends like this:

```markdown
## Run decision

| after round | outcome | decided by |
| --- | --- | --- |
| 5 | accepted | user |
```

Rules:

*   **Final status.** Each id in `round-NN-findings.md` gets exactly one row
    with a final status: `fixed`, `contested`, `accepted-risk`, `escalated`,
    `user-rejected`, or `passed-over`. A re-opened finding also gets one
    `re-opened` row before its final row, using the match `reason` recorded in
    `round-NN-findings.md`. `decided by` is `user`, `elephant`, or `none`
    (`passed-over` only). A decision taken from a comment on the resolve
    report says so in `reason` (`from comment: ...`).
*   **Pre-resolve reasons.** A match or churn reason recorded in
    `round-NN-findings.md` always reaches the ledger. A `re-opened` row or a
    re-raised settled row carries it as its `reason`. For any other finding
    with one (an ambiguous match treated as new, a re-raised `passed-over`
    finding, or churn), the final row's `reason` starts with that reason,
    followed by resolve's reason. Merge reasons stay in the findings file,
    next to the `source` headings.
*   **Summary row.** `completed`, `not run`, and `clean` are copied from the
    header of `round-NN-findings.md`. `findings` is the number of rows in
    `round-NN-findings.md`. `fixed + contested + accepted-risk + escalated +
    user-rejected + passed-over` must equal `findings`. `re-opened` is counted
    separately. `stop` is `continue`, `converged`, `cap`, or `churn`. It is
    the result of the loop's §2.4 check for that round, not how the run
    ended: the loop writes it before it asks the user anything. For
    churn, the reason column of the affected rows names the fix that would be
    reverted, as recorded in `round-NN-findings.md` before resolve.
*   **Run decision row.** How the run ended goes in a one-row `Run decision`
    block, appended after the round block it follows. The loop appends one
    when the round converges (`converged`, decided by `elephant`), when the
    user answers the cap or churn question in §2.4 (`accepted`,
    `continued`, or `returned-to-drafting`, decided by `user`), and when the
    user declines another round or otherwise stops the loop (`halted`,
    decided by `user`). Every outcome except `continued` ends the run. A
    halt cannot go in `stop`, because the round block is already appended
    when the user answers. A ledger whose last block is a round block has no
    recorded ending: the run was abandoned or the session ended.
*   **Evidence.** A `contested` row records the evidence the contest cited (a
    file and symbol, or a decision in the document).
    [#344](https://github.com/google/elephant-goldfish-model/pull/344) needs
    that evidence
    to survive compaction. A re-raised settled row writes `see same-as` in
    `evidence` (since its `same-as` cell already holds the root id). This
    column is the Elephant's contest evidence, not the reviewer's evidence
    basis that #433 proposes. Whether a re-raised contest's evidence still
    holds is #344's rule. Until #344 lands, a re-raised `contested` finding is
    carried forward without that check; its `evidence` cell lets a reader
    check it by hand. Once #344 lands, a re-raised contested finding whose
    evidence no longer holds gets a `re-opened` row with #344's reason, then
    its new final status, like a re-raised fixed finding.
*   **Append-only.** The loop appends one round block after resolve returns
    (or after the findings file is written, when there is nothing to resolve),
    appends each run decision block when that decision is made, and never
    edits earlier blocks.

### Mapping resolve outcomes to statuses

| Resolve outcome | Status | Decided by | Settled |
| --- | --- | --- | --- |
| PROPOSE FIX, applied (auto accept, accepted in breakdown, or custom instruction) | `fixed` | `user` | no |
| PROPOSE FIX, skipped in the breakdown, or declined by comment or custom instruction | `user-rejected` | `user` | yes (pending Open Question 1) |
| PROPOSE FIX, no per-item decision ("continue / no changes", or a comment or custom instruction that does not address it) | `passed-over` | `none` | no |
| CONTEST, kept | `contested` | `elephant` | yes |
| CONTEST, overruled and fixed | `fixed` | `user` | no |
| ESCALATE, user confirmed no change (breakdown, comment, or custom instruction) | `escalated` | `user` | yes (pending Open Question 1) |
| ESCALATE, fact added to the document | `fixed` | `user` | no |
| ESCALATE, no per-item decision (auto accept, "continue / no changes", or a comment or custom instruction that does not address it) | `passed-over` | `none` | no |
| DECLINE (Nit recorded without a fix) | `accepted-risk` | `elephant` | yes |
| Re-raised settled finding (§2.4 match) | prior settled status | `elephant` | yes |
| Re-raised fixed finding (§2.4 match) | `re-opened`, then its new final status | `elephant`, then per row above | per final status |
| Re-raised unsettled, never-fixed finding (§2.4 match): `passed-over`, and `user-rejected` or `escalated` if Open Question 1 is answered no | its new final status, with `same-as` set and no `re-opened` row | per row above | per final status |

**Settled depends on the status alone.** `contested` and `accepted-risk` are
settled, and so are `user-rejected` and `escalated` if Open Question 1 is
answered yes. `fixed` and `passed-over` are never settled. `decided by` adds
detail and never changes whether a row is settled.

**Why `passed-over` is a separate status.** In `egm-resolve` Step 4, "continue"
and "no changes" skip the resolution phase as a whole, and "auto accept"
bypasses every ESCALATE item. Only the interactive breakdown, or a comment or
custom instruction that names the item, gives a per-item decision. An item
with no decision gets `passed-over`, decided by `none`, whether its category
was PROPOSE FIX or ESCALATE (the category stays in `round-NN-resolved.md`).
So a user cannot converge the loop with nothing fixed by typing "continue"
each round, and `user-rejected` and `escalated` always mean an explicit
decision. A re-raised `passed-over` finding goes to resolve again with the new
and re-opened findings, and a Blocker or Major one makes the round not clean.
It gets no `re-opened` row, because no fix was applied.

**Default rule.** Some outcomes have no row above, for example a custom
instruction that touches a CONTEST item. For these, if the target text changed
for the finding, record `fixed` by `user`. If not, and the user stated a
decision on that finding, record `user-rejected` for PROPOSE FIX or
`escalated` by `user` for ESCALATE. If the user stated no decision on that
finding, whatever reply ended Step 4, record `passed-over` by `none` for
PROPOSE FIX or ESCALATE, `contested` for CONTEST, and `accepted-risk` for
DECLINE. Resolve does not exit while a breakdown item is still under
"Discuss", so that case does not reach the ledger.

If the Elephant no longer knows a decision the user made in Step 4 (for
example, context compacted during the breakdown), it records `fixed` by `user`
if the target has the proposed edit from `round-NN-resolved.md` or another
edit at the finding's scope, and otherwise `passed-over` by `none` with the
reason "decision not recorded". This applies to PROPOSE FIX, ESCALATE, and
CONTEST items alike, so a lost overrule is never recorded as `contested`.
DECLINE items are not in the breakdown and keep `accepted-risk`. A lost
decision therefore never settles a finding, and the finding blocks again if it
is raised again.

### Completion message

Step 3's summary adds the run folder path and two counts: findings closed
without a fix (`user-rejected`, `escalated`, `contested`, `accepted-risk`) and
findings left undecided (`passed-over`). Each finding is counted once, by its
current status: the last row for its root id, or the last row of each split id
when a root was split. The summary also lists the id and severity of each
`passed-over` Blocker or Major finding, on every ending and not only at cap or
churn. `passed-over` Nits are counted and not listed. §2.4 writes a list of
open findings only at cap or churn, so without this a converged run would give
a count and no id to open.

The loop writes these lines in chat on every ending, including before it exits
back to a programmatic caller such as `egm-review`, so the caller's own stage
message does not replace them.

## Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Append-only is a written convention. The Elephant could edit an earlier block. | State it as a limit in the skill text. Earlier blocks are also checkable against the round files, which the ledger does not replace. A K9 checker could verify this later. |
| In direct dispatch the Elephant writes `round-NN-review.md`, so the record shows the decisions are consistent with what was recorded, not what reviewers said. | Mark the file and the ledger header self-reported, and state the limit in the skill text. |
| With the synthesizer, `round-NN-review.md` is the synthesizer's consolidated text, not the reviewers' raw output, so a finding it dropped or merged leaves no trace in the run folder. | State it as a limit. The trace runs from the ledger to the review report, not to raw reviewer output. Keeping raw outputs is a possible follow-up. |
| The Elephant makes a wrong `same-as` match. | Every match has a stated reason written to `round-NN-findings.md` before resolve and copied to the ledger, and ambiguous matches are treated as new (unsettled). A human can dispute a match from the ledger alone. |
| Compaction or a session ending during resolve. Fixes may be applied with no ledger block for that round. | `round-NN-findings.md` is written before resolve with `Completed`, `Not run`, `Clean`, `same-as`, and `reason`, so all pre-resolve judgments survive. A round with a findings file and no ledger block has no recorded resolve decisions. The skill tells the reader to compare the target against that round's resolve report. Resuming the round is #63's scope. Decisions made during the interactive breakdown are held in context until the breakdown ends (`egm-resolve` Step 4). If they are lost, the lost-decision rule records them as `fixed` or `passed-over`, never as settled, including a lost overrule of a contest. |
| Typing "continue" at Step 4 each round could let the loop converge with nothing fixed. | Items with no per-item decision get `passed-over`, which is never settled, so a re-raised Blocker or Major still makes the round not clean. A `passed-over` finding that no later reviewer raises again does not block; the completion message counts it as undecided and, for a Blocker or Major, lists its id. Explicit `user-rejected` findings are counted in every summary row and in the completion message; whether they count as settled is Open Question 1. |
| Collisions when searching for an id (`egm-design-1-1` matching `egm-design-1-10` or `x-egm-design-1-1`). | Every `id` and `same-as` value fills a table cell and has a space on each side, so searching for the root id with a space on each side matches only that id, however the table is padded and however many findings a round has. Ids in free-text cells are backticked, so a reason that names an id does not match either. |
| A later fix removes a contest's evidence, and the finding stays settled. | #344 re-checks contest evidence. Until then this is stated as a limit, and the `evidence` column makes it checkable. |
| Two runs on the same target start in the same second. | Numeric suffix on an existing folder name. |
| `egm-review` calls `egm-resolve` again at its stage checkpoint, after the loop returns. Those decisions are not in the ledger. | State it as a limit. That call is outside the loop and out of scope here. |
| #344, [#287](https://github.com/google/elephant-goldfish-model/pull/287), and #433 edit the same text (§2.4, `review.md`, `synthesizer.md`, and the `egm-resolve` report template). | Whichever lands second rebases. The ledger's evidence field is designed to fit #344's rule, the doc changes here are additive to #287's, and the only change to the resolve report template here is the id in each finding heading. |

## Alternatives Considered

### Alternative A: Append every round to one report file

*   **Pros**: One file per run.
*   **Cons**: The synthesizer writes a whole file per call, so appending needs
    the Elephant to merge reports, which is the overwrite risk this design
    removes. One long file is harder to diff per round.
*   **Reason for Rejection**: Rejected by author: separate round files keep
    the review report apart from Elephant-written text, and need no merge
    step.

### Alternative B: A mutable ledger with one row per finding

*   **Pros**: The current status is always in one place.
*   **Cons**: Each update erases the earlier decision.
*   **Reason for Rejection**: Rejected by author: it loses the decision history
    a check after compaction needs. With `same-as` on the root id, the
    current status is still one whole-cell search (the root id with a space
    on each side) away in the append-only form.

### Alternative C: `same-as` points to the previous id

*   **Pros**: Records the exact link the Elephant matched.
*   **Cons**: Finding the history needs one search per hop.
*   **Reason for Rejection**: Rejected by author: the root id finds the latest
    row in one search (the latest row of each split id, for a split root),
    and the reason column still records which earlier finding was matched.

### Alternative D: Round facts only in each round report

*   **Pros**: No summary rows in the ledger.
*   **Cons**: Checking the counts means opening every round report.
*   **Reason for Rejection**: Rejected by author: the summary row costs one
    line per round and lets a reader check the counts from the ledger alone.

### Alternative E: Fixed-width zero-padding on `<n>` instead of whole-cell search

*   **Pros**: A bare substring search for `egm-design-1-01` does not match
    `egm-design-1-10`, for up to 99 findings per reviewer in a round.
*   **Cons**: Changes the existing `<reviewer>-<round>-<n>` id format in
    `skills/egm-review-loop/SKILL.md` §2.2, and collides again past 99
    findings unless `<n>` is padded wider.
*   **Reason for Rejection**: Rejected by author: every `id` and `same-as`
    already fills its own table cell, so searching for the id with a space on
    each side avoids collisions at any count without changing §2.2's id
    format.

--------------------------------------------------------------------------------

## Non-Functional Requirements

*   **Security & Privacy**: Round files and the ledger can quote confidential
    target text, including in the findings file's `reason` column and the
    ledger's `reason` and `evidence` columns. They are kept until the user
    deletes them, like other EGM outputs. `docs/privacy.md` gets one line
    naming the run folder and saying that it can quote target text. When the
    artifact directory is inside a repository, users may want to ignore run
    folders in version control. This design does not change `.gitignore`.
*   **Performance & Latency**: Up to three files per round plus the ledger:
    16 at the default cap of 5 rounds, and three more for each round the
    user continues past it. Writing the findings file and the ledger block
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
    (dedicated output folder),
    [#433](https://github.com/google/elephant-goldfish-model/issues/433)
    (evidence basis on each finding; edits the resolve report template and
    asks whether an owner question blocks a clean round),
    [#448](https://github.com/google/elephant-goldfish-model/issues/448)
    (one folder per feature, which would hold the run folder),
    [#408](https://github.com/google/elephant-goldfish-model/issues/408)
    (give reviewers recorded decisions; the ledger's settled rows are one
    such record)

### Future Improvements

*   **K9 checker**: A read-only Goldfish persona that reads only the run folder
    and the target, checks the Elephant's recorded decisions against the
    round review reports, and reports to the human on every exit.
*   **Resume**: #63 could later decide whether the run folder is enough state
    to resume from. This design does not assume it.

--------------------------------------------------------------------------------

## Detailed Implementation Plan

### Target Files to Create/Modify

#### 1. `skills/egm-review-loop/SKILL.md` (Modify)

*   **Type / Scope**: Skill instructions.
*   **Proposed Changes**:
    *   New "Run Record" section: run folder name, location, and collision
        suffix; file names; findings-file format (`Completed`, `Not run`,
        `Clean` header plus `reason` column) and ledger format; matching rules
        with whole-cell search (the id with a space on each side); summary row;
        status mapping (including `passed-over` for items with no per-item
        decision) with the default rule; and the stated limits from Risks and
        Mitigations. If the section would push `SKILL.md` past the size target
        in [#369](https://github.com/google/elephant-goldfish-model/pull/369),
        the formats, matching rules, and mapping table move to
        `skills/egm-review-loop/references/run_record.md`, linked from the
        section, and `SKILL.md` keeps only the steps that use them.
    *   §2.2: pass `round-NN-review.md` in the run folder to the synthesizer.
        In direct dispatch, the Elephant writes that file and marks it
        self-reported. When consolidating, merge duplicates, assign ids, match
        against the ledger with stated reasons, decide `clean`, reviewer
        status, and churn, and write `round-NN-findings.md` before calling
        resolve. Leave re-raised settled findings out of the `FindingsList`,
        and keep re-raised unsettled findings (such as `passed-over`) in it.
        When nothing is left to send, skip resolve and append the round block.
    *   §2.3: pass `ReportPath` (`round-NN-resolved.md`) to `egm-resolve`.
    *   §2.4: list the settled statuses. After resolve returns, combine
        `round-NN-findings.md` with resolve's decisions to append the round
        block to `ledger.md`, then decide stop or continue. Append a run
        decision block on converged, on the user's answer at cap or churn,
        and on a halt.
    *   Step 3: add the run folder path, the count of findings closed without
        a fix, the count left undecided, and the id and severity of each
        `passed-over` Blocker or Major finding to the completion summary, and
        write them for programmatic callers too, before exiting.

#### 2. `skills/egm-resolve/SKILL.md` (Modify)

*   **Type / Scope**: Skill instructions.
*   **Proposed Changes**: Optional input `ReportPath`. When it is given, write
    the annotated report there, start each finding's heading with its id in
    place of `[Issue N]`, and name it in the Step 4 message. Copy it to
    `goldfish_review_report.md` at Step 3, and again at Step 5 after marking
    it resolved. The Step 5 handoff
    returns, for each finding id, the outcome (distinguishing an explicit
    per-item decision from no decision), who decided, a short reason, and
    cited evidence for contests. Standalone behavior is unchanged.

#### 3. `skills/egm-review-loop/test_scenarios.yaml` (Modify)

*   **Type / Scope**: Behavioral eval scenarios.
*   **Proposed Changes**: Scenarios for: `round-NN-findings.md` records
    `Completed`, `Not run`, `Clean`, `same-as`, and `reason` before resolve; a
    re-opened finding gets a `same-as` row with the root id and match reason; a
    settled re-raise is recorded and not sent to resolve; an ambiguous match is
    treated as new; a reason that names a candidate root does not match the
    search for that root; a Step 4 decision lost to compaction is recorded
    as undecided; "continue / no changes" records `passed-over` (unsettled)
    for PROPOSE FIX and ESCALATE items; a custom instruction that names only
    some items leaves the rest `passed-over`; a re-raised `passed-over`
    finding goes to resolve with no `re-opened` row; a pre-resolve reason
    reaches the ledger row; the summary counts add up to the rows in the
    findings file; direct dispatch marks the round review file self-reported;
    round files are not overwritten; a round with nothing to resolve skips
    resolve and still gets a ledger block; each ending (converged, each
    answer at cap or churn, and a halt) appends a run decision row with who
    decided; the completion message names the run folder and both counts,
    and lists the id of a `passed-over` Major on a converged run.

#### 4. `skills/egm-review-loop/TEST.md` (Modify)

*   **Type / Scope**: Test description.
*   **Proposed Changes**: Describe the new scenarios.

#### 5. `skills/egm-resolve/test_scenarios.yaml` (Modify)

*   **Type / Scope**: Behavioral eval scenarios.
*   **Proposed Changes**: With `ReportPath`, each finding heading in the
    report starts with its id, `goldfish_review_report.md` is also written,
    and the handoff returns a decision per id distinguishing an explicit
    per-item decision from no decision. Without it, behavior matches today.

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

#### 11. `skills/egm-review-loop/references/run_record.md` (Create, only if needed)

*   **Type / Scope**: Skill reference.
*   **Proposed Changes**: Created only if the "Run Record" section would push
    `SKILL.md` past the size target in #369 (see item 1). It then holds the
    formats, matching rules, and mapping table, and `SKILL.md` links to it.

### Verification Plan

*   **Compilation/Build**: `python3 scripts/pack_plugin.py --target claude
    --output <dir>` builds the runtime package without error. `main` no
    longer holds a generated copy to update
    ([#387](https://github.com/google/elephant-goldfish-model/issues/387)).
*   **Unit Tests**: `pytest tests/unit`, including packaging, frontmatter,
    link integrity, scenario coverage, and the 24,000-byte skill load limit
    (`skills/egm-review-loop/SKILL.md` is 10,325 bytes today).
*   **Static Analysis & Linting**: N/A beyond the unit checks; skill text
    only.
*   **Test Coverage Requirement**: Each new rule in the "Run Record" section
    (or in `references/run_record.md`, if the rules move there) has at least
    one scenario in item 3 or 5.
*   **E2E/Integration**: Run `egm-review-loop` on a sample design doc for at
    least three rounds, once with the synthesizer and once in direct
    dispatch. Check that no round file is overwritten, that every id in each
    findings file has one final row, that each summary's counts match its
    rows, that the ledger ends with a run decision row, and that the
    completion message names the run folder.

--------------------------------------------------------------------------------

<!-- Provenance: Indicates initial structural drafting via EGM. -->

*Drafted with EGM*
