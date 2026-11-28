# Surface Relevant Technical Constraints During `egm-brainstorm`

* **Status:** Proposed (Stage 1 Design Doc, Refs #318)
* **Primary Component:** [`skills/egm-brainstorm/SKILL.md`](../../skills/egm-brainstorm/SKILL.md)

## Overview

During early ideation in `/egm-brainstorm`, developers often know the product
goal but do not yet know which technical standards, provider limits, storage
guarantees, or failure modes govern the design. Discovering those conditions
manually takes research before architectural trade-offs can be evaluated.

This design adds a bounded constraint-discovery step to the Elephant workflow in
`egm-brainstorm` after problem clarification establishes project context and
before Step 2 spawns the Goldfish swarm. The step reuses the host's existing
file-reading and web-search capabilities without adding a new skill, persona, or
external service.

## Goals vs. Non-Goals

### In-Scope Goals

* Proactively identify decision-relevant technical questions and read
  supporting primary sources (specifications, provider contracts, and relevant
  public incident reports or postmortems) from feature and project context.
* Distinguish confirmed applicable constraints, conditional findings, and
  recommendations so unknown deployment assumptions or general advice are never
  presented as mandatory requirements.
* Record pattern preconditions explicitly: when a finding draws on a pattern
  from another system, state which preconditions are met, unmet, or unknown in
  the target project.
* Keep findings selective and research bounded; allow cases that need no
  external research, and distinguish inaccessible sources or unfinished
  investigation from finding no relevant issues.
* Preserve material findings and source citations in `concepts_brief.md` through
  Goldfish review and handoff to `/egm-draft`, with unit tests and packaged-runtime
  updates in Stage 2.

### Out-of-Scope Non-Goals

* Adding new slash commands, reviewer personas, search services, browser
  engines, or required paid providers.
* Direct-to-draft research, rescanning existing design documents, persistent
  local caches, or background monitoring.
* Application code changes, automated architectural decisions, exhaustive
  discovery, or compliance certification.
* Claiming verified support across all hosts before live validation; initial
  live validation targets one capable Codex environment.

## Workflow Placement

The constraint-discovery step runs inside Step 1 of `egm-brainstorm`, after
multi-turn problem drilling has established the target system, runtime
dependencies, and operational context, and before the Step 1.3 Readiness
Checkpoint Gate:

1. **Context Inspection**: Read local project configuration, manifests, and
   referenced design or architecture files already in scope to determine
   versions, storage engines, concurrency models, and external providers.
2. **Bounded Primary-Source Research**: When project context surfaces
   unverified technical conditions (for example, multi-worker database
   locking, external provider rate or delivery guarantees, or known failure
   modes for the same class of system), form a small, bounded set of research
   questions and inspect primary sources using host capabilities. Skip external
   research when local context already answers the question or no external
   dependency is involved.
3. **Hypothesis & Gate**: Incorporate material findings into the anchored
   working hypothesis presented at the Step 1.3 Readiness Checkpoint Gate so
   the user can confirm, refine, or rule out assumptions before Goldfish
   subagents are spawned.

Existing Goldfish isolation and user decision gates remain unchanged: Goldfish
lenses in Step 2 still run in fresh contexts without parent chat history and
receive only the synthesized context and brief.

## Finding Format & Applicability Rules

Each material finding recorded in `concepts_brief.md` under `## Analysis`
connects four fields:

* **Project evidence**: The requirement, code path, or configuration file in
  the repository that makes the condition relevant.
* **Source evidence**: The primary-source section actually read (specification,
  provider contract, or incident report) and its applicable version or date.
* **Applicability**: Confirmed conditions, unknown assumptions, and what would
  establish or rule out relevance. When borrowing a pattern from another
  system, list its key preconditions and mark each as met, unmet, or unknown
  in this project.
* **Design implication**: The specific question, invariant, or trade-off the
  author should weigh before drafting.

### Handling Uncertainty & Read Failures

* **No external research needed**: Record `"No external constraint research
  required"` with a one-line reason when the feature is self-contained.
* **Unknown version or deployment assumption**: Mark the constraint
  `conditional` and surface the missing assumption as an open question rather
  than a mandatory requirement.
* **Inaccessible or failed source read**: Record the attempted source and
  failure reason under unfinished investigation; never infer or fabricate
  contents from an unread URL, and never equate a failed read with `"no
  issues found"`.

## Handoff to `/egm-draft` and `/egm-review`

Material constraint findings remain in `concepts_brief.md` (`## Analysis` and
`## Key Decisions & Staging for Next Steps`). Because `/egm-draft` ingests
`concepts_brief.md` as its primary intake source, verified project/source
evidence and unresolved conditional questions carry forward into the formal
design document and subsequent `/egm-review` stages without re-running
discovery.

## Validation Plan (Stage 2)

1. **Offline Unit Checks**: Verify `skills/egm-brainstorm/SKILL.md` structure,
   frontmatter, load-limit compliance, and packaged runtime bundles via
   `python -m pytest tests/unit`.
2. **Controlled Scenario Fixtures**: Evaluate fixture prompts covering (a)
   proactive constraint discovery without user-supplied URLs, (b) self-contained
   no-research cases, (c) unknown-version conditional handling, and (d)
   failed-read reporting.
3. **Live Codex Probe**: Run an opt-in comparison in one capable Codex
   environment checking actual primary-source reads, applicability accuracy,
   and preservation in `concepts_brief.md`. Support on other harnesses remains
   unclaimed until tested separately.
