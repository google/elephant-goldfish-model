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
   * **a)** Submit and merge a full EGM design document PR
     (`docs/designs/<name>.md` authored via `/egm-brainstorm`, `/egm-draft`,
     and `/egm-review`) as Stage 1.
   * **b)** Submit and merge an implementation PR of the approved design into
     the codebase (linking `docs/designs/<name>.md` and the Stage 1 PR) as
     Stage 2.

   A contributor can prepare (a) and (b) early as a draft stack; Stage 2 merges
   after Stage 1 lands. See
   [CONTRIBUTING.md](CONTRIBUTING.md#stacked-pull-requests-and-size).
4. **No Artificial PR Splitting**: Do not artificially split a single logical
   feature or refactoring into multiple smaller pull requests (e.g., two 60-line PRs)
   to bypass the 100-line scope threshold. A stack of small pull requests implementing
   one design is not artificial splitting.
