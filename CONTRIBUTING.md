# Contributing to the Elephant-Goldfish Model (EGM) Plugin

We welcome contributions! We all benefit when new ideas, skills, and reviewer
perspectives are shared across the open-source community.

## Which track is my change?

Pick a track before you open an issue or PR. The full rules for each track are
in [Contribution Tracks & Workflow](#contribution-tracks--workflow); this
section points to them.

For your first contribution, choose an unclaimed
[good first issue](https://github.com/google/elephant-goldfish-model/issues?q=is%3Aissue%20is%3Aopen%20label%3A%22good%20first%20issue%22).
Comment on the issue to say you want to work on it. Confirm your
[Google CLA coverage](#contributor-license-agreement-cla) and run the checks
listed in the issue before you open a PR.

*   **Small fix within the Track 1 limits:** open a PR with the
    [PR template](.github/PULL_REQUEST_TEMPLATE.md).
*   **New feature, architectural change, or anything over the Track 1
    limits:** follow the Track 2 steps, starting with a Stage 1 Design Doc PR
    adding `docs/designs/<name>.md`. Existing design docs are listed in
    [docs/designs/README.md](docs/designs/README.md).

**Example:** If a documentation link is broken, fix the destination on a
branch, follow the [test setup in TESTING.md](TESTING.md), and run
`pytest tests/unit/test_link_integrity.py`. Open a Track 1 PR with the
[PR template](.github/PULL_REQUEST_TEMPLATE.md) and record the result. A
small fix like this does not need a prior issue or design document.

For usage questions, use [Discussions Q&A](https://github.com/google/elephant-goldfish-model/discussions/categories/q-a).

## Design Principles

These general principles guide development of the EGM framework:

*   **Humans Own the Outcomes**: AI is an exploration and review partner, but
    human engineers remain responsible for all design decisions and code.
*   **Artifact-First UX**: Large proposals, drafts, and reviews belong in
    dedicated files, not dumped into chat streams.
*   **Living Specifications**: Code and design specifications must evolve
    together.

## Contribution Tracks & Workflow

Write a short PR title that starts with an action verb. Use sentence case and
describe the change. Omit unnecessary words when the meaning stays clear.
Keep articles such as "a" and "the" when needed for clarity.
Example: `Explain ignored agents folder warning in Claude Code`.

Add applicable labels: `docs` for documentation, `site` for the website,
`ci` for GitHub Actions, or `deps` for dependencies. If you cannot apply labels,
suggest them in the PR description. Automation manages `design-needed` and
`triage: passed`.

All contributions must comply with our [AI & Automated Contribution Policy](AI_POLICY.md):
every pull request requires a human author who has reviewed and tested the change. They
should be able to explain it themselves.

Contributions follow a two-track intake model defined in
[`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md):

### Track 1: Bug Fix / Minor Patch (`<= 100` Non-Test Lines, `< 3` Core Files)
Targeted fixes, typo corrections, and test additions that do not alter core
agent behavior or touch 3+ core files (`skills/`, `agents/`) can be
submitted directly as a Pull Request without a design document.
PRs exceeding these limits without an approved design doc receive an advisory label
(`design-needed`) recommending two-stage alignment.

### Track 2: Feature / Architectural Change (Two-Stage Alignment)
Any new skill, persona, or change exceeding `100` non-test
lines (or touching `>= 3` core files in `skills/` or `agents/`)
follows the EGM Spec-Driven Development process:

1.  **Draft & Review Design Specification**:
    Explore the problem with `/egm-brainstorm`, draft a technical design
    specification under `docs/designs/<name>.md` (we recommend `/egm-draft`),
    and register it in [`docs/designs/README.md`](docs/designs/README.md).
    We also recommend running `/egm-review docs/designs/<name>.md` to stress-test
    the proposal before opening a PR.

2.  **Submit and Merge a Stage 1 Design Doc PR**:
    Open a dedicated **Design Doc PR** containing `docs/designs/<name>.md` and
    `docs/designs/README.md`. Maintainers review the scope, `Goals` vs.
    `Non-Goals`, and technical design directly on this PR. When maintainers
    approve and merge the Design Doc PR, the specification is checked into
    the codebase.

3.  **Submit the Stage 2 Implementation PR**:
    Write and submit the implementation PR referencing both the Stage 1 PR
    (`#<stage1-pr>`) and `docs/designs/<name>.md`. To start early, stack it on
    the Design Doc PR as a draft until Stage 1 merges.

### Stacked Pull Requests and Size

*   **Stack**: When one PR depends on another, use GitHub
    [stacked pull requests](https://docs.github.com/en/pull-requests/how-tos/stacked-pull-requests).
    The Design Doc PR targets `main`. The implementation PR targets the design
    branch and stays a draft until the design merges. Use `gh stack submit`,
    or `gh stack link <PR> <PR>` for open PRs. GitHub does not auto-merge a
    stacked PR. This requires branches in the upstream repository. Fork
    contributors can prepare the stack locally, then open the implementation
    PR after the Design Doc PR merges.
*   **Size**: Give each PR one purpose. Aim for about 200 changed lines that a
    reviewer must read, and split above about 400 (see Google's
    [small changes](https://google.github.io/eng-practices/review/developer/small-cls.html)
    guide). Put renames, moves, and deletions in a PR of their own. Each PR
    must pass the tests on top of the PR below it.
*   **Links**: Stage 2 PRs link their Stage 1 PR and `docs/designs/<name>.md`.
    When fixing an existing bug or task issue, lower PRs in a stack use
    `Refs #<issue>` and the top PR uses `Closes #<issue>` (or `Fixes #<issue>`
    for a standalone minor patch). Put follow-up work in a new issue.
*   **Limits**: The track limits apply to the whole stack. Do not split a
    feature into minor patches to avoid the design process.

## Issues and review comments

Search existing issues and pull requests by affected skill, host, and version
before opening an issue. Add new reproduction steps or evidence to an existing
issue when it covers the same behavior. Link related work when the scope differs.

Choose Bug for behavior that fails, Feature for new behavior or architecture,
and Task for scoped maintenance, documentation, or validation. If you file
outside the GitHub issue chooser, copy the matching
[issue template](.github/ISSUE_TEMPLATE) and set the native issue type
explicitly. For example, pass `--type Task` to `gh issue create` for a Task.

When a maintainer confirms a duplicate, use GitHub's `Duplicate of #123` comment
and preserve any unique reproduction steps or PR links on the canonical issue.
Ask usage questions in [Discussions Q&A](https://github.com/google/elephant-goldfish-model/discussions/categories/q-a).

Before commenting on a PR, read the current diff and existing review threads.
Reply in the existing thread when it covers the finding. For a new finding, cite
the affected line or behavior, explain the impact, and ask for a concrete change.
For example, “The help example uses the old flag, so the command exits with an
unknown-option error. Update the example to use `--dry-run`.”
For template feedback, link the [PR template](.github/PULL_REQUEST_TEMPLATE.md).

## Automated Validation & Testing

*   **Skill Definitions**: Ensure all `SKILL.md` files contain valid YAML
    frontmatter (`name`, `description`, and optional `disable-model-invocation`).
*   **Evaluation Suites**: Skills must include a co-located behavioral
    evaluation suite in `skills/<skill_name>/test_scenarios.yaml` and
    verification instructions in `skills/<skill_name>/TEST.md`. See
    [TESTING.md](TESTING.md) for running static checks (`pytest tests/unit`).
*   **Formatting**: Format markdown files cleanly using standard formatters
    (e.g., Prettier or markdownlint).

## Contributor License Agreement (CLA)

Contributions to this project must be accompanied by a
[Contributor License Agreement](https://cla.developers.google.com/about) (CLA).
You (or your employer) retain the copyright to your contribution; this simply
gives us permission to use and redistribute your contributions as part of the
project.

If you or your current employer have already signed the Google CLA (even if it
was for a different project), you probably don't need to do it again.

Visit <https://cla.developers.google.com/> to see your current agreements or to
sign a new one.

## Community Guidelines

See our [accessibility statement](ACCESSIBILITY.md) for goals, current limits,
and how to report accessibility barriers.

This project follows
[Google's Open Source Community Guidelines](https://opensource.google/conduct/).
