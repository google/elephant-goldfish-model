# Independent precommit review

**Author:** [Vlad Shvedov](https://github.com/vshvedov)

**Status:** Draft. Maintainer scope alignment and design approval are pending.
Scope inquiry: #295. Proposed implementation: #293.

## Problem and prior implementation

EGM reviews documents and implementation drift, but does not have a workflow
for independently reviewing pending code changes before a commit. A reviewer
that receives the implementer's explanation can miss the same assumptions.

This proposal adapts the fresh-review, explicit-triage, and bounded-loop steps
from [ClaudeFlows cf-precommit-review](https://github.com/OmniPragmatic/claudeflows/blob/60d180dc6f89d7ffa1166e19ed4a6054a994aff2/plugins/claudeflows/skills/cf-precommit-review/SKILL.md),
following the earlier [elephant-goldfish implementation](https://github.com/vshvedov/elephant-goldfish).
It uses EGM's existing fresh-context dispatch and artifact conventions. It does
not claim to originate the Elephant/Goldfish pattern.

## Goals

- Review staged, unstaged, and non-ignored untracked changes, including staged
  contents that differ from the working copy.
- Give a fresh reviewer source evidence without the implementation narrative.
- Preserve every finding and its disposition across fresh review rounds.
- Optionally fix findings in the parent context, then recheck the actual changes.
- Distinguish clean code review from incomplete evidence or failing validation.

## Non-goals

- Stage, unstage, commit, push, create a PR, or install a Git hook.
- Review remote PRs or assume a branch named main.
- Run application code in the reviewer or change files from a child agent.
- Automatically accept risks, weaken tests, or discard the user's working tree.
- Prove absence of bugs or filesystem isolation.

## Interface

`egm-precommit-review` takes `RepoRoot` (default current repository), optional
`BaseRef` (default HEAD), optional `Focus`, and `Mode` (`review` by default or
`fix` when explicitly requested). Focus emphasizes areas; it never silently
narrows the change inventory. The repository must have a HEAD commit.

Without BaseRef, review pending changes only. With BaseRef, resolve it to a
commit and pin its merge base with HEAD once, adding committed branch changes
to the scope. Fail on invalid or ambiguous merge bases, unmerged index entries,
or unreadable evidence. Never invent a base or treat failed Git commands as
empty changes. Support detached HEAD. Git is local; do not fetch.

## Evidence and artifacts

Use the host guide's artifact directory and a new `egm-precommit-<unique-id>/`
run directory. Never overwrite an earlier run. Exclude untracked artifacts from
the current run and prior EGM precommit run directories directly under that
artifact directory. Identify prior runs by their `egm-precommit-*/` directory
name and generated layout, such as `round-N/scope.md` or the final report and
ledger. Check paths and file types without reading report contents or following
symlinks. List the excluded directories in `scope.md`. Keep tracked changes
and all other untracked files in scope, including lookalike source directories.
Reject a run path overlapping an existing source path or traversing symlinks.

Before each round, the parent saves a numbered round directory containing:

- `scope.md`: repository, HEAD, resolved base, status, paths and change layers,
  exclusions and unreadable/unsupported evidence, plus applicable project rules.
- `branch.patch`, `staged.patch`, `unstaged.patch`: separate, complete diffs
  with external diff drivers and text conversion disabled.
- `files/`: numbered copies of changed text files, including distinct index
  and working-copy versions, mapped to repository paths and line numbers in
  scope.md. Deleted files use the old-side diff; binary files, submodules and
  symlinks are recorded as coverage gaps, never followed or silently dropped.
  Any such gap makes the result `incomplete`, even if other files were reviewed.
- `checks.md`: actual commands, source of each check, tested layer and evidence
  hash, exit status and result.
- `review.md`: the unedited completed child response.

Use NUL-delimited Git inventories that list untracked files individually.
Quote paths safely and never evaluate filenames as shell code. Read full diff
output or save it directly to files. Truncated tool output is incomplete
evidence. Record SHA-256 of each patch and file copy, plus current
HEAD/index/worktree evidence. Recollect and compare that evidence before
dispatch and after the child returns. If source changes, retain the report as
stale and stop without a clean outcome. This detects observed changes between
checks. Git can still change during either check.

The reviewer may read surrounding source and tests. Record any unavailable
context as a limitation. Reviews and validation concern the recorded state;
they do not attest future edits. Do not feed previous full reports, conversation
history, private reasoning, or implementation plans to the first reviewer.

`ledger.md` records stable finding IDs, original citations, evidence and status:
open, fixed (awaiting recheck), verified fixed, or rebutted with a verbatim reason.
`precommit_report.md` gives final scope, checks, coverage, rounds, findings and
remaining limits. Retain all artifacts, including failures.

## Dispatch and loop

Use one fresh `agents/precommit_reviewer.md` per round. In Claude, register
`egm-precommit-reviewer` with Read/Grep/Glob, `omitClaudeMd`, no memory or shell,
and spawn it under the installed plugin namespace, normally
`egm:egm-precommit-reviewer`. In Codex, set `fork_context: false` or
`fork_turns: "none"`, whichever the schema exposes. If fresh dispatch is
unavailable, stop.

The child reads its persona, all scope/patch/check artifacts, and required file
copies before returning a structured completion status and numbered substantive
findings with layer, path, line, impact and suggested correction. Only a complete
review with zero findings may end with `no findings`. Missing or truncated
evidence, failed dispatch and absent reports are incomplete, never clean.

Review mode runs one round and reports findings without changing project files.
Fix mode lets the parent apply authorized fixes without touching the index or
Git history. A staged defect remains open if only its working copy is fixed;
the report must say staging is still needed, not certify the staged version.
Do not repeatedly retry that fix. Test expectation changes require evidence
from the review and a justified behavior change, not merely a desire for green.

After a fix, run affected checks and dispatch a new reviewer with fresh evidence,
the previous fix list, and exact rebuttals. A fixed finding is only verified
after recheck. Include previously affected paths even when a fix removes the
entire diff; initial no-changes handling must not skip this verification round.
A rebuttal needs code or a documented requirement as evidence;
a later reviewer can reopen it with new evidence. Never hide rebuttals or treat
accepted risk as a clean review. No automatic same-line churn detection; require
the same substantive issue to recur after an attempted fix.

Checks must name their tested layer. Normal local checks validate the working
copy only. If staged changes exist and the proposed index tree differs from the
working copy, report `validation incomplete` unless its applicable checks also
ran in an isolated materialization of that tree. Do not infer index or
intermediate branch-commit test success from working-copy success.
Intermediate commits get code review, not an individual test attestation. If
index materialization needs unavailable dependencies or unsafe setup, leave it
untested and report the limitation.

Stop on a complete clean round with passing applicable checks for the working
copy and any distinct staged candidate, and every earlier
finding verified fixed. If there are only upheld rebuttals, report
`completed with rebuttals`, not clean. Stop at five rounds, repeated ineffective
fix, failed validation that cannot be resolved within scope, or incomplete review.
Report open findings and ask whether to continue, leave them, or stop. Never
automatically commit or roll back regardless of the answer.

## Validation

Detect project checks from manifests, CI and project rules. Run applicable local
checks separately, recording passed/failed/not run/not applicable. Existing
authorization applies; network, destructive or external-system checks need
their normal permissions. Missing tools or unrun required checks prevent a
clean outcome. Pre-existing failures need baseline evidence; compare in a
separate checkout without stashing, cleaning or resetting the user's files.

Offline tests cover metadata, packaging, read-only adapter restrictions and
native evidence validators. Native Claude fixtures cover: (1) a staged defect
whose working copy is fixed, plus an untracked defect; (2) an unstaged defect
fixed by the parent and re-reviewed by a distinct child. Verify actual reads,
child completion, no parent marker leakage in visible records, unchanged index
and HEAD, appropriate findings, and incomplete validation of an untested index.
In the first fixture, verify that prior review artifacts are excluded while
an untracked source directory with a similar name remains in scope.
Run active isolation and denied-read probes.
Run a focused Codex workflow where available. Codex native dispatch payloads
can be encrypted, so the probe cannot audit those child inputs. State that
limit in the results.

The repository uses pytest for offline checks and opt-in native harness tests.
Regenerate the Claude distribution and validate both runtime packages. Add the
skill to the README and website with matching descriptions and order, and
update current skill counts in the integration guides. Behavioral scenarios
cover missing base, conflicts, unsupported files, stale evidence, rebuttals and
the round cap. Scenario assertions must prohibit a clean outcome for
unsupported changed entries. Separate live runs verify model behavior for the
scenarios they exercise.

## Initial host scope

Claude and Codex are the initial native targets. Cursor, Copilot CLI and
OpenCode do not register the precommit reviewer, so the skill stops on those
hosts. Other hosts with a fresh-context subagent tool can spawn a general-purpose
agent that reads `agents/precommit_reviewer.md` first, as described in
[the harness guide](../harnesses.md). A host without that capability stops.
