# Test Plan: EGM Ask Skill

Frontmatter, link checks, and scenario coverage run in `pytest tests/unit` (see [TESTING.md](../../TESTING.md)).

## Protocol Verification Checklist

When evaluating or exploring `egm-ask` interactively in chat, verify:

- **Read-Only & Gate Safety:** Never edits files, runs shell commands (`git status`), spawns subagents, or selects options on a pending approval gate from another skill (`egm-resolve`, `egm-review`, `egm-draft`).
- **Question Classification:**
  - *Next step* (including empty prompt): inspects workspace artifact names and cites `docs/getting_started.md`.
  - *Skill choice* (including task requests like "Fix my draft"): reads `skills/*/SKILL.md` frontmatter without editing files and recommends the matching skill.
  - *Troubleshooting*: cites `docs/harnesses.md` and the active harness guide (`docs/claude.md` or `docs/codex.md`), or suggests opening an issue when undocumented.
  - *Out of scope*: declines non-EGM programming questions cleanly.
- **Stage & Implementation Guards:** Lists all artifacts seen, asks whether a started review finished before recommending `egm-resolve`, and verifies target clarity and human approval before suggesting implementation.
- **Reply Shape:** Uses `**Where you are:**`, `**Answer:**`, `**Next steps:**` (at most 3), and `**Source:**` within 20 lines.
