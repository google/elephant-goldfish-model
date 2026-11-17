# EGM in Chat: a document-first skill for chat hosts

- **Author:** @n3wth
- **Status:** Proposed. Maintainer scope approval is pending.
- **Date:** 2026-11-16
- **Scope issue:** #414
- **Related:** #460, #419, #438 (`egm-lite` for repo-backed engineering), #371 (24 KB skill load limit)
- **Earlier names:** `egm-lite`, `egm-chat`. This design proposes `/egm-in-chat` (`EGM for ChatGPT` in the OpenAI UI).

## Overview

Add an `egm-in-chat` skill (`display_name: "EGM in Chat"`) to the existing EGM OpenAI plugin for ChatGPT on the web and desktop.
It helps a user shape an idea, draft a plan, and review a document from chat context and user-supplied files.
The existing `egm-openai.zip` contains this skill alongside the seven full EGM skills, under the same `egm` identity and listing. Its source lives in `openai/skills/`, outside the shared coding-harness skills.

The skill runs in a single context.
It labels its critique as same-context and never claims Goldfish or fresh-context review.
When a task needs repository access or independent reviewers, it checks the tools actually available in that chat and points to the appropriate full EGM skill. A web or desktop label alone does not establish those capabilities.

## The Problem

The published OpenAI listing sets `extensions.com.openai.requires_local_executor: true` in `plugin.json`.
ChatGPT on the web cannot run it.
In a Chrome check, the starter prompts opened the desktop app, and EGM did not appear in the ChatGPT Work plugin picker.
People in chat products therefore cannot use EGM, even for document work that needs no repository.

Full EGM depends on capabilities that are not available in every chat: fresh-context subagents, artifact access, and, for repository workflows, shell and repository access.
A chat skill can critique a document in the same context.
It cannot provide independent review and must not imply that it does.

## Name

`egm-in-chat` (with OpenAI `display_name: "EGM in Chat"`) replaces the working names `egm-lite` and `egm-chat`.
The skill is the document-first entry point within the existing EGM plugin. "Lite" now belongs to the repo-backed single-agent engineering protocol in #460 (#419, #438), which solves a different problem.
The plugin keeps its existing name and listing; the skill displays as `EGM in Chat`.

## Goals

- Support a small document workflow: clarify an idea, draft or revise a document, and review it against user-selected goals or lenses.
- Work with files the user supplies and, when the host provides them, connected documents.
- Return results in chat. Change a connected file only when asked, and preserve the source by default.
- Keep source, skill, and test instructions open source and portable.
- Run in ChatGPT Work on the web without local execution.
- Ship one OpenAI plugin package and identity for web and desktop, with behavior selected from observed capabilities.
- Preserve the full skills' artifact requirements and independent-review guarantees.

## Non-Goals

- Repository inspection, `egm-bootstrap`, `egm-drift-report`, code changes, or local CLI delegation.
- Claiming fresh-context review when the host does not provide and verify it.
- Building a hosted EGM service, storing user documents, or adding mandatory MCP or Google OAuth.
- Publishing the revised package before combined-package web and desktop tests and directory eligibility are confirmed.
- Adding a second ChatGPT plugin, a web-only ZIP, or a hosted reviewer service.
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
8. Check available tools when a task needs repository access or independent reviewers. Route to full EGM only when its required capabilities exist; otherwise explain the missing capability and offer same-context document work.

Rules 3 to 7 came from the evaluation. Each was kept only when it improved results beyond run-to-run noise without making another measure worse.

## Critical User Journeys

### Review a plan in ChatGPT Work

- **Given:** A user uploads a plan to ChatGPT Work on the web and selects `egm-in-chat` from EGM.
- **When:** The user asks for a review.
- **Then:** The reply gives a proceed-or-hold decision, blockers, fixes, and a next step.
- **Then:** The reply says the review is same-context and makes no independence claim.

### Request work the host cannot do

- **Given:** A user asks `egm-in-chat` to inspect a repository or run independent reviewers, but the required tools are absent.
- **When:** The skill reads the request.
- **Then:** It explains the missing capability, narrows the task, and points to full EGM on a capable host.

### Use full EGM from the same plugin

- **Given:** The same OpenAI package is installed in a chat with readable bundled files, writable artifacts, and verified fresh-context subagents.
- **When:** The user requests independent review.
- **Then:** EGM routes to `egm-review` and retains its isolation checks. A document-only request can still use `egm-in-chat` in that chat.
- **Then:** Repository operations additionally require access to the requested repository and command execution. The skill must not infer either from the desktop label.

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

Use the existing `--target openai` build and `egm-openai.zip`. Keep the `egm` identity, version scheme, marketplace entry, and public listing. Do not create a second plugin manifest or `chatgpt-web` target.

