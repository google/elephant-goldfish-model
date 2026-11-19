# Automated issue triage

Status: Proposed. Automated native issue type and topical label classification
for newly opened issues (#328).
Author: @bevinkatti, @n3wth. Date: 2026-11-18.

## Problem statement

Issues created through GitHub's web templates receive native issue types from
template frontmatter, but issues created through the GitHub CLI or API can
arrive without a type. Those untyped issues also lack consistent topical labels,
which adds manual triage work for maintainers. This workflow fills that gap
when title and body text contain clear signals while preserving human choices.

## Goals

- Assign a native `Bug`, `Feature`, or `Task` type to an untyped issue only when
  a canonical template heading or exactly one type's keyword signals identify
  it clearly.
- Add every matching label from a fixed allowlist of eight topical labels when
  its regex matches the issue title or sanitized body text.
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
present. Issues created through `gh issue create` or API calls can still arrive
without that web-template metadata; those are the main intake paths this
workflow covers.

When an untyped issue body follows a canonical template, matching its heading
provides a deterministic classification signal for CLI/API intake. This does
couple the workflow to template prose, so heading matches must be covered by
fixtures and updated with template changes. If no heading matches, keyword
fallback runs against the issue title and sanitized body. Exactly one matching
type is required; zero or multiple type matches means no type is assigned.

Before matching either type keywords or topical label regexes, strip HTML
comments and fenced code blocks from the issue body. Keep the title as supplied.
This prevents template instructions and code examples from being treated as
reporter signals. Topical labels are evaluated independently: add every
allowlisted label whose own regex matches, even when multiple labels match one
issue. Type ambiguity does not prevent clear topical labels from being added.

| Stage | Target | Selection rule | Preservation guard |
| :--- | :--- | :--- | :--- |
| 1. Native issue type | `Bug`, `Feature`, `Task` | Match canonical issue template headings first; otherwise assign only when exactly one type's keyword signals match the title or sanitized body. | Skip if a type is already set or if a human actor previously changed or cleared it. |
| 2. Topical labels | `ci`, `tests`, `deps`, `docs`, `site`, `harness`, `isolation`, `release` | Independently evaluate each domain regex against the title and sanitized body; add every matching label that exists in the repository. | Never remove labels. Only add allowlisted labels absent from the issue and not previously removed by a human actor. |

Concurrency prevents overlapping workflow runs from racing each other. Timeline
checks are still needed because a human can edit the issue after the workflow is
queued or while the runner is starting. Query current state immediately before
mutation and inspect `UNLABELED_EVENT`, `ISSUE_TYPE_REMOVED_EVENT`, and
`ISSUE_TYPE_CHANGED_EVENT` events. Preserve human changes made during that
window. Use the term `human actor` consistently for these guards.

## Workflow architecture and API use

Keep the triage logic inline in `.github/workflows/issue-triage.yml` under a
SHA-pinned `actions/github-script` step, following the checkout-free pattern in
`.github/workflows/pr-scope-advisory.yml`. Do not check out the repository or
grant `contents: read`.

Use GraphQL to read repository issue types, repository labels, issue fields,
and the issue timeline, and to set a selected native issue type. Use the REST
`issues.addLabels` endpoint to add topical labels. If the type mutation fails,
log a warning and continue to the topical label stage. Attempt label writes
independently so a type failure cannot block them; a label failure must not
undo a successful type write. Report write failures in the job logs and retain
any successful write.

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
  types. Treat a live permission check in a controlled test repository as a
  Stage 2 gate before rollout. Offline mocks do not prove the workflow token has
  these live permissions.
- **Token fallback**: Do not add a bot token by default. If the controlled live
  check proves `GITHUB_TOKEN` cannot read or mutate the required native types,
  evaluate a narrowly scoped `EGM_TRIAGE_BOT_TOKEN` secret as a fallback. Limit
  its repository access and document ownership and rotation before enabling it.
- **Partial failure**: Type and label operations are separate writes and cannot
  be atomic. Isolate them so a type mutation failure logs a warning and does not
  abort label assignment; preserve a successful write if the other operation
  fails and surface failures in the workflow result/logs.
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
  abstention when type signals are absent or ambiguous, independent additive
  label matching, closed-allowlist enforcement, human timeline override
  preservation, and continuation to label assignment after a type-write error.
- **Planned live permission check (Stage 2)**: In a controlled test repository,
  verify that the workflow token can read configured issue types, set a native
  issue type, and add an allowed topical label. Keep this separate from offline
  mocks and do not use a production issue for the permission check. If
  `GITHUB_TOKEN` fails, resolve the token fallback decision described above
  before production rollout.
- **Rollout gate**: This Stage 1 design PR can merge after aligned issue #328
  receives `design-ready`. The Stage 2 implementation follows after the design
  merges and issue #328 receives `pr-ready`.
