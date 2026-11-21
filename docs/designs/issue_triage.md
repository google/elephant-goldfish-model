# Automated issue triage

Status: Proposed. Automated native issue type and topical label classification
for newly opened issues (#328).
Author: @bevinkatti, @n3wth. Date: 2026-11-18.

## Problem statement

Issues created through GitHub's web templates receive native issue types from
template frontmatter, but issues created through the GitHub CLI or API can
arrive without a type. Newly opened issues across all intake paths lack
consistent topical labels, which adds manual triage work for maintainers. This
workflow fills that gap by assigning types to untyped intake and applying
topical labels to every newly opened issue when title and body text contain
clear signals, while preserving human choices.

## Goals

- Assign a native `Bug`, `Feature`, or `Task` type to an untyped issue only when
  a canonical template-heading combination matches or, if none matches,
  exactly one type's keyword signals identify it clearly.
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
  permission granted inside the action. These declared permissions apply to
  `GITHUB_TOKEN`, not the optional issue-only fallback secret described under
  Risks and limits; scope that secret independently if enabled.

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
or stray heading such as `## Scope` alone is not a template match and cannot
classify an issue. If heading combinations from more than one template match
(a multiple-template match), abstain from type assignment for that issue. This
couples the workflow to template prose, so heading combinations must be covered
by fixtures and updated with template changes. When no template heading
combination matches, keyword fallback assigns a type only when exactly one type
matches; zero or multiple type matches means no type is assigned. Topical
labels are evaluated independently: add every allowlisted label whose own
regex matches, even when multiple labels match one issue. Type ambiguity does
not prevent clear topical labels from being added.

| Stage | Target | Selection rule | Preservation guard |
| :--- | :--- | :--- | :--- |
| 1. Native issue type | Untyped intake from CLI, API, or maintainer blank issues; `Bug`, `Feature`, `Task` | Match canonical template-heading combinations in sanitized body first; abstain from type assignment on a multiple-template match. A generic or stray heading alone is not a match. When no template heading combination matches, assign only when exactly one type's keyword signals match the title or sanitized body. | Skip if a type is already set or if a non-bot user account previously changed or cleared it; preserve edits when the actor is unavailable or deleted. |
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

Read current issue fields and current issue labels separately from the
repository label catalog. Check the repository label catalog before adding
labels because missing labels must not be created automatically. Check current
issue labels first, then add all matching allowlisted labels that exist in the
repository but are missing from the issue in one batched REST
`issues.addLabels` call, not one API request per label.

The initial issue-field GraphQL query retrieves title, body, and current labels
under `GITHUB_TOKEN` and does not include the native issue type. A separate
isolated read using the native-type credential checks whether a type is already
present. Use `GITHUB_TOKEN` by default, with the optional fallback described
under Risks and limits. If a type is already present, skip the repository
issue-type catalog and issue-type timeline GraphQL reads, and skip type
assignment; this includes web-template submissions. If the issue is untyped,
perform those separate native-type reads to determine whether assignment is
available and whether a human override exists. Keep native-type reads separate
from the repository label catalog and label timeline reads. If either separate
native-type read fails, record a type-stage runtime error and continue topical
labeling using the already-fetched issue fields; no reread of issue fields is
needed.

Assign the selected native type with the GraphQL
`updateIssueIssueType` mutation; use the REST `issues.addLabels` endpoint for
topical labels. Keep the type and label stages independent so either is
attempted if the other encounters an error.

Expected skips (an issue already has a type; native types are unavailable on
user-owned repositories or an empty repository issue-type catalog; an
allowlisted label is missing from the repository catalog; a human override is
present; or classification signals are ambiguous) complete successfully.
Unrecovered authentication or permission failures, 5xx responses,
rate limits, incomplete pagination, and rejected writes are runtime errors:
record them, continue the independent stage, and fail the workflow job at the
end if a runtime error occurred. A successful HTTP 401 fallback retry is a
recovered operation, not a runtime error.

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
  native types are enabled but required native-type permissions are unavailable
  through `GITHUB_TOKEN`, use a narrowly scoped fallback credential for
  native issue-type operations; do not reuse `EGM_TRIAGE_BOT_TOKEN`, which is
  used by the PR review workflow. Do not configure this fallback by default.
  If enabled, prefer minting a short-lived GitHub App installation token per run
  (from an App ID and private key secret) for `Bot` actor attribution on
  timeline events; alternatively, a dedicated static `EGM_ISSUE_TRIAGE_BOT_TOKEN`
  secret may be used, which carries user-account attribution instead. Maintainers
  must document ownership and rotation policy before enabling either credential.
  Limit the credential to the required repository access.
  Retry a native-type operation with `GITHUB_TOKEN` only when the
  issue-only token returns HTTP 401 for an authentication or expiry error, not
  for rate limits. If that retry succeeds, emit a `core.warning` notice and use
  the successful fallback token for the remainder of the run; the native-type
  operation succeeds and does not cause a job failure. A token failure must
  never prevent topical
  labels, which always use `GITHUB_TOKEN`; if native-type processing still
  fails, record and log the failure, continue topical labeling, and fail the
  job at the end as described below.
- **Partial failure**: Type and topical-label stages are independent. Attempt
  both and preserve successful writes. Log runtime errors and continue the
  other stage; after both stages finish, fail the workflow job if any runtime
  error remains unrecovered. Expected skips are successful outcomes and do not
  fail the job. A type-stage error must not prevent topical-label processing,
  and a label-stage error must not undo a successful type write.
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
  templates, independent additive label matching, existing-label checks and a
  single batched `issues.addLabels` call, closed-allowlist enforcement, expected
  skips completing successfully, and human timeline override preservation.
  Verify continuation to label assignment after a native-type read or write
  error; retry with `GITHUB_TOKEN` only after an issue-triage token HTTP 401,
  with a `core.warning` emitted and the fallback token latched for the remainder
  of the run on a successful retry, and no retry for rate limits; preserve
  successful writes and require a failing job result for runtime errors.
- **Planned live permission check (Stage 2)**: In an organization-owned test
  repository with native issue types enabled, verify that the workflow token
  can read configured issue types and the relevant issue-type and label
  timeline events (`ISSUE_TYPE_REMOVED_EVENT`, `ISSUE_TYPE_CHANGED_EVENT`, and
  `UNLABELED_EVENT`), set a native issue type, and add an allowed topical label.
  Keep this separate from offline mocks and do not use a production issue for
  the permission check. If `GITHUB_TOKEN` lacks the required native-type
  permission, resolve the token fallback decision described above before
  production rollout.
- **Rollout gate**: This Stage 1 design PR can merge after aligned issue #328
  receives `design-ready`. The Stage 2 implementation follows after the design
  merges and issue #328 receives `pr-ready`.
