# Independent bug diagnosis

**Author:** [Vlad Shvedov](https://github.com/vshvedov)

**Status:** Draft proposal. Maintainer scope alignment and design approval are
pending. Scope inquiry: [#294](https://github.com/google/elephant-goldfish-model/issues/294).
The implementation remains in draft [#292](https://github.com/google/elephant-goldfish-model/pull/292).

## Problem

EGM gives design documents independent reviewers. An existing code failure
needs a different input: observations that do not already tell the reviewer
what to believe. Asking "check my diagnosis" can anchor a reviewer to the same
wrong explanation as the Elephant, even with a fresh conversation context.

The proposed `egm-diagnose` skill adds independent investigation before a fix.
The Elephant records its own hypothesis. A fresh Goldfish receives only the
observed failure and reproduction evidence, investigates the source, and returns
candidate causes with supporting evidence and checks that could disprove them.
The Elephant then compares the two results and records unresolved disagreement.

## Prior implementation

This proposal adapts the independent diagnosis step from Vlad Shvedov's
[ClaudeFlows `cf-bug` workflow](https://github.com/OmniPragmatic/claudeflows/blob/60d180dc6f89d7ffa1166e19ed4a6054a994aff2/plugins/claudeflows/skills/cf-bug/SKILL.md#step-2-goldfish-diagnosis-check-parallel-to-your-hypothesis).
It follows the earlier [elephant-goldfish implementation](https://github.com/vshvedov/elephant-goldfish).
In that workflow, the Goldfish receives the symptom and reproduction but not
the Elephant's hypothesized root cause. It ranks candidate causes and identifies
supporting and falsifying evidence. The Elephant compares the result with its
own hypothesis before writing a failing test and implementing the fix.

The contribution to EGM is this diagnostic information boundary and comparison
step. EGM already provides the underlying Elephant/Goldfish model and isolated
reviewers. This is not a claim to have originated those ideas or a measured
claim that independent diagnosis improves bug-fix success rates.

The proposed EGM implementation uses separate artifacts, a read-only persona,
Claude's native tool restrictions, explicit incomplete outcomes, and behavioral
evaluation cases. It stops before implementing a fix so it can be used with
the developer's existing fix and review workflow.

## Goals

- Diagnose an existing failure from a symptom and concrete reproduction or
  failure trace, without requiring a feature design document.
- Keep the Elephant's initial hypothesis out of the Goldfish's supplied input.
- Require source evidence and a possible disproof for every candidate cause.
- Preserve the original hypothesis and the independent result for comparison.
- Distinguish convergence, disagreement, uncertainty, and failed execution.
- Produce a diagnostic experiment or regression-test specification as a handoff.

## Non-goals

- Automatically fix the bug, edit tests, commit changes, or run a review loop.
- Replace EGM's design review personas or its convergence rules.
- Add a general agent orchestration engine, automatic routing, or resume state.
- Promise filesystem isolation, exclusion of host instructions on every harness,
  or a correct diagnosis merely because two agents agree.
- Add native adapters for every experimental harness in the first implementation.

## Interface and workflow

Invoke `egm-diagnose` with a symptom, expected behavior, reproduction steps or
failure trace, optional evidence, and a source root (default: working directory).
The skill remains explicitly invoked, consistent with existing EGM skills.
Existing host rules determine plugin resource paths and the artifact directory.

1. **Intake:** Ask for missing concrete evidence before dispatch. Accept an
   intermittent trace without claiming that it was reproduced. Do not create a
   design doc for the application bug.
2. **Prepare:** Create a unique run directory. Write observations separately from
   the Elephant's hypothesis. Distinguish user-reported and newly observed facts.
   Record the revision and relevant existing edits when available.
3. **Diagnose:** Launch one fresh, read-only Goldfish with the persona,
   observations, source root, and explicit artifact exclusions. It reads source
   and returns a report. It does not execute experiments or propose a patch.
4. **Validate:** Wait for completion, retain the original report, inspect cited
   evidence, and check native read records where exposed. Label self-reported
   reads when native records are absent.
5. **Compare:** Compare the independent candidates with the previously recorded
   hypothesis. Preserve disagreement and the evidence for changing either view.
6. **Handoff:** Write the consolidated report. Separate experiments actually run
   from proposed ones. Leave implementation to a later task.

The Elephant may execute an authorized existing local reproduction under normal
host permissions. New test code, application edits, and destructive or external
experiments are outside this skill's automatic scope.

## Information boundary

| Input | Elephant | Goldfish |
| :---- | :------- | :------- |
| Conversation and original bug discussion | Available | Not supplied |
| Sanitized symptom, repro and observed evidence | Available | Supplied |
| Relevant source and existing tests | Available | Read-only inspection |
| Initial hypothesis and suggested fix | Recorded separately | Excluded |
| Independent diagnosis | Read after completion | Produced independently |

The parent extracts observations rather than forwarding an entire issue or
problem document. A stack frame is an observation; a suspected module is an
interpretation unless supported by an observed trace. The source root stays
broad enough for the Goldfish to discover a different cause.

Only `observations.md` from the run directory is supplied. Broad searches of
artifact folders, conversation history, previous reports, and memory are
prohibited. A contaminated input returns an incomplete diagnosis. Fresh context
does not hide accessible files or host-injected instructions. Claude's adapter
uses `omitClaudeMd: true` and read-only tools. Codex uses a fresh context with
the isolation limitations documented in its existing integration guide.

An attempted fix already in the working tree can disclose a theory through the
source itself. Record that limitation; never revert the user's work for this
skill. Neither prompt instructions nor a report's claim of independence count
as proof of isolation. Native launch and read records are preferred evidence.

## Artifacts and outcomes

Each invocation creates a new `egm-diagnosis-<unique-id>/` directory containing:

- `observations.md`: Facts supplied to the Goldfish, with their provenance.
- `elephant-hypothesis.md`: Initial hypothesis, preserved after dispatch.
- `goldfish-diagnosis.md`: Original returned report, unchanged when available.
- `diagnosis_report.md`: Execution status, candidate comparison, verification
  evidence, limitations, and the next discriminating check or test specification.

The Goldfish reports completion separately from certainty. A complete
investigation can return no supported candidates. Each supported candidate
needs a source location, causal explanation, and a concrete falsifying check.
Missing files, denied reads, contaminated input, and timeouts yield an incomplete
outcome. Do not interpret an empty or failed response as agreement.

Comparison is `converged`, `diverged`, `inconclusive`, or `not compared`.
Convergence records the common mechanism without treating agreement as proof.
Divergence requires evidence, not a vote or repeated requests for agreement.
If either side lacks a supported candidate, comparison is inconclusive, even
when the other side has a supported hypothesis. A completed Goldfish with zero
candidates remains complete. A failed Goldfish or invalid report is not compared.
For flaky failures, record attempts and failures; one passing run is insufficient.

## Alternatives

**Reuse a design critic with the full problem doc:** Less implementation work,
but supplies the suspected cause and loses the intended information boundary.
Design-critique rubrics also do not require falsifiable causal explanations.

**Port the whole `cf-bug` pipeline:** Adds test authoring, implementation, review,
and routing choices to the first contribution. Keeping diagnosis separate lets
maintainers evaluate its usefulness without adopting another delivery workflow.

**Always run several diagnosis agents:** Could reveal more alternatives, but
increases cost before the value of even one independent diagnosis is measured.
Start with one and measure disagreements and useful falsifications.

## Detailed Implementation Plan

1. Add `skills/egm-diagnose/SKILL.md`, host UI metadata, and a skill icon.
2. Add `agents/bug_diagnosis.md` and a native read-only Claude adapter. Register
   the adapter and require the skill/persona in both runtime packages.
3. Add the skill to the README and website with matching descriptions and order.
   Update current skill counts in the integration guides while retaining their
   resource resolution, permissions, and fresh-context dispatch instructions.
4. Add co-located evaluation scenarios and a test guide covering convergence,
   divergence, missing evidence, failure, contamination, and repeat runs.
5. Add a small deterministic fixture with a misleading expiration hypothesis
   and an actual cache-key collision. Check that the reproduction and a
   discriminating experiment establish the intended fixture behavior offline.
6. Add opt-in native Codex and Claude tests to inspect dispatch arguments,
   child reads, completion, parent-hypothesis exclusion, and preserved source.
   Check both the private label and the actual hypothesis in readable inputs.
   Claude additionally checks omission of a project-instruction marker and
   read-only child tools. Report encrypted Codex dispatch text as unaudited.
   Package checks alone do not establish model behavior or native isolation.

## Validation and rollout

Run `pytest tests/unit` for package integrity, adapter restrictions, links,
scenario structure, and fixture behavior. Build both distributable archives.
Run the focused native diagnosis test to exercise the complete skill on the
fixture. Retain actual launch/read evidence, candidate reports, and limitations.
Other behavioral scenarios require separate native runs; a passing fixture does
not establish general diagnostic quality or support on every harness.

Follow the feature contribution track: scope inquiry, approved design PR, then
implementation PR. The local prototype permits review before publication; its
existence is not maintainer approval. Measure the rate of distinct supported
causes and useful falsifying checks before claiming an improvement in outcomes.

## Initial host scope

Claude and Codex are the initial native targets. Cursor, Copilot CLI and
OpenCode do not register the diagnosis persona, so the skill stops on those
hosts instead of attempting a general-purpose fallback.
