# EGM in Chat: a document-first skill for chat hosts

- **Author:** @n3wth
- **Status:** Proposed. Maintainer scope approval is pending.
- **Date:** 2026-11-16
- **Scope issue:** #414
- **Related:** #460, #419, #438 (`egm-lite` for repo-backed engineering), #371 (24 KB skill load limit)
- **Earlier names:** `egm-lite`, `egm-chat`. This design proposes `/egm-in-chat` (`EGM for ChatGPT` in the OpenAI UI).

## Overview

Add a separate `egm-in-chat` skill (`display_name: "EGM for ChatGPT"`) for chat hosts that have no local executor, such as ChatGPT Chat and Work on the web.
It helps a user shape an idea, draft a plan, and review a document from chat context and user-supplied files.
It ships in its own package outside `skills/`, so no coding harness loads it and published `/egm` behavior does not change.

The skill runs in a single context.
It labels its critique as same-context and never claims Goldfish or fresh-context review.
When a task needs repository access or independent reviewers, it says so and points to full EGM on a capable host.

## The Problem

The published OpenAI listing sets `extensions.com.openai.requires_local_executor: true` in `plugin.json`.
ChatGPT on the web cannot run it.
In a Chrome check, the starter prompts opened the desktop app, and EGM did not appear in the ChatGPT Work plugin picker.
People in chat products therefore cannot use EGM, even for document work that needs no repository.

Full EGM also depends on capabilities chat hosts lack: fresh-context subagents, a shell, and repository access.
A chat skill can critique a document in the same context.
It cannot provide independent review and must not imply that it does.

## Name

`egm-in-chat` (with OpenAI `display_name: "EGM for ChatGPT"`) replaces the working names `egm-lite` and `egm-chat`.
The skill targets web chat experiences where it is the only EGM skill exposed inside the ChatGPT plugin.
"Lite" now belongs to the repo-backed single-agent engineering protocol in #460 (#419, #438), which solves a different problem.
Calling this skill `/egm-in-chat` and displaying `EGM for ChatGPT` makes its surface explicit when users invoke the plugin in ChatGPT.

## Goals

- Support a small document workflow: clarify an idea, draft or revise a document, and review it against user-selected goals or lenses.
- Work with files the user supplies and, when the host provides them, connected documents.
- Return results in chat. Change a connected file only when asked, and preserve the source by default.
- Keep source, skill, and test instructions open source and portable.
- Run in ChatGPT Work on the web without local execution.

## Non-Goals

- Repository inspection, `egm-bootstrap`, `egm-drift-report`, code changes, or local CLI delegation.
- Claiming fresh-context review when the host does not provide and verify it.
- Building a hosted EGM service, storing user documents, or adding mandatory MCP or Google OAuth.
- Updating the published plugin listing before the web test and directory eligibility are confirmed.
- Raising problem recall above an unaided model. The evaluation below shows a single reply cannot do this.

## Behavior Rules

The skill must:

1. Label any critique as same-context. Never claim fresh-context, independent, or Goldfish review.
2. Work only from user-supplied text and files, or a connected document app the user chooses.
3. Sort each issue as a blocker, a fix to make while proceeding, or a note. Hold only for a blocker.
4. Reply in a fixed order: decision, blockers, fixes, next step.
5. Treat facts stated in the document as true. Recompute totals and dates from the document's own figures.
6. Treat a broken stated hard limit as a blocker. Do not phrase other fixes as preconditions.
7. Not add requirements the document does not state.
8. Point to full EGM when the task needs repository access or independent reviewers.

Rules 3 to 7 came from the evaluation. Each was kept only when it improved results beyond run-to-run noise without making another measure worse.

## Critical User Journeys

### Review a plan in ChatGPT Work

- **Given:** A user uploads a plan to ChatGPT Work on the web and selects `egm-chat`.
- **When:** The user asks for a review.
- **Then:** The reply gives a proceed-or-hold decision, blockers, fixes, and a next step.
- **Then:** The reply says the review is same-context and makes no independence claim.

### Request work the host cannot do

- **Given:** A user asks `egm-chat` to inspect a repository or run independent reviewers.
- **When:** The skill reads the request.
- **Then:** It explains the missing capability, narrows the task, and points to full EGM on a capable host.

## Evaluation Evidence

The skill was evaluated before this proposal. Results are for skill version 0.3.0.

### Method

