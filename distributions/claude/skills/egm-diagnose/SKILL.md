---
name: egm-diagnose
license: Apache-2.0
disable-model-invocation: true
description: >-
  Diagnoses an existing bug with a fresh Goldfish that receives observations
  but not the Elephant's suspected cause. Compares independent diagnoses,
  records evidence and falsifying checks, and produces a diagnosis report.
  Use before fixing a reproducible failure; does not change application code.
---

# Independent Bug Diagnosis

When running in Codex or ChatGPT Work, first read [Codex integration](../../docs/codex.md).
In Claude Code or Cowork, read `${CLAUDE_PLUGIN_ROOT}/docs/claude.md` first.
For other hosts, read [Harnesses](../../docs/harnesses.md) and verify that a
fresh, read-only subagent can be dispatched before proceeding.

The Elephant investigates with the conversation's context. A separate Goldfish
investigates from observations without the Elephant's explanation. Compare
their evidence before choosing what to test next. Agreement alone does not
prove the cause.

## Inputs

- **Symptom**: Actual behavior and expected behavior.
- **Repro**: Reproduction steps, a failing test, or a concrete failure trace.
- **SourceRoot**: Repository to inspect, defaulting to the working directory.
- **Evidence** (optional): Relevant logs, environment facts, or observed stack
  locations. Separate observations from interpretations in this material.

Resolve plugin resources against the installed plugin root, not SourceRoot.
Write artifacts under the host's EGM artifact directory, or the working
directory when none is configured. Create a new `egm-diagnosis-<unique-id>/`
directory for each invocation. Never overwrite an earlier run.

## 1. Prepare observations and a separate hypothesis

If no concrete reproduction or failure trace is available, ask for the missing
evidence and stop before dispatch. Do not invent a reproduction. An intermittent
failure trace is usable evidence, but mark its repeatability as unknown unless
measured. Diagnosis can remain inconclusive.

Before creating the run directory, inspect path metadata in SourceRoot, the
working directory, and the configured artifact directory for earlier
`egm-diagnosis-*/` runs. Include nested, hidden, and ignored paths. Use a
metadata-only walk (for example, `find` without following symlinks). Do not
open old artifacts. Check link targets by path and treat links to prior
artifacts as exposure too. A verified absent artifact directory is empty
for this check. If you cannot inspect the roots, report that the boundary
could not be checked and stop before creating a run directory.

If earlier run artifacts are present, dispatch only if the host can enforce
their exclusion from the child's file reads and searches, including through
aliases. A read-only tool list or an instruction to skip a path does not
enforce that exclusion. Otherwise report an incomplete diagnosis in chat.
Do not create a new run directory or dispatch a child. Tell the user which
artifact locations need to be outside the child's readable workspace.
Leave the old runs untouched.

Inspect the relevant source and fix the Elephant's initial hypothesis in the
parent conversation before dispatch. Include the candidate cause, source
evidence, uncertainty, and a check that would disprove it. Use `unknown` if
there is not enough evidence. Keep this entry unchanged for comparison.
Do not write the entry to a file, scratchpad, or other shared storage while
the Goldfish could still be running. Do not copy it into a child task.

Write `observations.md` with the symptom, expected behavior, reproduction steps,
actual results, environment facts, and narrowly selected evidence excerpts.
Mark each result as user-reported or observed in this run. Include source paths
when they appear in observed traces, not just because they fit a theory.

Build observations by selecting facts, not by copying the full problem doc,
issue, conversation, or logs. Omit proposed causes, suggested fixes, verdicts,
and links to discussions containing them. Save needed evidence as excerpts in
`observations.md` instead of passing unfiltered external files or URLs.
Do not include diagnostic hints in the run directory name.

Record the inspected revision and whether the tree has edits, if available.
Keep interpretations of those edits and attempted fixes in the parent context.
If an attempted fix is already present, say so in the final report: the source
can reveal the hypothesis even when the dispatch prompt does not. Do not reset,
stash, or undo the user's changes to manufacture an independent baseline.

## 2. Dispatch one fresh diagnosis Goldfish

Read `agents/bug_diagnosis.md` and resolve its absolute path. In Claude use the
registered `egm-bug-diagnosis` adapter under the installed plugin namespace
(normally `egm:egm-bug-diagnosis`). In Codex use a general-purpose agent
with `fork_context: false` or `fork_turns: "none"`, as supported by the actual
tool schema. Never resume an earlier agent or forward parent turns. On other
hosts use the equivalent fresh-context, read-only dispatch, or stop and report
that the host cannot perform this diagnosis. Cursor, Copilot CLI and OpenCode
don't register an `egm-bug-diagnosis` agent yet, so stop there.

Recheck for earlier run artifacts immediately before dispatch. Do not
dispatch if another run is active in the same readable workspace and its
artifacts cannot be excluded. The new run's observations are the only
diagnostic artifact the child should receive.

Give the Goldfish only the following task, replacing the paths:

