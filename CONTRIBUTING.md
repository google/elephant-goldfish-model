# Contributing to the Elephant-Goldfish Model (EGM) Plugin

We welcome contributions! We all benefit when new ideas, skills, and reviewer
perspectives are shared across the open-source community.

## Which track is my change?

Pick a track before you open an issue or PR. The full rules for each track are
in [Contribution Tracks & Workflow](#contribution-tracks--workflow); this
section points to them.

*   **Small fix within the Track 1 limits:** open a PR with the
    [PR template](.github/PULL_REQUEST_TEMPLATE.md).
*   **New feature, architectural change, or anything over the Track 1
    limits:** open a
    [feature proposal issue](https://github.com/google/elephant-goldfish-model/issues/new?template=feature_proposal.md)
    and follow the Track 2 steps. Existing design docs are listed in
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
suggest them in the PR description. Maintainers control `design-ready` and
`pr-ready`. A PR needs its label to merge. You can open the PR earlier.
Automation manages `design-needed` and `triage: passed`.

All contributions must comply with our [AI & Automated Contribution Policy](AI_POLICY.md):
every pull request requires a human author who has reviewed and tested the change. They
should be able to explain it themselves.

Contributions follow a two-track intake model defined in
[`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md):

### Track 1: Bug Fix / Minor Patch (`<= 100` Non-Test Lines, `< 3` Core Files)
Targeted fixes, typo corrections, and test additions that do not alter core
agent behavior or touch 3+ core files (`skills/`, `agents/`) can be
submitted directly as a Pull Request without a prior issue or design document.
PRs exceeding these limits without an approved design doc receive an advisory label
(`design-needed`) recommending two-stage alignment.

### Track 2: Feature / Architectural Change (Two-Stage Alignment)
Any new skill, persona, or change exceeding `100` non-test
lines (or touching `>= 3` core files in `skills/` or `agents/`)
follows the EGM Spec-Driven Development process:

1.  **Reach Out & Align (`design-ready`)**:
    Before investing in a large implementation or full specification, open a
    [Feature / Architectural Inquiry Issue](https://github.com/google/elephant-goldfish-model/issues/new?template=feature_proposal.md)
    (`.github/ISSUE_TEMPLATE/feature_proposal.md`) outlining the problem
    statement and proposed `Goals` vs. `Non-Goals`. We recommend using
    `/egm-brainstorm` to complete this section. Maintainers will review and apply
    `design-ready` once aligned on direction.

2.  **Draft & Review Design Specification**:
    Draft a technical design specification under `docs/designs/<name>.md`. We
    recommend using `/egm-draft`, and registering it in [`docs/designs/README.md`](docs/designs/README.md).
    We also recommend running `/egm-review docs/designs/<name>.md` to stress-test
    the proposal.

3.  **Submit a Design Doc PR and wait for `pr-ready`**:
    You can open this PR before `design-ready` is applied. It merges after.
    Open a dedicated **Design Doc PR** containing `docs/designs/<name>.md`
    and `docs/designs/README.md` (referencing your aligned issue with
    `Refs #<issue>` rather than `Closes #<issue>` so the issue stays open).
    When maintainers merge the Design Doc PR, the specification is checked into
    the codebase and maintainers manually transition the issue label to
    `pr-ready`.

4.  **Submit the Implementation PR**:
    Open the implementation PR (`Closes #<issue>`) referencing
    `docs/designs/<name>.md`. It merges after the specification merges and the
    issue has `pr-ready`. To start early, stack it on the Design Doc PR as a
    draft.

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
*   **Links**: A feature has one issue. Lower PRs in a stack use
    `Refs #<issue>`. The top PR uses `Closes #<issue>`. A minor patch uses
    `Fixes #<issue>` when an issue exists. Put follow-up work in a new issue.
*   **Limits**: The track limits apply to the whole stack. Do not split a
    feature into minor patches to avoid the design process.

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
