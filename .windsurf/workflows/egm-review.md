---
description: Route to canonical skills/egm-review/SKILL.md without copied skill text.
---

1. Read `skills/egm-review/SKILL.md` from the EGM package root.
2. Execute the skill.
3. Resolve `agents/*.md` and `resources/document_standards/*.md` relative to the package root.
4. Require fresh-context, read-only subagents before running Goldfish swarm steps. If unavailable in Windsurf Cascade, stop immediately, report that a same-context review is not a Goldfish review, and invoke no write or shell tools.
5. Launch each reviewer with the host's read-only subagent profile. Never use a write-capable profile and never resume a reviewer. Reviewers return findings as text; only the parent writes files, after the user approves.
