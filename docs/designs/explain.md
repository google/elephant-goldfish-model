# EGM Explainers (Plain-Language Companions to README Contracts)

*   **Author:** Barkha Gvalani ([@barkhagvalani](https://github.com/barkhagvalani))
*   **Status:** Draft
*   **Date:** 2026-10-28
*   **Issue:** Refs [#214](https://github.com/google/elephant-goldfish-model/issues/214)

--------------------------------------------------------------------------------

## Overview

The **EGM Explain Skill** (`/egm-explain`) writes a plain-language
`EXPLAINER.md` beside each `README.md` contract that `/egm-bootstrap` produced,
plus one repository explainer with a shared glossary. Contracts stay the source
of truth for agents and for engineers changing code. Explainers are for the
people around the code: product managers, investors, operators and new hires.

An explainer is built **only from contracts**, never from code. Contracts have
already been checked against the code, so an explainer inherits that accuracy,
and a gap in an explainer points to a gap in the contract.

## The Problem

1.  **Contracts are written for agents.** Interface signatures, invariants and
    symbol citations are what an agent needs. A non-engineer reading
    `src/intake/README.md` meets reason codes, file names and test commands
    before learning that the directory turns forwarded emails into requests.

2.  **Hand-written overviews drift silently.** Teams that write a summary by
    hand have nothing tying it to the contracts, so it goes stale the first
    time the code changes, and no EGM skill notices.

3.  **One audience's document pollutes the other's.** Putting a plain-language
    section inside the contract spends agent context on prose agents do not
    need, and `/egm-bootstrap` upserts would overwrite or fight with it.

## Goals and Non-Goals

**Goals**

*   One explainer per meaningful contract, plus a repository explainer and
    glossary.
*   Every fact traceable to a contract, a child explainer, or (for the
    repository explainer only) a named extra source.
*   Mermaid diagrams that render on GitHub, used only where they help.
*   Incremental refresh driven by contract hashes.
*   Reuse of `/egm-bootstrap`'s traversal and safety gate, and of the
    `egm-comprehension` persona.

**Non-Goals**

*   Reading or summarising code.
*   Export to HTML, Notion or slides.
*   Editing contracts beyond one pointer line.
*   Replacing `/egm-drift-report`.

## System Architecture & Workflow

```mermaid
sequenceDiagram
    autonumber
    actor Human as Engineer
    participant Skill as egm-explain
    participant Writers as Writer subagents
    participant Readers as Goldfish reviewers
    participant Tree as Repository tree

    Human->>Skill: /egm-explain path [scope, audience, refresh]
    Skill->>Tree: Find EGM contracts (stop if none: run /egm-bootstrap)
    Skill->>Skill: Decide own explainer vs fold; safety gate above 15
    loop Bottom-up, siblings in parallel batches
        Skill->>Writers: Contract + child summaries + templates
        Writers->>Tree: Write EXPLAINER.md with sha256:PENDING
        Writers-->>Skill: Summary, glossary terms, gaps
    end
    Skill->>Tree: Write repository explainer and glossary
    Skill->>Tree: Add pointer under each README H1, then fill hashes
    Skill->>Readers: Fact-check (explainer + sources), then plain-language (explainer only)
    Readers-->>Skill: Return findings without modifying files
    Skill->>Tree: Apply source-supported fixes
    Skill->>Human: Report written, folded, gaps, kept-as-is findings
```

The skill finds the contracts, writes explainers from the leaves up, writes the
repository explainer, links each pair, records hashes, runs two reviewers, and
reports.

### Inputs

| Input | Default | Purpose |
| :---- | :------ | :------ |
| `path` | required | Repository root or subtree. |
| `scope` | `all` | `all`, `repo` (root only) or `package` (one directory). |
| `audience` | `internal` | `shareable` leaves out hosts, internal emails, account names and ticket numbers. |
| `refresh` | `false` | Rewrite explainers whose source or output-configuration fingerprint changed, plus ancestors. |
| `target_filename` | `EXPLAINER.md` | Output name. |
| `contract_filename` | `README.md` | Use `EGM.md` for trees bootstrapped with that name. |
| `extra_sources` | none | Human-maintained documents the repository explainer may cite, such as a runbook. |

### Which Directories Get an Explainer

A directory gets its own explainer when it is the repository root, when its
contract describes something a person would recognise (a feature, an external
system, a scheduled job, money spent, data people read), or when it has child
contracts. A **pass-through** blueprint, with exactly one child contract and
nothing of its own, folds. Everything else folds into the nearest parent's
"What's inside" table.

### Explainer Shape

Package explainers follow one outline: In one sentence; What it does; an
optional diagram; Who or what uses it; What it touches; What it costs; Rules it
always keeps; When something goes wrong; What's inside; and a footer linking
the contract. The repository explainer adds What people see, Data in and out,
Schedule, Costs and guardrails, and the Glossary. Package explainers aim for
about 60 lines, with 80 as the ceiling; the repository explainer is exempt
because it carries the glossary.

### Diagram Rules

| Shape in the contract | Mermaid type |
| :-------------------- | :----------- |
| 3+ steps, or data moving between systems | `flowchart LR` |
| States something moves through | `stateDiagram-v2` |
| Ordered requests among 3+ parties | `sequenceDiagram` |
| Scheduled jobs | A table (preferred) or `timeline` |

Every node and arrow names something the contract names; at most 12 nodes; one
plain sentence under each diagram for viewers that do not render Mermaid. A
parent links to a child's diagram instead of repeating it.

### Freshness

Each explainer ends with
`<!-- egm-explain source: <contract path> sha256:<12 hex> -->`. Writers leave
`sha256:PENDING`; the hash is taken **after** the pointer line is added to the
contract. Hashing first would make every explainer look stale on the next
refresh, which the trial run caught.

The contract hash alone is not a sufficient refresh key. Record a deterministic
fingerprint covering the contract content, child explainer content, named extra
source content, and effective output settings (`audience`, filenames, scope,
and template version). Added, removed, or changed dependencies invalidate the
explainer and its ancestors. A changed audience must invalidate an existing
internal explainer before producing a shareable result. Missing dependencies
or an incomplete fingerprint require regeneration rather than a fresh result.

### Goldfish Review

1.  **Fact check** (general reviewer, explainer plus its sources): reports
    any claim, number, node or arrow the sources do not support, and any
    shareable-mode leak.
2.  **Plain-language reader** (`egm-comprehension`, explainer only): reports
    what it could not follow.

Both reviewers are read-only Goldfish agents. They return findings to the
coordinator, which applies source-supported fixes. Fact fixes land first.
A reader's suggested rewrite often guesses at facts it
cannot see, so each one is checked against the sources before it is applied;
rewrites that would need a missing fact are reported as "kept as is" and added
to the gaps.

### Cost Control

One writer per directory and two reviewers per explainer would mean about 45
subagents for a 15-explainer tree. Writers and reviewers take 2 to 5 sibling
directories each and treat each one on its own; a reviewer still sees only what
its role allows.

## Evidence from a Trial Run

The draft skill ran on a production sourcing app with 20 bootstrapped contracts.

| Measure | Result |
| :------ | :----- |
| Explainers written | 15 (10 with diagrams) |
| Directories folded | 5: a pass-through `src/`, constants, migrations, two frontend data folders |
| Package explainer length | 45 to 74 lines, excluding diagrams |
| Fact-check corrections | 39 claims, mostly overstatements of the contract |
| Plain-language findings | About 90; about 70 applied, 20 kept for lack of a contract fact |
| Subagents | 20, batched |
| Mechanical checks | All links resolve, all diagram types valid, all hashes match |

The run led to eight design changes, all reflected above: hash after the
pointer, fold pass-through blueprints, `extra_sources` for runbook facts, the
80-line ceiling, checking reader rewrites against sources, a glossary covering
every linked term, batched subagents, and gaps grouped by contract.

## Alternatives Considered

| Alternative | Why not |
| :---------- | :------ |
| A plain-language section inside each README | Spends agent context on prose agents do not need, and bootstrap upserts would fight with it. |
| Generate explainers from code | Duplicates `/egm-bootstrap` and loses the contract's verified accuracy. |
| A flag on `/egm-bootstrap` | Different audience, different reviewers, and a different refresh cadence; reusing bootstrap's traversal gets the benefit without the coupling. |
| One repository overview only | No entry point at the folder level, where people land from GitHub. |

## Open Questions

1.  Is `EXPLAINER.md` the right default filename?
2.  Should the README pointer line be opt-in?
3.  Should the fact checker become its own persona under `agents/`, or reuse
    `egm-codebase-details` with an explainer-specific prompt?

## Implementation Files

| File Path | Type | Purpose & Reason for Existence |
| :-------- | :--- | :----------------------------- |
| `skills/egm-explain/SKILL.md` | Skill Definition | Implements `/egm-explain`: discovery, folding, batched writers, diagrams, glossary, linking, hashing, review and verification. |
| `skills/egm-explain/references/templates.md` | Templates | Package and repository explainer outlines. |
| `skills/egm-explain/TEST.md` | Test Plan | Points to `pytest tests/unit` and lists six manual scenarios. |
| `skills/egm-explain/test_scenarios.yaml` | Evaluation Scenarios | No contracts, diagram grounding, pass-through fold, hash after pointer, shareable redaction, refresh after child or extra-source changes, audience changes, and read-only reviewer findings. |
| `skills/egm-explain/assets/icon.svg` | Icon | Speech bubble in the create palette (`#1b6ef3` / `#7cacf8`). |
| `skills/egm-explain/agents/openai.yaml` | Host Metadata | Display name, description and icon for OpenAI hosts. |

Registering the skill also touches `scripts/pack_plugin.py`,
`tests/unit/test_harnesses.py`, `tests/unit/test_packaging.py`, `README.md`,
`docs/designs/skill_icons.md` and the regenerated `distributions/claude`.

## References

*   [Bootstrap design](bootstrap.md), whose traversal and safety gate this
    skill reuses.
*   [Drift report design](drift_report.md), which keeps the contracts
    themselves current.
