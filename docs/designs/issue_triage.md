# Automated issue triage

Status: Proposed. Automated native issue type and topical label classification for newly opened issues (#328).
Author: @bevinkatti, @n3wth. Date: 2026-11-18.

## Purpose and scope

Automatically classify newly opened GitHub issues by assigning a native GitHub
issue type and additive topical labels when unambiguous signals are present.
This workflow reduces manual maintainer triage overhead while preserving human
editorial overrides and governance gate labels.

This specification covers the `.github/workflows/issue-triage.yml` intake
workflow and its unit and fixture test suites. It does not alter pull request
routing, maintainer-controlled governance labels (`design-ready`, `pr-ready`,
`design-needed`, `advisory: design-doc-suggested`), or core EGM skills.

## Trigger and permissions

- **Event trigger**: Runs on `issues` with `types: [opened]`, skipping pull
  request events (`github.event.issue.pull_request == null`).
- **Concurrency**: Groups runs by `${{ github.workflow }}-${{ github.event.issue.number }}`
  with `cancel-in-progress: false` to serialize triage per issue.
- **Least privilege**: Sets workflow-level `permissions: {}` and grants only
  job-level `issues: write` inside `actions/github-script` (pinned by commit SHA).

## Classification and human-override preservation

The workflow queries repository issue types, existing repository labels, the
issue title and body, and timeline events (`UNLABELED_EVENT`,
`ISSUE_TYPE_REMOVED_EVENT`, `ISSUE_TYPE_CHANGED_EVENT`) via GraphQL before
making mutations:

| Stage | Target | Selection rule | Preservation guard |
| :--- | :--- | :--- | :--- |
| 1. Native issue type | `Bug`, `Feature`, `Task` | Matches canonical issue template headings first; falls back to keyword signals only when exactly one type matches unambiguously. | Skips mutation if an issue type is already set or if a non-bot actor previously changed or cleared the issue type. |
| 2. Topical labels | `ci`, `tests`, `deps`, `docs`, `site`, `harness`, `isolation`, `release` | Evaluates domain regex patterns against combined issue title and body; applies all matching labels that exist in the repository. | Never removes existing labels, never applies excluded governance labels, and skips any label previously removed by a human actor. |

## Verification and rollout

- **Behavioral and static tests**: Verified via mock GraphQL/REST harnesses in
  `tests/issue_triage.cjs` and static workflow assertions in
  `tests/unit/test_issue_triage.py`, covering template matching, keyword
  fallback, ambiguous signal abstention, governance label exclusion, and human
  timeline override preservation.
- **Rollout**: Ships in Stage 2 implementation PR (#334) once this Stage 1
  design specification merges and issue #328 receives `pr-ready`.