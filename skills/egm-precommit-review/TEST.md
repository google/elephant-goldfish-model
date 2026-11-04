# Precommit review verification

## Offline

Run `python -m pytest tests/unit`. Packaging checks include the evidence protocol,
new skill metadata and the read-only Claude adapter. Fixture tests establish
that the index really contains a defect masked by the working copy, and that
the fix fixture starts with a failing test. Native trace negative controls
reject missing, failed or unrelated reads, writes and incomplete handbacks.

## Native Claude

With an authenticated CLI, run:

```sh
EGM_CLAUDE_LIVE=1 python -m pytest tests/integration/test_claude_precommit.py -v
EGM_CLAUDE_LIVE=1 python -m pytest tests/integration/test_claude.py -k precommit -v
```

The full workflow builds a uniquely named candidate via `--plugin-dir` and uses
disposable Git repositories. Review mode has an index defect whose working
copy is corrected and a defective untracked file with a Unicode/space name.
Fix mode has an unstaged calculation defect and failing unittest. It must
produce findings, preserve the child report, fix only source, run passing checks
and obtain a second review from a fresh child. HEAD and index must not change.

Inspect native launches, registered type, completed reads and returned reports.
The focused isolation probe asks the child to report visible parent/project
markers; the denied-read probe must stop without a verdict. Marker absence in
ordinary workflow transcripts is only a visible-record check, not proof that
hidden host context is absent. These tests consume authenticated model usage.

## Behavioral cases and limits

For a focused installed Codex review, run
`EGM_CODEX_LIVE=1 python -m pytest tests/integration/test_codex_precommit.py -v`.
This uses a temporary marketplace and checks native fresh dispatch, completion,
required reads and the staged/untracked findings. It does not exercise Codex
fix mode. Encrypted dispatch inputs and host instruction exclusion remain
unverified. Empty patches need a successful literal read even though they emit
no content; a failed read must not count as an empty patch.

The adjacent scenario file covers conflicts, invalid bases, unsupported files,
stale evidence, validation limits, rebuttals, cap and missing reads. Its static
validation does not execute these branches. Record which cases actually ran.
The workflow is a prompt protocol, not a Git lock or a mechanical approval gate.
Do not claim universal code-review accuracy or support for every host from a
fixture pass. Keep raw account-bearing native traces private; publish sanitized
results and versions in the PR description.
