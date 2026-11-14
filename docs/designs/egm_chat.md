# EGM Chat: a document-first skill for chat hosts

- **Author:** @n3wth
- **Status:** Proposed. Maintainer scope approval is pending.
- **Date:** 2026-11-13
- **Scope issue:** #414
- **Earlier name:** `egm-lite`. This design proposes `egm-chat`.

## Overview

Add a separate `egm-chat` skill for chat hosts that have no local executor, such as ChatGPT Chat and Work on the web.
It helps a user shape an idea, draft a plan, and review a document from chat context and user-supplied files.
It ships in its own package, so published `/egm` behavior does not change.

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

`egm-chat` replaces the working name `egm-lite`.
The skill targets chat experiences.
"Lite" suggests a reduced copy of EGM, which invites comparison with independent review that the skill cannot make.

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

## Packaging

Option 1 is proposed: a separate web package with its own manifest and build target, containing only `egm-chat`.
Its manifest omits `requires_local_executor`.
The published desktop package and its `SKILLS` tuple in `scripts/pack_plugin.py` stay unchanged during the experiment.

## Alternatives Considered

### Full skill set plus `egm-chat` in one web package

A preview bundled the seven skills with `egm-chat`.
ChatGPT Work listed all eight, but the full skills need capabilities the web host lacks.
Users could start a workflow that cannot finish. Rejected for the experiment.

### Add `egm-chat` to the published package

This would change published `/egm` behavior, which #414 rules out.

### Simulate Goldfish reviewers inside one reply

A five-angle in-reply review pass modeled on EGM's lenses was tested in round 7. It did not raise recall and added length.
It would also blur the line between same-context and independent review.

## Required Tests (Stage 2)

- `skills/egm-chat/` with `SKILL.md`, `TEST.md`, `test_scenarios.yaml`, `agents/openai.yaml`, and `assets/icon.svg`, following `skills/egm-review/`.
- Existing unit tests for packaging, frontmatter, load limits, style and boundaries, and scenario coverage pass for the new skill.
- `ruff check .` and `python -m pytest tests/unit` pass.
- Offline package validation passes for the web package.
- A clean ChatGPT Work web test completes brainstorm, draft, and document review from user-provided content, with the package version and observed capabilities recorded.
- Connected-document use is tested only when the host exposes it. Uploads remain the fallback.

## Open Questions

- A maintainer must approve the scope and the `egm-chat` name.
- Where the web package's manifest and build target should live.
- Whether the web package can be listed separately once directory eligibility is confirmed.
