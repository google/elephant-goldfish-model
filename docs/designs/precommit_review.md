# Independent precommit review

**Author:** [Vlad Shvedov](https://github.com/vshvedov)

**Status:** Draft. Maintainer scope alignment and design approval are pending.
Scope inquiry: #295. Proposed implementation: #293.

## Problem Statement

Before committing, a developer needs an independent review of the changes
that will actually be committed. A fix in the working copy can hide a defect
in the Git index, and an untracked source file may contain a defect absent
from both diffs. An agent that receives the implementer's explanation can
also inherit the assumptions that led to the defect.

The proposed skill adapts fresh review, explicit triage and a bounded fix loop
from [ClaudeFlows cf-precommit-review](https://github.com/OmniPragmatic/claudeflows/blob/60d180dc6f89d7ffa1166e19ed4a6054a994aff2/plugins/claudeflows/skills/cf-precommit-review/SKILL.md)
and the earlier [elephant-goldfish implementation](https://github.com/vshvedov/elephant-goldfish).

## Goals

- Review pending changes, including separate staged and working-copy versions
  and non-ignored untracked files. An explicit base can add committed changes.
- Give a fresh reviewer the source evidence without the implementation history.
- Preserve findings and evidence-backed rebuttals across rounds. Make fixes
  optional and verify them in the changed version.
- Distinguish review coverage, validation and the final outcome.

## Non-Goals

- Stage, unstage, commit, push, create a PR or install a Git hook.
- Review remote PRs or infer a base branch. The default is pending changes.
- Let the reviewer run tests or write files, or certify future changes.
- Hide findings or call incomplete coverage clean.

## Proposed Architecture

The Elephant resolves the Git scope, captures evidence for each change layer
and runs authorized checks. A fresh Goldfish reads that evidence and relevant
source, then returns citations and findings. The Elephant maintains the ledger
and writes the result. In explicit fix mode it can correct a finding on disk
and send fresh evidence to a new reviewer. The same chain handles all hosts
that support the required dispatch.

The skill reuses EGM's artifact conventions, fresh dispatch and bounded review
loop pattern. The existing `egm-review-loop` reviews a document and resolves
document findings. It does not bind findings or test results to different Git
versions. This skill's code reviewer must cite the layer it read, and a single
complete recheck can verify a fix against captured evidence. The existing
design and codebase personas evaluate a design against the repository. The
new persona reviews changes and returns coverage for every supplied layer.

## Interface and Outcomes

`egm-precommit-review` takes an optional `RepoRoot`, `BaseRef`, `Focus` and
`Mode`. It defaults to the current repository, pending changes and review only.
`BaseRef` adds committed changes from the pinned merge base. `Focus` directs
attention while keeping the full inventory in scope. The repository needs a
HEAD commit, a readable index and a unique merge base when requested.

Review status and validation status are separate. Validation records passing,
failing, incomplete or inapplicable checks with their tested versions. Choose
the first matching outcome below, retaining findings and validation limits.

| Condition | Outcome |
| :--- | :--- |
| Evidence changed during review | `stale` |
| Required coverage, reads or reviewer completion are missing | `incomplete` |
| Initial scope is empty and no fixes need verification | `no changes` |
| Fix mode reached five rounds with open findings or unresolved validation | `stopped at limit` |
| A finding remains open, including a staged defect fixed only on disk | `findings remain` |
| Required validation failed or is incomplete | `incomplete` |
| Review and validation are complete and only upheld rebuttals remain | `completed with rebuttals` |
| Full coverage, valid checks, no new findings and all fixes verified | `clean` |

## Alternatives Considered

- **Extend the document review loop.** It could share dispatch and triage, but
  changing its document-based evidence contract would also affect existing
  callers. Start with a separate skill and reuse the workflow conventions.
- **Review the working tree alone.** This is simpler but can miss the staged
  permission defect covered by the test fixture.
- **Automatically fix and stage everything.** That changes the proposed
  commit and risks staging unrelated work. Fix mode changes the working copy
  only and reports when the user needs to stage a correction.

## Risks and Mitigations

- **Cross-round leakage.** Supply the current evidence only, plus specific
  fixes and rebuttals in later rounds. Exclude prior generated artifacts while
  retaining tracked changes and unrelated untracked directories.
- **Evidence drift.** Compare captured bytes and versions before dispatch and
  after return. Record gaps in surrounding-source reads. The checks detect
  observed differences without locking Git.
- **Wrong layer.** Test the index in a separate materialization when it differs
  from the working copy. Keep an untested staged version explicit.
- **Host context.** Claude uses `omitClaudeMd` and read-only tools. Codex can
  exclude parent turns, but instruction-file exclusion remains unverified.
- **Untrusted source.** Treat code and patches as evidence. Record binary,
  symlink, submodule and unreadable entries as coverage gaps.

## Detailed Implementation Plan

1. **Capture evidence in the parent.** Implement the workflow as skill
   instructions and local Git/file calls, with the exact procedure in
   `skills/egm-precommit-review/references/evidence.md`. Pin HEAD and the
   optional unique merge base. Use NUL-delimited
   `git status --porcelain=v1 -z --untracked-files=all`,
   `git ls-files --stage -z` and
   `git ls-files --others --exclude-standard -z`. Save separate branch,
   staged and unstaged diffs with external drivers and text conversion off.
   Read exact index blobs and separate working-copy bytes. Preserve full
   untracked file evidence.
2. **Store round evidence.** Use a fresh `egm-precommit-<id>/round-N/` under
   the host artifact directory. `scope.md` records the complete in-scope
   inventory as readable text, with losslessly escaped paths, layers,
   exclusions, versions and SHA-256 hashes of patches and mapped file copies.
   Keep raw NUL-delimited captures parent-side outside the round directory.
   `checks.md` records the SHA-256 of the saved scope file, tested layer,
   command, source, exit status and result. Compare the actual evidence on
   recollection. Exclude untracked files under the current run or a prior
   direct child with an `egm-precommit-*` name and generated layout
   (`round-N/scope.md` or both the final report and ledger). Inspect file
   types without following links. Keep tracked entries and lookalike source.
3. **Dispatch the reviewer and validate the return.** Use
   `agents/precommit_reviewer.md` and pass the current scope, checks, three
   patches and mapped file copies. The child returns status, coverage, added
   context reads, numbered findings with layer/path/line/impact/fix, previous
   finding dispositions and validation limits. Save its verbatim response as
   `review.md`. Only a complete review with zero findings ends in
   `no findings`. In Claude Code 2.1.271 or later use the registered
   `egm:egm-precommit-reviewer` adapter. In Codex use fresh dispatch with
   `fork_context: false` or `fork_turns: "none"`. Stop on Cursor, Copilot CLI
   and OpenCode. For other hosts, use a fresh read-only agent with the persona
   when supported, or stop. See [the harness guide](../harnesses.md).
4. **Triage and recheck.** Record stable IDs, original citations and dispositions
   in `ledger.md`. Review mode stops after one round. Fix mode applies only
   authorized changes on disk. Stop and request staging when a defect remains
   in the index. Otherwise rerun affected checks and verify fixes with a fresh
   child, including when the fix removes the entire diff. Stop on incomplete
   review, unresolved validation failure, a repeated ineffective fix or the
   fifth round. Write `precommit_report.md` with separate review, validation
   and outcome fields.
5. **Register and verify the runtime.** Package the skill, persona and Claude
   adapter, regenerate the Claude distribution, align README/site listings
   and update instructional skill counts. Unit tests check packaging and
   scenario structure before any opt-in live calls.

### Target files

| Action | Repository path |
| :--- | :--- |
| Create | `.claude-plugin/agents/precommit_reviewer.md` |
| Modify | `.claude-plugin/plugin.json` |
| Modify | `README.md` |
| Create | `agents/precommit_reviewer.md` |
| Create | `distributions/claude/.claude-plugin/agents/precommit_reviewer.md` |
| Modify | `distributions/claude/.claude-plugin/plugin.json` |
| Modify | `distributions/claude/README.md` |
| Create | `distributions/claude/agents/precommit_reviewer.md` |
| Create | `distributions/claude/skills/egm-precommit-review/SKILL.md` |
| Create | `distributions/claude/skills/egm-precommit-review/agents/openai.yaml` |
| Create | `distributions/claude/skills/egm-precommit-review/assets/icon.svg` |
| Create | `distributions/claude/skills/egm-precommit-review/references/evidence.md` |
| Modify | `docs/cursor.md` |
| Modify | `docs/opencode.md` |
| Modify | `scripts/pack_plugin.py` |
| Modify | `site/src/components/SkillIcon.astro` |
| Modify | `site/src/components/Skills.astro` |
| Create | `skills/egm-precommit-review/SKILL.md` |
| Create | `skills/egm-precommit-review/TEST.md` |
| Create | `skills/egm-precommit-review/agents/openai.yaml` |
| Create | `skills/egm-precommit-review/assets/icon.svg` |
| Create | `skills/egm-precommit-review/references/evidence.md` |
| Create | `skills/egm-precommit-review/test_scenarios.yaml` |
| Create | `tests/integration/precommit_fixture.py` |
| Create | `tests/integration/precommit_trace.py` |
| Modify | `tests/integration/test_claude.py` |
| Create | `tests/integration/test_claude_precommit.py` |
| Create | `tests/integration/test_codex_precommit.py` |
| Modify | `tests/unit/test_harnesses.py` |
| Modify | `tests/unit/test_opencode_adapter.py` |
| Modify | `tests/unit/test_packaging.py` |
| Create | `tests/unit/test_precommit_fixture.py` |
| Create | `tests/unit/test_precommit_scenarios.py` |
| Create | `tests/unit/test_precommit_traces.py` |

### Verification

- `python -m pytest tests/unit` checks manifests, resources, scenario structure,
  fixture defects, package freshness and trace validation. Negative tests
  reject missing reads, invalid completions and write operations by reviewers.
- `EGM_CLAUDE_LIVE=1 pytest tests/integration/test_claude_precommit.py` covers
  review and fix mode. Review mode must find a staged permission bug hidden
  by the working copy and a separate untracked bug. Its trace must include
  similarly named untracked source and exclude an old review marker. Fix mode
  must run checks and verify the correction with a new child. Both preserve
  the real HEAD and index.
- `EGM_CODEX_LIVE=1 pytest tests/integration/test_codex_precommit.py` checks the
  focused review fixture. Run native tests only with the corresponding
  authenticated CLI and opt-in flag. Report encrypted dispatch inputs as
  unaudited and record any skipped probes. The scenario YAML also covers
  stale evidence, invalid bases, missing coverage, rebuttals and the round cap.
