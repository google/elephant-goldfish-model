<!-- Title: Start with an action verb and use sentence case. Describe the change.
Omit unnecessary words when the meaning stays clear. Keep articles when needed.
Example: Explain ignored agents folder warning in Claude Code -->

<!-- Labels: Add applicable labels: docs, site, ci, or deps.
If you cannot apply labels, suggest them in the description.
Maintainers control design-ready and pr-ready. Automation manages design-needed. -->

## Contribution Type

Replace the value below with exactly one of the track names listed here:

Track: <choose one track>

- **Bug Fix / Minor Patch**: targeted fix, non-test diff <= 100 lines and < 3 core files in `skills/` or `agents/`; no design doc required.
- **Feature / Architectural Change -- Stage 1: Design Doc PR**: use `Refs #___` with `design-ready`; add `docs/designs/<name>.md` and update the design index. Keep the issue open for Stage 2.
- **Feature / Architectural Change -- Stage 2: Implementation PR**: use `Closes #___` with `pr-ready`; implement a merged design.

<!-- Delete the track explanations above after selecting your track. -->

## Summary of Key Changes

List all key changes made in this pull request and why:

<!-- Describe each key change and its motivation here. -->

## Human Accountability Affirmation

- [ ] I am a human contributor. I have personally reviewed, understood, and can explain every line of this change in review (using AI tools to write code is welcome, but human understanding of the submitted change is required).

## Verification

Record results as **passed**, **not run**, or **not applicable**. Include commands,
outputs or evidence links, and limits. Delete entries that do not apply.

Unit tests and relative links: <result; commands and evidence>

Design review (Stage 1): <result; `/egm-review`, `/egm-resolve`, and remaining findings>

Native harness workflows (harness support): <result; host/version, installation,
`/egm-brainstorm`, `/egm-draft`, `/egm-review`, and transcript or summary>

Other checks and limits: <results; checks not run and why>