- Models ran through the OpenAI Agents SDK in a mode where the model must open the skill file, as in the ChatGPT app.
- 77 cases: 27 hand-written (19 for tuning, 8 held out), 30 blind-spot cases, and 20 trips from the TREK planning benchmark (CC BY 4.0, released August 2026, after the models' training data).
- Each version was compared with no skill on the same model and cases.
- Judges were checked against labels before use. The blocker judge reached TPR 0.90 and TNR 1.00 against three-model proxy labels. The invented-fact judge reached TPR 0.73 and TNR 0.92 against human labels from RAGTruth and SummEdits.
- Twelve rounds tested 33 skill versions.

### Held-out results

gpt-5.5, 8 held-out cases and 10 TREK trips, 2 runs each:

| Measure | v0.3.0 | No skill |
|---|---|---|
| Right decision, held-out cases | 100% | 75% |
| Right decision, TREK trips | 100% | 45% |
| Right decision, flawed plans | 100% | 100% |
| Sound plans with no unsupported blocker | 100% | 0-33% |
| Unsupported blockers per reply (TREK) | 0.05 | 1.95 |
| Real problems found | 100% | 100% |
| Words per reply | 476 | 358 |

Claude Haiku 5.5, 8 held-out cases, 3 runs each:

| Measure | v0.3.0 | No skill |
|---|---|---|
| Right decision | 96% | 58% |
| Right decision, flawed plans | 100% | 92% |
| Sound plans with no unsupported blocker | 89% (99% judge-corrected) | 0% |
| Unsupported blockers per reply | 0.25 | 2.5 |
| Real problems found | 100% | 100% |
| Words per reply | 411 | 478 |

The first prototype instruction set (v0.1.0) scored below no skill: 50% right decisions on Haiku 5.5.

### Findings

- On strong models, the skill mainly fixes over-blocking. Without it, models hold most sound plans for reasons the plan does not support.
- The skill does not find more real problems. Strong models already find 97 to 100% unaided.
- No single-reply instruction raised recall on a small model (gemini-3.5-flash-lite). Two independent fresh reviews raised it only from 77% to 82%, because both tend to miss the same flaws. Extra catches need separate fresh-context reviewers, which is full EGM.
- On gemini-3.5-flash-lite, the skill lets some real problems through: right decisions on flawed plans were 77 to 95%, against 100% with no skill. The skill should recommend a strong model and full EGM Review for decisions users depend on.
- Every activated reply disclosed same-context review. None claimed independent review.

### ChatGPT web pilot

A three-case manual pilot ran on 2026-11-10 in ChatGPT Chat and Work on the web, with an earlier version (0.1.0) installed as a private plugin.
Replies were masked, shuffled, and scored blind.
The skill tied the plain model on five of six pairs and lost one.
No reply invented facts or claimed independent review.
ChatGPT Work listed all packaged skills; the UI did not show whether the skill file was read.
The pilot must be repeated on version 0.3.0 before Stage 2 merges.

### Limits

- Blocker-judge labels come from three models, not people.
- The held-out set is small (8 cases), and the gpt-5.5 check uses 2 runs per case.
- The boundary between a fix and a blocker is a judgment call.
- ChatGPT web runs were not repeated.

## Packaging and Host Visibility

A separate web package is proposed for the first version.
It lives in `chatgpt-web/`, outside `skills/`, with its own manifest and build target, and contains only `egm-in-chat`.
Its manifest omits `requires_local_executor`.
The published desktop package and the `SKILLS` tuple in `scripts/pack_plugin.py` stay unchanged.

### Why the skill stays out of `skills/`

Every supported coding harness reads the shared `skills/` folder, so a skill placed there appears in all of them:

- Claude Code and Codex install from the repository root through `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json`.
- Cursor reads `./skills/` through `.cursor-plugin/plugin.json`.
- The OpenCode adapter installs every folder under `skills/`.
- The website check requires a public page for every folder under `skills/`.

`disable-model-invocation: true` does not hide a skill. All seven published skills already set it.
A folder outside `skills/` is the only option that keeps the skill out of every coding harness without host-specific rules.

### Per-skill product gating (not used in the first version)

Codex reads `policy.products` from `agents/openai.yaml`, with the values `chatgpt`, `codex`, and `atlas`.
In `openai/codex`, CLI, VS Code, Exec, and MCP sessions map to `codex`, and the loader drops a skill whose list excludes the session product.
A skill with `policy.products: ["chatgpt"]` is therefore hidden in Codex.
Whether ChatGPT on the web reads the same field is not verified.
A later version could use this field to ship one OpenAI plugin for both hosts, once the web behavior is tested.

## Alternatives Considered

### Full skill set plus `egm-chat` in one web package

A preview bundled the seven skills with `egm-chat`.
ChatGPT Work listed all eight, but the full skills need capabilities the web host lacks.
Users could start a workflow that cannot finish. Rejected for the experiment.

### Add `egm-chat` to the published package

This would change published `/egm` behavior, which #414 rules out.

### One OpenAI plugin with per-skill product gating

One bundle could hold all eight skills, with `policy.products` hiding each skill on the wrong host.
It would need `requires_local_executor` removed from the published listing, and it depends on web behavior that is not verified.
It also leaves the skill visible in Claude Code, Cursor, and OpenCode. Deferred.

### Simulate Goldfish reviewers inside one reply

A five-angle in-reply review pass modeled on EGM's lenses was tested in round 7. It did not raise recall and added length.
It would also blur the line between same-context and independent review.

## Required Tests (Stage 2)

- `chatgpt-web/` with `plugin.json`, and `chatgpt-web/skills/egm-in-chat/` with `SKILL.md`, `TEST.md`, `test_scenarios.yaml`, `agents/openai.yaml`, and `assets/icon.svg`, following `skills/egm-review/`.
- Unit tests check the new skill's frontmatter, load limit, scenarios, and icon, because the shared tests only scan `skills/`.
- Unit tests check that the web package omits `requires_local_executor`, and that the Claude and OpenAI desktop bundles do not contain `egm-in-chat`.
- `ruff check .` and `python -m pytest tests/unit` pass.
- Offline package validation passes for the web package.
- A clean ChatGPT Work web test completes brainstorm, draft, and document review from user-provided content, with the package version and observed capabilities recorded.
- Connected-document use is tested only when the host exposes it. Uploads remain the fallback.

## Open Questions

- A maintainer must approve the scope and the `egm-in-chat` (`EGM for ChatGPT`) name.
- Whether `chatgpt-web/` is the right home for the web package's manifest and build target.
- Whether the web package can be listed separately once directory eligibility is confirmed.
