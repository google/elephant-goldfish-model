# Metadata triage prototype

Tracking: [#328](https://github.com/google/elephant-goldfish-model/issues/328).
The template signals and topical label taxonomy follow the contributor prototype
in [#334](https://github.com/google/elephant-goldfish-model/pull/334).
This branch adds Gemini classification and deterministic PR labels for evaluation.
It does not replace that contribution or grant approval to ship it.

## Behavior

- New issues receive a preview of a native Bug, Feature, or Task type and existing
  topical labels. Gemini makes one tool-free JSON request; recognized template
  headings take precedence for the type. Ambiguous classifications stay unset.
- PRs receive path-based area-label previews on opening and new commits. Neither
  Gemini nor PR code runs for PR classification, including fork PRs.
- Writes are disabled by default. When enabled, existing types and labels remain;
  labels previously removed are not restored. Workflow retries skip all work.
  Changed or closed issues and changed PR heads are skipped before publication.
- Approval labels, assignments, priority, comments, closure, backlog sweeps, and
  release tags are outside this workflow. Maintainers own contribution gates.

## Rollout after design approval

Follow [CONTRIBUTING.md](../CONTRIBUTING.md) before submitting the implementation.
PR path labels extend #328's issue-only scope and need maintainer alignment.

1. Confirm the organization's approval for Gemini API processing of public issue
   text and its usage budget. An existing secret name does not prove valid access.
2. Keep `EGM_TRIAGE_APPLY` unset. Configure `GEMINI_API_KEY`, set
   `GEMINI_TRIAGE_MODEL=gemini-2.5-flash` (supports disabled thinking and structured
   output), and set `EGM_TRIAGE_ENABLED=true` to enable previews after merge.
3. Use the manual workflow with individual issue numbers to preview representative
   bugs, features, tasks, ambiguous reports, and embedded instructions. Manual
   dispatch never publishes. Compare suggestions with maintainer classifications.
4. Verify native-type and additive-label writes on a disposable test repository
   with a GitHub Actions token before setting `EGM_TRIAGE_APPLY=true` in EGM.
   Review failures and misclassifications before broadening use.

Each issue run is limited to one request, 20000 input characters, 1024 output
tokens, and a 60-second request timeout. No model retry or automatic backlog run
is configured. These bounds do not impose a daily spend cap; use provider quotas.
Missing credentials, invalid JSON, blocked responses, and API errors fail visibly.

Disable `EGM_TRIAGE_ENABLED` to stop new work and cancel any running triage jobs.
Unset `EGM_TRIAGE_APPLY` to return to previews. GitHub offers no atomic conditional
metadata update: the workflow rereads immediately before each write, but a human
edit in the final read/write interval remains possible. It never replaces labels.