```text
Read <absolute plugin path>/agents/bug_diagnosis.md and follow it.
SourceRoot: <absolute source root>
Observations: <absolute run directory>/observations.md
ExcludedArtifacts: all egm-diagnosis-*/ directories, except the supplied observations.md

Investigate the observed failure independently. Read only the supplied persona,
observations, and relevant source, tests, manifests, and architecture docs under
SourceRoot. Apply the artifact exclusion to reads, globs, and grep. If you
cannot exclude those directories from a search, narrow its scope or skip it.
Do not read diagnostic reports, issue discussions, conversation logs, memory,
or hypothesis files. Do not invoke another skill, spawn agents, run application
code or tests, or modify files. If there is no native read tool, use shell only
for read-only file inspection. Return your diagnosis to the parent; the parent
writes the report.
```

Do not add the suspected module, root cause, proposed patch, or a request to
confirm the Elephant's diagnosis to this task. The Goldfish discovers relevant
source from the observations. Project instructions and accessible files can
still contain hypotheses; fresh conversation context is not filesystem
isolation. Use host read restrictions when available. Record any known context
leak as a limitation rather than claiming an independent result.

Wait for actual completion. A launch, empty response, denied persona read,
timeout, or unhandled tool failure is not a completed diagnosis. Save an
incomplete report explaining what is missing; do not substitute the Elephant's
own reasoning and call it a Goldfish result. Do not retry silently.
On timeout or uncertain child state, keep the hypothesis off disk unless the
host confirms the child has stopped. Record that the comparison was skipped.

## 3. Preserve and check the result

After confirmed child completion, write the unchanged parent-context entry to
`elephant_hypothesis.md`. Do this before interpreting the returned candidates.
If the original entry was lost, record it as unavailable instead of reconstructing
it from the Goldfish's answer.

Write only the child's report text verbatim to `goldfish_diagnosis.md`.
Keep host metadata and any parent annotations in `diagnosis_report.md`.
The child report must contain:

- Completion status: `complete` or `incomplete`, with any access limitations.
- The files actually read and whether the persona and observations were read.
- Zero to three ranked candidate causes, each with file and line evidence,
  an explanation connecting it to the symptom, and a falsifying check.
- Missing evidence, competing explanations, and suggested diagnostic checks.

Zero candidates is valid when the evidence is insufficient. A completed
investigation may be inconclusive. An assertion without a source citation and
falsifying check is not a supported candidate. Check the cited source yourself.
Use native tool records to verify reads and completion where available; label
read claims as self-reported when those records are unavailable. Do not claim
verified isolation from a child's assurance alone.
If the child received earlier run contents, or a new accessible run appeared
while it was active and exclusion cannot be verified, record incomplete
execution and skip the comparison.

## 4. Compare evidence and write the handoff

Only now compare the Goldfish's candidates with the preserved parent hypothesis:

- **Converged**: Both identify the same mechanism. Identify a diagnostic check
  that distinguishes it from the strongest alternative; agreement is not proof.
- **Diverged**: Read the contrary evidence. Record which hypothesis changed and
  why, or retain both with a discriminating check. Do not ask a second Goldfish
  to agree with the Elephant and discard the first result.
- **Inconclusive**: Either side lacks a supported candidate to compare, including
  a completed Goldfish with zero candidates while the Elephant has a hypothesis.
  Preserve the completed execution status and record what evidence would resolve
  the uncertainty.
- **Not compared**: The Goldfish did not complete, its report is invalid
  (for example, missing status or read accounting), or the initial hypothesis
  entry could not be preserved. Record the
  execution or report-validation failure and the next recovery step. A valid
  complete report with no supported candidates is inconclusive, not failed.

The Elephant may run an existing, authorized local reproduction or diagnostic
test under the host's normal permissions. Do not edit application code, tests,
configuration, or design docs during this skill. Do not run destructive or
external-system experiments without the user's authorization. Mark proposed
checks as not run; never turn an expected outcome into a reported observation.
For intermittent failures, record attempts and observed failures instead of
treating a single pass as disproof.

Write `diagnosis_report.md` with these sections:

1. **Observed failure**: Expected/actual behavior, repro, revision and changes.
2. **Execution**: Completion status, actual read evidence, isolation limitations.
3. **Independent candidates**: Link to the unchanged Goldfish report.
4. **Comparison**: Link to the original Elephant hypothesis, outcome, and the
   evidence for accepting, rejecting, or retaining each candidate.
5. **Verification**: Checks run and their actual results, separately from checks
   proposed but not run. Distinguish a supported hypothesis from a demonstrated
   cause; do not declare a cause confirmed from agreement alone.
6. **Next step**: A discriminating experiment or regression-test specification
   tied to the failure, ready for a later fix task. No patch or automatic handoff.

Return a short summary and a link to `diagnosis_report.md`. State whether the
diagnosis completed and whether the cause remains unverified. Stop here.
