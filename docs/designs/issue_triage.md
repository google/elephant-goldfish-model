# Automated issue triage

Status: Proposed. Automated native issue type and topical label classification
for newly opened issues (#328).
Author: @bevinkatti, @n3wth. Date: 2026-11-18.

## Problem statement

Issues created through GitHub's web templates receive native issue types from
template frontmatter, but issues created through the GitHub CLI or API can
arrive without a type. Those untyped issues also lack consistent topical labels,
which adds manual triage work for maintainers. This workflow fills that gap
by assigning types to untyped intake and applying topical labels to every newly
opened issue, when title and body text contain clear signals, while preserving
human choices.

## Goals

- Assign a native `Bug`, `Feature`, or `Task` type to an untyped issue only when
  a canonical template heading or exactly one type's keyword signals identify
  it clearly.
- Add every matching label from a fixed allowlist of eight topical labels when
  its regex matches the issue title or sanitized body text, for every newly
  opened issue including web-template submissions.
- Preserve types and labels set or removed by a human, and keep issue type and
  label writes isolated so failure in one stage does not prevent the other.
- Run only when an issue is opened and keep workflow permissions least-privilege.

## Non-goals

- Do not create missing repository issue types or labels; skip unavailable
  types and labels.
- Do not edit or reopen existing issues, or retroactively classify the backlog.
- Do not run on pull requests, issue edits, or issue reopenings.
- Do not assign or remove maintainer-controlled gate labels (`design-ready`,
  `pr-ready`) or any labels outside the topical allowlist.
- Do not create new issue templates or change the existing issue intake forms.

## Scope

This specification covers `.github/workflows/issue-triage.yml` and its Stage 2
unit and fixture test suites. The workflow does not alter pull request routing
or core EGM skills. The topical label allowlist is `ci`, `tests`, `deps`,
`docs`, `site`, `harness`, `isolation`, and `release`. This closed allowlist is
the safety boundary: labels such as `design-needed` and `triage: passed` are
managed by other automation and are never candidates for this workflow. The
legacy `advisory: design-doc-suggested` label is also outside this workflow's
allowlist and is stripped by the PR scope advisory workflow.
`design-ready` and `pr-ready` remain maintainer-controlled merge gates.

## Trigger, concurrency, and permissions

- **Event trigger**: Run on `issues` with `types: [opened]`. GitHub's issue
  webhook does not fire for pull requests; checking
  `github.event.issue.pull_request == null` is a defensive guard only.
- **Concurrency**: Group runs by
  `${{ github.workflow }}-${{ github.event.issue.number }}` with
  `cancel-in-progress: false`. Even on an opened-only trigger, maintainers may
  rerun a job manually, and separate runs may start close together. Serializing
  them and rereading current issue state reduces conflicting writes.
- **Least privilege**: Set workflow-level `permissions: {}` and grant only
  job-level `issues: write` to the job that consumes `actions/github-script`.
  This is the permission available to the action's workflow token, not a
  permission granted inside the action.

## Intake paths and classification

The three web issue templates already declare native type frontmatter:
`bug_report.md` declares `Bug`, `feature_proposal.md` declares `Feature`, and
`task.md` declares `Task`. The template config hides the blank-issue option from
contributors without write access; users with write access can still open a
maintainer-only blank issue. GitHub sets these types for web template
submissions, so the workflow skips type mutation when a type is already
present, but still evaluates topical labels on those submissions. The templates
do not declare topical labels in frontmatter. Native type assignment covers
untyped intake from `gh issue create`, API calls, and maintainer-created blank
issues.

Sanitize the issue body once before any classification matching by removing
HTML comments and fenced code blocks; keep the title as supplied. Use that same
sanitized body for canonical template-heading matching, type keyword fallback,
and topical label regexes. Template-heading matching uses template-specific
heading combinations: `Expected Behavior` with `Actual Behavior` for bugs,
`Problem Statement & Motivation` with `Proposed Scope (Goals vs. Non-Goals)`
for features, and `Objective` with `Completion Criteria` for tasks. A generic
heading such as `## Scope` alone is not a template match. If headings from more
than one template match, abstain from type assignment for that issue. This
couples the workflow to template prose, so heading matches must be covered by
fixtures and updated with template changes. When there is not a multiple-
template match, keyword fallback assigns a type only when exactly one type
matches; zero or multiple type matches means no type is assigned. Topical
labels are evaluated independently: add every allowlisted label whose own
regex matches, even when multiple labels match one issue. Type ambiguity does
not prevent clear topical labels from being added.

| Stage | Target | Selection rule | Preservation guard |
| :--- | :--- | :--- | :--- |
| 1. Native issue type | Untyped intake from CLI, API, or maintainer blank issues; `Bug`, `Feature`, `Task` | Match canonical template-specific heading combinations in sanitized body first; abstain from type assignment on multiple template matches. A generic heading alone is not a template match. If there is no template match, assign only when exactly one type's keyword signals match the title or sanitized body. | Skip if a type is already set or if a non-bot user account previously changed or cleared it; preserve edits when the actor is unavailable or deleted. |
| 2. Topical labels | Every newly opened issue, including web-template submissions; `ci`, `tests`, `deps`, `docs`, `site`, `harness`, `isolation`, `release` | Independently evaluate each domain regex against the title and sanitized body; add every matching label that exists in the repository. | Never remove labels. Only add allowlisted labels absent from the issue and not previously removed by a non-bot user account; preserve edits when the actor is unavailable or deleted. |

Concurrency prevents overlapping workflow runs from racing each other. Timeline
checks are still needed because a human can edit the issue after the workflow is
queued or while the runner is starting. Query current state immediately before
mutation and inspect `UNLABELED_EVENT`, `ISSUE_TYPE_REMOVED_EVENT`, and
`ISSUE_TYPE_CHANGED_EVENT` events. Preserve human changes made during that
window. For these guards, a human actor is a non-bot user account. If the event
actor is unavailable or the account was deleted, preserve the edit rather than
assuming automation may overwrite it.

## Workflow architecture and API use

Keep the triage logic inline in `.github/workflows/issue-triage.yml` under a
SHA-pinned `actions/github-script` step, following the checkout-free pattern in
`.github/workflows/pr-scope-advisory.yml`. Do not check out the repository or
grant `contents: read`.

Keep native issue-type GraphQL reads separate from issue and label reads. A
permission failure while reading repository issue types or issue-type timeline
fields must not fail the query used to read issue fields, labels, or label
timeline events, and must not prevent topical labeling. Use the REST
`issues.addLabels` endpoint to add topical labels. Attempt type assignment and
topical labeling as independent stages, even if either stage encounters an
error. Preserve successful writes, log warnings for failures, and continue
attempting the other stage and any independent label writes. Aggregate stage
failures and fail the workflow job at the end if either stage failed; do not
report a partially failed run as successful.

## Alternatives considered

| Alternative | Evaluation |
| :--- | :--- |
| Deterministic template headings and keyword rules (proposed) | Easy to audit, test offline, and run without an external model credential. Regexes can miss wording or match incidental text, so sanitize input, keep type fallback conservative, use a closed label allowlist, and cover rules with fixtures. |
| Gemini-based classification represented by the `feat/328-gemini-triage` comparison branch, which follows `.github/workflows/pr-triage-review.yml` | The prototype uses one bounded, tool-free Gemini request, separates read-only classification from writes, and validates the result against the allowlist. It could interpret varied descriptions more flexibly, but adds an API credential and service dependency, plus latency, token cost, variable output, and failure modes. Prefer deterministic rules for this bounded classification unless evaluation shows a material accuracy benefit that justifies those costs. |
| Structured YAML issue forms | GitHub forms can collect explicit fields and set a native type for web submissions. Adopting them would change reporter experience and template maintenance, and would still leave CLI/API-created issues outside the web form flow. |
| Rely only on native `type:` template frontmatter | Already classifies web template submissions with no extra workflow. It leaves CLI/API-created issues untyped and does not apply topical labels, so it does not meet the stated goals. |

## Risks and limits

- **Native issue type permissions are unverified**: `issues: write` may not be
  sufficient for GraphQL reads or mutations of organization-backed native issue
  types. Treat a live permission check in an organization-owned test repository
  with native issue types enabled as a
  Stage 2 gate before rollout. Offline mocks do not prove the workflow token has
  these live permissions.
- **Token fallback**: Always use `GITHUB_TOKEN` for topical-label operations.
  Use it by default for native issue-type operations as well. Only if the
  required native-type permissions are unavailable through `GITHUB_TOKEN`, use
  the narrowly scoped `EGM_ISSUE_TRIAGE_BOT_TOKEN` secret for native issue-type
  operations; do not reuse `EGM_TRIAGE_BOT_TOKEN`, which is used by the PR
  review workflow. Limit the issue-only secret to the required repository
  access and document ownership and rotation before enabling it. If the
  issue-only token is expired or encounters an authentication error, retry the
  native-type operation using `GITHUB_TOKEN`. A token failure must never
  prevent topical-label processing: if native-type processing still fails,
  record and log the failure, continue topical labeling with `GITHUB_TOKEN`,
  and fail the job at the end as described below.
- **Partial failure**: Type and label operations are separate writes and cannot
  be atomic. Attempt both independent stages and all independent label writes;
  preserve successful writes, log warnings for failed operations, and fail the
  workflow job at the end if either stage fails. A type read or mutation error
  must not abort topical labeling, and a label error must not undo a successful
  type write.
- **Heuristic errors**: Text rules can miss intent or produce false positives.
  Removing HTML comments and fenced code blocks reduces template/example
  matches; conservative type fallback and per-label fixtures reduce the risk.
- **Human edits during execution**: A query can become stale before a mutation.
  Concurrency, current-state rereads, and timeline guards reduce this race, but
  cannot make separate GitHub API operations transactional.
- **Scale and API limits**: The workflow runs once per newly opened issue, so a
  burst of issues can consume Actions capacity and GitHub API rate limits.
  Request only the fields and timeline events needed for classification, and
  make rate-limit or pagination failures visible rather than silently applying
  partial classifications.

## Verification and rollout

- **Planned offline checks (Stage 2)**: Run the actual workflow script against
  mock GraphQL and REST APIs in `tests/issue_triage.cjs`, plus static workflow
  assertions in `tests/unit/test_issue_triage.py`. Cover template matching,
  sanitized input (HTML comments and fenced code blocks), keyword fallback,
  abstention when type signals are absent, ambiguous, or match multiple
  templates, independent additive label matching, closed-allowlist enforcement,
  human timeline override preservation, continuation to label assignment after
  a native-type read or write error, fallback to `GITHUB_TOKEN` after an
  issue-triage token authentication or expiry error, preservation of successful
  writes, and a failing job result after either stage fails.
- **Planned live permission check (Stage 2)**: In an organization-owned test
  repository with native issue types enabled, verify that the workflow token
  can read configured issue types, set a native issue type, and add an allowed
  topical label. Keep this separate from offline
  mocks and do not use a production issue for the permission check. If
  `GITHUB_TOKEN` fails, resolve the token fallback decision described above
  before production rollout.
- **Rollout gate**: This Stage 1 design PR can merge after aligned issue #328
  receives `design-ready`. The Stage 2 implementation follows after the design
  merges and issue #328 receives `pr-ready`.
