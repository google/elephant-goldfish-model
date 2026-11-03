# Artificial Intelligence & Automated Contribution Policy

We encourage using AI tools when developing changes for our codebase. However,
purely autonomous contributions are not accepted; human contributors must
review, understand, and explain every submitted change.

## Operational Rules

1. **Human Accountability**: Every pull request must have a human author who has
   personally reviewed, tested, and verified every line of changed code.
2. **Interactive Code Review**: Contributors must directly defend their changes
   in review. Copying maintainer review comments into an LLM and pasting
   unverified model responses back into review threads is prohibited.
3. **EGM Design Requirement & Two-Stage Alignment**: Contributors planning features
   or large changes (`> 100` non-test lines or `>= 3` core files in `skills/` or
   `agents/`) should:
   * **a)** Reach out to maintainers first via a
     [Feature Inquiry Issue](https://github.com/google/elephant-goldfish-model/issues/new?template=feature_proposal.md)
     (`.github/ISSUE_TEMPLATE/feature_proposal.md`) to receive
     `design-ready`.
   * **b)** Submit and merge a full EGM design document PR
     (`docs/designs/<name>.md` authored via `/egm-brainstorm`, `/egm-draft`,
     and `/egm-review`, referencing the issue with `Refs #<issue>`) so
     maintainers can apply `pr-ready` to the Feature Inquiry Issue.
   * **c)** Submit and merge an implementation PR of the approved design into
     the codebase (`Closes #<issue>`).
4. **No Artificial PR Splitting**: Do not artificially split a single logical
   feature or refactoring into multiple smaller pull requests (e.g., two 60-line PRs)
   to bypass the 100-line scope threshold.