Store the document skill in `openai/skills/egm-in-chat/`. The OpenAI packer places its runtime files at `skills/egm-in-chat/` alongside the seven canonical skills, using the same path-safety and reproducibility checks. The Claude build and repository-based coding-harness skill discovery remain unchanged; repository installs still expose the seven canonical skills.

Remove `requires_local_executor` from both OpenAI manifest locations. Update the listing description to distinguish document work from independent review. This prepares a candidate; it does not publish an update to the current desktop-only listing.

All full skills already read `docs/codex.md` before starting on OpenAI hosts. That document adds a capability check before any workflow intake: readable bundled resources and writable artifacts for full EGM; verified fresh-context native subagents for any Goldfish stage; repository and command access for repository operations. If a requirement is absent, stop that workflow, name the missing capability, and offer `egm-in-chat` when it is installed. Do not silently replace an independent review with same-context critique.

The document skill works on either surface. It checks current tools before referring a repository or independent-review request to full EGM. Neither skill selection nor routing depends on the word "web" or "desktop".

### Why the skill stays out of `skills/`

Every supported coding harness reads the shared `skills/` folder, so a skill placed there appears in all of them:

- Claude Code and Codex install from the repository root through `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json`.
- Cursor reads `./skills/` through `.cursor-plugin/plugin.json`.
- The OpenCode adapter installs every folder under `skills/`.
- The website check requires a public page for every folder under `skills/`.

`disable-model-invocation: true` does not hide a skill. All seven published skills already set it.
Keeping the source outside `skills/` lets the OpenAI archive include it without adding it to other harnesses.

### Per-skill product gating (not used in the first version)

Codex reads `policy.products` from `agents/openai.yaml`, with the values `chatgpt`, `codex`, and `atlas`.
In `openai/codex`, CLI, VS Code, Exec, and MCP sessions map to `codex`, and the loader drops a skill whose list excludes the session product.
A skill with `policy.products: ["chatgpt"]` is therefore hidden in Codex.
Whether ChatGPT on the web reads the same field is not verified.
The combined package does not depend on this field. Product labels do not establish whether an individual chat has repository access or fresh-context reviewers.

## Alternatives Considered

### Separate web plugin

A separate package avoids exposing full skills in restricted chats, but creates a second installation, identity, and release path. Oliver selected one OpenAI plugin for web and desktop instead. Capability checks must prevent unsupported full workflows from starting.

### Add the document skill to shared `skills/`

This would expose the skill in every coding harness. Use an OpenAI-only source directory and include it in the existing OpenAI build instead.

### One OpenAI plugin with per-skill product gating

Web behavior is unverified, and filtering by product cannot replace checks of the current chat's tools. It is not required for the first combined package.

### Simulate Goldfish reviewers inside one reply

A five-angle in-reply review pass modeled on EGM's lenses was tested in round 7. It did not raise recall and added length.
It would also blur the line between same-context and independent review.

## Required Tests (Stage 2)

- `openai/skills/egm-in-chat/` contains `SKILL.md`, `TEST.md`, `test_scenarios.yaml`, `agents/openai.yaml`, and `assets/icon.svg`, following `skills/egm-review/`. There is no separate plugin manifest.
- Unit tests check the new skill's frontmatter, load limit, scenarios, and icon, because the shared tests only scan `skills/`.
- Unit tests check that the existing OpenAI archive has the same `egm` identity, contains all eight skills and their runtime assets, omits `requires_local_executor` in both manifests, and is reproducible. The Claude archive still has seven skills. Missing or symlinked document-skill files fail before output.
- `ruff check .` and `python -m pytest tests/unit` pass.
- Offline package validation passes for the combined OpenAI package.
- Before merge or publication, install the exact same archive in clean ChatGPT web and desktop chats. Record archive checksum, package version, host version or date, installation result, skill discovery, and observed capabilities separately for each surface.
- On each surface, complete document brainstorm, draft, and same-context review through `egm-in-chat`. Verify a full-skill request with missing tools names the limitation and offers the document skill without claiming independent review.
- On a capable desktop chat, run `egm-brainstorm`, `egm-draft`, and `egm-review` end to end and verify native fresh-context reviewer evidence. Record `not run` for any missing check. Installation or unit tests alone do not satisfy this gate.
- Connected-document use is tested only when the host exposes it. Uploads remain the fallback.

## Open Questions

- A maintainer must approve the revised scope and `egm-in-chat` name.
- Combined-package installation, routing, and native workflow behavior must be verified on web and desktop before merge.
- Confirm directory eligibility for the revised existing listing before publication.
