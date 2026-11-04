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
*   Incremental refresh driven by a dependency fingerprint.
*   Never overwrite an explainer a person wrote or edited.
*   Reuse of `/egm-bootstrap`'s traversal and safety gate, and of the
    `egm-comprehension` persona.

**Non-Goals**

*   Reading or summarising code.
*   Export to HTML, Notion or slides.
*   Editing contracts, apart from the opt-in pointer line.
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

    Human->>Skill: /egm-explain path [scope, audience, refresh, readme_pointer]
    Skill->>Tree: Find EGM contracts (stop if none: run /egm-bootstrap)
    Skill->>Skill: Decide own explainer vs fold; skip human-owned explainers; safety gate above 15
    loop Bottom-up, siblings in parallel batches
        Skill->>Writers: Contract + child summaries + templates
        Writers->>Tree: Write EXPLAINER.md with fingerprint:PENDING
        Writers-->>Skill: Summary, glossary terms, gaps
    end
    Skill->>Tree: Write repository explainer and glossary
    opt readme_pointer is true
        Skill->>Tree: Add pointer under each README H1
    end
    Skill->>Readers: Fact-check (explainer + sources), then plain-language (explainer only)
    Readers-->>Skill: Return findings without modifying files
    Skill->>Tree: Apply source-supported fixes
    Skill->>Tree: Finalize fingerprints, bottom-up
    Skill->>Human: Report written, folded, skipped, gaps, kept-as-is findings
```

The skill finds the contracts, leaves human-owned explainers alone, writes
explainers from the leaves up, writes the repository explainer, optionally adds
README pointers, runs two reviewers, applies their supported fixes, records
each explainer's fingerprint last, and reports.

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
| `readme_pointer` | `false` | `true` adds one line under each contract's H1 linking to its explainer. Off by default for teams that treat READMEs as human-owned. |

### Which Directories Get an Explainer

A directory gets its own explainer when it is the repository root, when its
contract describes something a person would recognise (a feature, an external
system, a scheduled job, money spent, data people read), or when it has child
contracts. A **pass-through** blueprint, with exactly one child contract and
nothing of its own, folds. Everything else folds into the nearest parent's
"What's inside" table.

### Existing Explainers

The skill owns a file only when it can prove it wrote it and nobody has changed
it since. Before writing, it reads any file already at the target path:

| What is there | Treated as | What the skill does |
| :------------ | :--------- | :------------------ |
| No file | Free | Writes a new explainer. |
| A file with no `egm-explain` footer | Human-written | Never writes, moves or renames it. The parent's "What's inside" links to it as is, and the report lists it under "Skipped: human-written". It is not a source, so no other explainer cites its claims. |
| A footer whose `output` hash no longer matches the file | Edited by hand | Same as human-written, including on `refresh`. The report lists it under "Skipped: edited by hand". |
| A footer with `fingerprint:PENDING` | The skill's own unfinished file | Overwrites it. |
| A footer whose `output` hash matches | The skill's own file | Rewrites it when its fingerprint is stale; otherwise leaves it unchanged. |

To hand a skipped directory back to the skill, a person deletes or renames the
file. The skill never removes a README pointer line; turning `readme_pointer`
off leaves existing lines in place.

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

The contract hash alone is not a sufficient refresh key. Each explainer records
a deterministic fingerprint of everything it was built from.

**Where it lives.** In the explainer's last line, and nowhere else:

```
<!-- egm-explain v1 source: <contract path> fingerprint:sha256:<64 hex> output:sha256:<64 hex> -->
```

Keeping it in the file means it moves, is reviewed and is versioned with the
explainer, and there is no separate state file to fall out of step. A
sidecar manifest was considered and rejected for that reason; the cost is that
a refresh can say an explainer is stale but not which input changed.

**What it covers.** The fingerprint is the SHA-256 of a sorted, newline-separated
list of records, one per input:

*   `template <version>` for the explainer template;
*   `setting <name>=<value>` for `audience`, `scope`, `target_filename`,
    `contract_filename` and `readme_pointer`;
*   `contract <path> <sha256>` for its own contract and the contract of every
    directory folded into it;
*   `child <path> <sha256>` for each child explainer, as written, footer
    included;
*   `extra <path> <sha256>` for each named extra source (repository explainer
    only).

Because a child's bytes include its own footer, any change below an explainer
changes the explainer's fingerprint, so ancestors go stale without a separate
rule. An added, removed or changed input, or a changed setting, makes the
explainer stale. A changed `audience` regenerates the explainer from its
sources rather than editing it, so no internal detail survives into a
shareable result. A missing input, or a footer that cannot be parsed, also
counts as stale.

`output` is the SHA-256 of the explainer with its footer line removed. It is
how the skill detects a hand edit (see [Existing Explainers](#existing-explainers)).

**When it is finalized.** Last. Writers leave `fingerprint:PENDING`, and an
explainer's fingerprint and `output` hash are computed only after all of these
have finished for it:

1.  the writer's draft;
2.  the README pointer, when `readme_pointer` is true, so the contract is
    hashed as it will stay (hashing before the pointer made every explainer
    look stale in the trial run);
3.  both reviews, and every fix the coordinator accepts from them;
4.  the mechanical checks: links, Mermaid types and line limits.

Finalization runs bottom-up after all fixes across the tree have landed: a
parent is finalized only after every child it depends on, since the child's
finished bytes are one of its inputs. If any step fails or the run stops, the
affected explainers and their ancestors keep `fingerprint:PENDING`, and the
next run treats them as stale. Any change made to an explainer after its
footer is written is, by definition, a hand edit.

### Goldfish Review

1.  **Fact check** (an inline reviewer prompt in `SKILL.md`, not a persona
    under `agents/`): sees the explainer and only the sources its writer was
    given, meaning its contracts, child explainers and named extra sources, with
    no repository or code access. It reports any claim, number, node or arrow
    those sources do not support, and any shareable-mode leak.
    `egm-codebase-details` is not used: its instructions require reading code,
    which this skill deliberately leaves out.
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

## Decisions

Settled with maintainers on [#228](https://github.com/google/elephant-goldfish-model/pull/228):

1.  The default filename stays `EXPLAINER.md`.
2.  The README pointer line is opt-in (`readme_pointer`, default `false`).
3.  The fact checker stays inline, reading only the supplied sources, rather
    than becoming a persona or reusing `egm-codebase-details`.

## Implementation Files

| File Path | Type | Purpose & Reason for Existence |
| :-------- | :--- | :----------------------------- |
| `skills/egm-explain/SKILL.md` | Skill Definition | Implements `/egm-explain`: discovery, folding, batched writers, diagrams, glossary, linking, hashing, review and verification. |
| `skills/egm-explain/references/templates.md` | Templates | Package and repository explainer outlines. |
| `skills/egm-explain/TEST.md` | Test Plan | Points to `pytest tests/unit` and lists six manual scenarios. |
| `skills/egm-explain/test_scenarios.yaml` | Evaluation Scenarios | No contracts, diagram grounding, pass-through fold, hash after pointer, shareable redaction, refresh after child or extra-source changes, audience changes, read-only reviewer findings, human-written and hand-edited explainers left alone, and the README pointer added only when `readme_pointer` is true. |
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
