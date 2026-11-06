# Review workflow example

This branch demonstrates structured issue forms and proposes a way to distribute human reviews. The forms use EGM’s existing Bug, Task, and Feature categories and preserve the design approval process.

## Example task

**Outcome:** Record a timed-out reviewer as incomplete so a maintainer can distinguish it from a clean review.

**Scope:** Replay one review with an unavailable reviewer and inspect the resulting report.

**Done when:** The report identifies the unavailable reviewer and leaves the review incomplete. Attach sanitized evidence from the replay.

## Team assignment proposal

The current catch-all CODEOWNERS rule lists individual reviewers. Ask a Google organization owner or team maintainer to identify a visible team with write access and confirm its membership. Configure load balancing to request one available reviewer for routine PRs, count existing requests, and notify only the requested members. Maintainers can request additional reviewers as needed.

Once the team is verified, replace the catch-all owner list with its actual handle. Preserve existing approval rules. On a ready PR, confirm that one individual is requested, the assigned code owner’s approval satisfies the existing rule, and the all-busy fallback is understood.

[GitHub team review settings](https://docs.github.com/en/enterprise-cloud%40latest/organizations/organizing-members-into-teams/managing-code-review-settings-for-your-team)
