# Independent bug diagnosis

**Author:** [Vlad Shvedov](https://github.com/vshvedov)

**Status:** Draft. Maintainer scope alignment and design approval are pending.
Scope inquiry: #294. Proposed implementation: #292.

## Problem Statement

A developer investigating a bug may ask a reviewer to check a suspected cause.
That framing can bias even a reviewer with fresh context. EGM already uses an
Elephant, the agent with the conversation context, and fresh Goldfish reviewers
for designs. A bug needs a different input and output: observed failure in,
candidate causes with source evidence and checks that could disprove them out.

This proposal adapts the independent investigation and evidence comparison
from [ClaudeFlows cf-bug](https://github.com/OmniPragmatic/claudeflows/blob/60d180dc6f89d7ffa1166e19ed4a6054a994aff2/plugins/claudeflows/skills/cf-bug/SKILL.md)
and the earlier [elephant-goldfish implementation](https://github.com/vshvedov/elephant-goldfish).
Its benefit to bug-fix outcomes remains unmeasured.

## Goals

- Start from a symptom, expected behavior and a concrete reproduction or trace.
- Keep the Elephant's initial hypothesis in its conversation until the Goldfish
  has stopped. Send only observations and the source location.
- Keep earlier runs out of the Goldfish's reads and searches. Stop before
  dispatch if earlier artifacts are reachable and cannot be excluded.
- Return up to three candidate causes with citations and falsifying checks.
- Preserve both accounts and leave a discriminating check for the developer.

## Non-Goals

- Edit code, write tests, commit changes or automate the subsequent fix.
- Add diagnosis adapters for Cursor, Copilot CLI or OpenCode in this release.
- Promise filesystem isolation, guaranteed correctness or a measured benefit.

## Proposed Architecture

The Elephant prepares a narrow observation file, holds its own hypothesis in
the parent conversation and dispatches one Goldfish. The Goldfish reads the
observation file and relevant source, then returns its report. The Elephant
saves the original hypothesis and report after the child stops. It compares
their evidence and writes a handoff.

Claude registers the `egm-bug-diagnosis` adapter with Read, Grep, Glob and
`omitClaudeMd` (Claude Code 2.1.271 or later). Use the installed plugin
namespace, normally `egm:egm-bug-diagnosis`. Codex uses a fresh
general-purpose child with parent turns excluded and a read-only task.
Fresh context can still include project instructions such as `AGENTS.md`.
The skill stops on Cursor, Copilot CLI and OpenCode, which do not register
this persona. On other hosts, use a fresh, read-only general-purpose agent
that reads `agents/bug_diagnosis.md` first, as described in the
[harness guide](../harnesses.md). Stop if the host cannot dispatch that agent.

## Interface and Outcomes

Invoke `egm-diagnose` with a symptom, expected behavior, steps or trace,
optional evidence and a source root (default working directory). Missing
concrete evidence stops dispatch. An intermittent trace can be used without
claiming that the failure was reproduced.

Each supported candidate includes a source location, a causal explanation and
a check with an outcome that would rule it out. The Goldfish reports completion
separately from certainty. It can complete with zero supported candidates.

| Comparison | Condition |
| :--- | :--- |
| `converged` | Both accounts support the same mechanism. Agreement still needs a check. |
| `diverged` | Both support different mechanisms. Preserve the disagreement and suggest a discriminating check. |
| `inconclusive` | The Goldfish completed and one or both accounts lack a supported candidate. |
| `not compared` | Execution is incomplete, the Goldfish report is invalid, or the original hypothesis was lost. |

The Elephant may run authorized existing local checks for any candidate.
Distinguish observations from suggested checks. For intermittent failures,
record attempts and failures. One passing attempt is insufficient to disprove
an intermittent failure.

## Risks and Mitigations

- **Hypothesis exposure.** The current hypothesis never enters a file while
  the Goldfish might still be active. The dispatch excludes it, and the
  observations omit attempted-fix details. Check for earlier artifacts
  before dispatch. A read-only tool list does not keep those files out of a
  search. Stop if the host cannot enforce an exclusion for reachable runs.
  Existing source edits and host instructions can still expose theories.
  Record known exposure.
- **Untrusted evidence.** Select small excerpts, omit secrets and proposed
  fixes, and treat excerpts as data. Contaminated observations produce an
  incomplete result.
- **Unsupported conclusions.** Check source citations and keep experiments
  actually run separate from proposed tests. Report unavailable read records as
  self-reported evidence.
- **Timeout or lost context.** Leave the hypothesis off disk if the host cannot
  confirm the child stopped. If the original hypothesis is lost, report it
  unavailable rather than reconstructing it from the child result.

## Alternatives Considered

- **Reuse a design critic with sanitized observations.** It could take the same
  unbiased input. The diagnosis persona adds a causal explanation and a
  falsifying check as required outputs.
- **Port the full bug-fix workflow.** That would combine diagnosis with test
  creation and implementation. A separate step works with existing fix flows.
- **Use a second reviewer or a filesystem snapshot.** These can improve
  independence in some cases but increase cost and setup. Start with one
  reviewer and keep the current hypothesis out of the shared files.

## Detailed Implementation Plan

1. **Add the skill and reviewer.** The skill defines explicit invocation and
   resolves the host integration guide. Inspect path metadata in the source,
   working and artifact directories for earlier `egm-diagnosis-*/` runs,
   including nested, hidden and ignored paths. Leave earlier runs untouched.
   If the host cannot enforce exclusion for reachable earlier runs, stop and
   list the full paths of the run directories that block the retry. The
   developer moves each whole directory, including its reports and hypotheses,
   to a location the child cannot read and removes any links that still make
   it reachable from the source, working or artifact directory. With the
   default working-directory artifact location, a repeat run remains blocked
   until the earlier runs are moved out of reach or the host enforces exclusion.
   Otherwise create a fresh `egm-diagnosis-<unique-id>/` directory under the
   host's artifact directory. Write `observations.md` with observed and
   user-reported facts separated. Form the initial hypothesis before dispatch
   and retain it only in the Elephant conversation. Record revision and
   whether the tree has edits.
2. **Dispatch and preserve evidence.** Invoke the registered Claude adapter
   or use Codex's `fork_context: false` or `fork_turns: "none"` as exposed by
   the host. Recheck for earlier runs before dispatch. Pass the persona,
   source root and observations. Exclude every diagnosis run directory from
   reads and searches except for the supplied observations file. Stop if
   earlier artifacts would be readable or the boundary cannot be checked.
   The child returns status, files read, zero to three ranked candidates,
   missing evidence and suggested checks. On confirmed child
   completion, save the original hypothesis to `elephant_hypothesis.md`
   and the verbatim return to `goldfish_diagnosis.md`. For an incomplete run,
   retain only artifacts that can be saved without exposing the hypothesis
   to a live child. Write `diagnosis_report.md` with status, comparison,
   verified observations and the next check. Skip comparison if earlier
   contents reached the child or a new run became readable during review and
   its exclusion cannot be verified.
3. **Register and package.** Add the adapter to the manifest, require the
   persona and skill in both archives, and regenerate the Claude distribution.
   Align the README and website entries. Update instructional skill counts in
   OpenCode and Cursor. Preserve dated verification notes.
4. **Verify.** Run the unit suite, then the opt-in native fixtures. A passing
   fixture verifies its boundary and outcome; it supplies no measure of
   overall diagnosis quality.

### Target files

| Action | Repository path |
| :--- | :--- |
| Create | `.claude-plugin/agents/bug_diagnosis.md` |
| Modify | `.claude-plugin/plugin.json` |
| Modify | `README.md` |
| Create | `agents/bug_diagnosis.md` |
| Create | `distributions/claude/.claude-plugin/agents/bug_diagnosis.md` |
| Modify | `distributions/claude/.claude-plugin/plugin.json` |
| Modify | `distributions/claude/README.md` |
| Create | `distributions/claude/agents/bug_diagnosis.md` |
| Create | `distributions/claude/skills/egm-diagnose/SKILL.md` |
| Create | `distributions/claude/skills/egm-diagnose/agents/openai.yaml` |
| Create | `distributions/claude/skills/egm-diagnose/assets/icon.svg` |
| Modify | `docs/cursor.md` |
| Modify | `docs/designs/skill_icons.md` |
| Modify | `docs/opencode.md` |
| Modify | `scripts/pack_plugin.py` |
| Modify | `site/src/components/SkillIcon.astro` |
| Modify | `site/src/components/Skills.astro` |
| Create | `skills/egm-diagnose/SKILL.md` |
| Create | `skills/egm-diagnose/TEST.md` |
| Create | `skills/egm-diagnose/agents/openai.yaml` |
| Create | `skills/egm-diagnose/assets/icon.svg` |
| Create | `skills/egm-diagnose/test_scenarios.yaml` |
| Create | `tests/fixtures/diagnosis/catalog.py` |
| Create | `tests/integration/diagnosis_checks.py` |
| Modify | `tests/integration/test_claude.py` |
| Create | `tests/integration/test_claude_diagnosis.py` |
| Modify | `tests/integration/test_codex.py` |
| Modify | `tests/unit/test_codex_traces.py` |
| Create | `tests/unit/test_diagnosis_claude_traces.py` |
| Create | `tests/unit/test_diagnosis_fixture.py` |
| Create | `tests/unit/test_diagnosis_inputs.py` |
| Create | `tests/unit/test_diagnosis_scenarios.py` |
| Modify | `tests/unit/test_harnesses.py` |
| Modify | `tests/unit/test_opencode_adapter.py` |
| Modify | `tests/unit/test_packaging.py` |

### Verification

- `python -m pytest tests/unit` checks packaging, adapters, scenario structure
  and the cache-key fixture. The fixture returns the wrong tenant's value
  when two tenants share a slug. Negative trace cases reject early writes,
  leaked inputs, denied reads and missing returns.
- Build each runtime with `scripts/pack_plugin.py` using the `claude` and
  `openai` targets. Unit tests compare the checked-in Claude distribution
  with fresh packaging.
- `EGM_CLAUDE_LIVE=1 pytest tests/integration/test_claude_diagnosis.py` checks
  a fresh read-only dispatch, source citations, unchanged source and the
  independent result. With the output directory inside the source root,
  require the first hypothesis write to follow the native child return.
  With an earlier run under an ignored source directory and no enforced
  exclusion, require incomplete execution without launching a child or
  opening the earlier hypothesis. The result names the blocking directory.
- `EGM_CODEX_LIVE=1 pytest tests/integration/test_codex.py -k independent_bug_diagnosis`
  checks the analogous fixture on Codex. Record encrypted dispatch input as
  unaudited. Retain version, launch, reads, completion and the output artifacts.
