---
trigger: model_decision
description: Route Elephant-Goldfish Model (EGM) brainstorming, drafting, review, resolution, drift-report, and bootstrap requests to the canonical shared skills and enforce fresh-context Goldfish isolation.
---

# EGM Routing and Isolation Contract (Experimental)

1. Resolve all EGM workflows from the shared `skills/<skill-name>/SKILL.md` files at the repository root. Never rely on copied skill instructions.
2. Resolve reviewer personas from `agents/*.md` and document rubrics from `resources/document_standards/*.md` relative to the same root.
3. Keep human approval pauses and file-output boundaries defined in each `SKILL.md` intact.
4. Goldfish review workflows (`egm-review`, `egm-review-loop`, `egm-drift-report`, and `egm-bootstrap`) require isolated, read-only subagent execution with zero parent authoring history. If Windsurf Cascade cannot spawn fresh-context read-only subagents in the active session, stop and report that required subagent isolation is unavailable. Never simulate multiple reviewers inline inside one context window.
