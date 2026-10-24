# Contributing to the Elephant-Goldfish Model (EGM) Plugin

We welcome contributions! We all benefit when new ideas, skills, and reviewer
perspectives are shared across the open-source community.

## Design Principles

These general principles guide development of the EGM framework:

*   **Humans Own the Outcomes**: AI is an exploration and review partner, but
    human engineers remain responsible for all design decisions and code.
*   **Artifact-First UX**: Large proposals, drafts, and reviews belong in
    dedicated files, not dumped into chat streams.
*   **Living Specifications**: Code and design specifications must evolve
    together.

## Contribution Tracks & Workflow

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
(`advisory: design-doc-suggested`) recommending two-stage alignment.

### Track 2: Feature / Architectural Change (Two-Stage Alignment)
Any new skill, persona, or change exceeding `100` non-test
lines (or touching `>= 3` core files in `skills/` or `agents/`)
follows the EGM Spec-Driven Development process:

1.  **Reach Out & Align (`status: approved-for-design`)**:
    Before investing in a large implementation or full specification, open a
    [Feature / Architectural Inquiry Issue](https://github.com/google/elephant-goldfish-model/issues/new?template=feature_proposal.md)
    (`.github/ISSUE_TEMPLATE/feature_proposal.md`) outlining the problem
    statement and proposed `Goals` vs. `Non-Goals`. We recommend using
    `/egm-brainstorm` to complete this section. Maintainers will review and apply
    `status: approved-for-design` once aligned on direction.

2.  **Draft & Review Design Specification**:
    Draft a technical design specification under `docs/designs/<name>.md`. We
    recommend using `/egm-draft`, and registering it in [`docs/designs/README.md`](docs/designs/README.md).
    We also recommend running `/egm-review docs/designs/<name>.md` to stress-test
    the proposal.

4.  **Submit a Design Doc PR (`status: approved-for-pr`)**:
    Open a dedicated **Design Doc PR** containing `docs/designs/<name>.md`
    and `docs/designs/README.md` (referencing your aligned issue with
    `Refs #<issue>` rather than `Closes #<issue>` so the issue stays open).
    When maintainers merge the Design Doc PR, the specification is checked into
    the codebase and maintainers manually transition the issue label to
    `status: approved-for-pr`.

5.  **Submit the Implementation PR**:
    Once the specification is merged and your issue is labeled
    `status: approved-for-pr`, open the implementation PR (`Closes #<issue>`)
    referencing `docs/designs/<name>.md`.

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

This project follows
[Google's Open Source Community Guidelines](https://opensource.google/conduct/).
