# Skill discovery comparison for #316

One fresh session per case and revision on November 6, 2026. Baseline
`6a8001e` and candidate `ce3e309` used the same prompts without EGM skill
names. The subsequent merge from main did not change either side's skill
files. These are observed selections from one run per case.

| Task | Codex baseline | Codex candidate |
| --- | --- | --- |
| Set up a design and review workspace | Bootstrap | Bootstrap, Draft, Review, Review Loop |
| Explore offline sync tradeoffs | None | Brainstorm |
| Draft a design from an agreed brief | None | Draft |
| Compare architecture and implementation | Drift Report | Drift Report |
| Triage conflicting review findings | None | Resolve |
| Set up a custom structural and style panel | Review Loop | None |
| Run a standard staged design review | Review | Review |
| Answer simple arithmetic | None | None |
| Proofread for spelling only | None | None |

Codex CLI 0.166.0 used one temporary EGM marketplace at a time. Selection
required a successful read of the installed skill file. Global skills were
still available. Each prompt asked for read-only work and disallowed
starting reviewers. The candidate improved three cases but also loaded
extra skills for setup and missed the custom review panel. Repeat those two
cases before deciding whether to retain the shorter descriptions.

Claude Code 2.1.319 with Sonnet 5.5 loaded one generated EGM package per
session. Both packages listed all seven EGM skills, and neither returned
an EGM Skill tool invocation for any of the nine prompts. This matches
the explicit invocation policy in both versions. The probe did not
exercise explicit invocation or full workflows.
