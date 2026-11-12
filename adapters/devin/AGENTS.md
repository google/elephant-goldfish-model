# EGM on Devin Local

For EGM tasks, read `docs/devin.md` in this installed plugin before starting.
Resolve EGM persona and standards paths against this plugin, not the user's project.
Use `run_subagent` and `read_subagent` with the schema exposed in this session.
Request the installed `egm:egm-<persona>` profile if available; otherwise use
`subagent_explore` and instruct it to read the shared persona first.
Pass only the review artifact, referenced sources, persona, and review criteria.
Do not pass the drafting conversation. Use direct dispatch if nesting is unavailable.
Keep reviewers read-only; the parent writes reports. Stop a review if fresh-context
subagents or required reads are unavailable. Never substitute a same-context review.
Host instruction exclusion and native persona tool restrictions are unverified.
