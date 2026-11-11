---
trigger: model_decision
description: Route EGM requests to shared skills. Require fresh-context isolation for Goldfish reviews.
---

# EGM Routing and Isolation Contract (Experimental)

1. Require a workspace-root checkout. Resolve all EGM workflows from `skills/<skill-name>/SKILL.md`, `agents/*.md`, and `resources/document_standards/*.md` at the repository root without copied skill text.
2. Preserve all human approval pauses and file-output boundaries from each `SKILL.md`.
3. Run `egm-draft`, `egm-resolve`, and `egm-drift-report` in the active session; in `egm-bootstrap`, run scout steps inline when no subagent tool exists.
4. Run Goldfish swarm workflows (`egm-brainstorm`, `egm-review`, `egm-review-loop`) only with fresh-context, read-only subagents that receive zero parent history. If Windsurf Cascade cannot create these subagents, stop immediately, report that a same-context review is not a Goldfish review, and invoke no file-write or shell tools.
5. Launch every Goldfish reviewer with the host's read-only subagent profile (`subagent_explore` in the Devin CLI). Never give a reviewer a write-capable profile and never resume a reviewer. Reviewers return findings as text. Only the parent writes files: the outputs that `SKILL.md` assigns to it, or a file the user asks for, after the user approves the write.
