# EGM Explainers (Plain-Language Companions to README Contracts)

*   **Author:** Barkha Gvalani ([@barkhagvalani](https://github.com/barkhagvalani))
*   **Status:** Draft
*   **Date:** 2026-10-28
*   **Issue:** Refs [#214](https://github.com/google/elephant-goldfish-model/issues/214)

--------------------------------------------------------------------------------

## Overview

The **EGM Explain Skill** (`/egm-explain`) writes a plain-language
`EXPLAINER.md` beside the `README.md` contracts that `/egm-bootstrap` produced,
except for directories that fold into a parent, plus one repository explainer
with a glossary. EGM is the [Elephant-Goldfish Model](../../README.md),
and a Goldfish is a reviewer that runs in a fresh context with no conversation
history. Contracts stay the source of truth for agents and for engineers
changing code. Explainers are for the people around the code: product
managers, operators and new hires.

An explainer is built from contracts, child explainers and, for the repository
explainer, named extra sources. It is never built from code. Its accuracy is
only as good as those sources: an explainer can be faithful to a contract that
has drifted. A fact checker compares each explainer with its sources, and the
report recommends `/egm-drift-report` first. A missing fact is reported as a
gap, which may point to a gap in the contract.

## The Problem

1.  **Contracts are written for agents.** Interface signatures, invariants and
    symbol citations are what an agent needs. A non-engineer reading
    `src/intake/README.md` meets reason codes, file names and test commands
    before learning that the directory turns forwarded emails into requests.

2.  **Hand-written overviews have no link to the contracts.** Nothing ties a
    hand-written summary to the contracts, so no EGM skill can detect when it
    goes stale.

3.  **One audience's document pollutes the other's.** Putting a plain-language
    section inside the contract spends agent context on prose agents do not
    need, and `/egm-bootstrap` updates could overwrite it. A one-line pointer
    costs little if it is lost; a whole section does not.

## Goals and Non-Goals

**Goals**

*   One explainer for each directory selected under
    [Which Directories Get an Explainer](#which-directories-get-an-explainer),
    plus a repository explainer and glossary.
*   Every fact about the system traceable to a contract, a child explainer, or
    (for the repository explainer only) a named extra source.
*   Mermaid diagrams using types GitHub renders, used only when the contract has
    a shape listed in [Diagram Rules](#diagram-rules).
*   Incremental refresh driven by a dependency fingerprint.
*   Never overwrite an explainer whose footer is missing, unreadable, or does
    not match its content.
*   Follow the same safety-gate approach as `/egm-bootstrap`, and reuse the
    `egm-comprehension` persona.

**Non-Goals**

*   Reading or summarising code.
*   Export to HTML, Notion or slides.
*   Editing contracts, apart from the opt-in pointer line.
*   Replacing `/egm-drift-report`.
*   Alerting on stale explainers between runs. Staleness is detected only when
    someone runs the skill.

## System Architecture & Workflow

```mermaid
sequenceDiagram
    autonumber
    actor Human as Engineer
    participant Skill as Coordinator (egm-explain)
    participant Writers as Writer subagents
    participant Reviewers as Goldfish reviewers
    participant Tree as Repository tree

    Human->>Skill: /egm-explain path [options]
    Skill->>Skill: Run the hash script (stop if it cannot run)
    Skill->>Tree: Find EGM contracts (stop if none: run /egm-bootstrap)
    Skill->>Skill: Classify existing files; decide own explainer vs fold; safety gate above 15 contracts
    loop Bottom-up, one tree level at a time
        Skill->>Writers: Contracts + reviewed child explainers + templates
        Writers->>Tree: Write EXPLAINER.md with fingerprint:PENDING
        Writers-->>Skill: Gaps
        Skill->>Reviewers: Fact-check (explainer + sources), then plain-language
        Reviewers-->>Skill: Return findings without modifying files
        Skill->>Tree: Apply source-supported fixes
        Skill->>Tree: Run mechanical checks and repair
    end
    Skill->>Tree: Write, review, fix and check repository explainer and glossary
    Skill->>Tree: Finalize fingerprints bottom-up
    opt readme_pointer is true
        Skill->>Tree: Add pointers for finalized explainers
    end
    Skill->>Human: Report written, folded, skipped, gaps, kept-as-is findings
```

The skill confirms the hash script runs, finds the contracts, classifies
existing files, decides what folds, and applies the safety gate. It then works
from the leaves up, and each level is written, reviewed, corrected and checked
before the next level starts. It does the same for the repository explainer and
records each fingerprint. It then optionally adds pointers for finalized
explainers, and reports.

### Inputs

| Input | Default | Purpose |
| :---- | :------ | :------ |
| `path` | required | Repository root or a subtree. The repository explainer and glossary are written only when `path` is the repository root. |
| `scope` | `all` | `all`; `repo` (root explainer only, built from finished child explainers, with a missing or `PENDING` one left out and reported); or `package` (one directory). A `package` run does not rewrite ancestors, and the report lists them as stale. `repo` with a subtree `path` stops with an error. `package` with the repository root is the same as `repo`. |
| `audience` | value in the existing footer, then the nearest ancestor explainer's footer, then `internal` | `shareable` leaves out network hosts, internal email addresses, account names, customer names, ticket numbers, credentials and vendor pricing. An explicit value that differs from an existing footer rewrites that explainer only with `refresh=true`. Otherwise the run reports it and stops. |
| `refresh` | `false` | `false` writes missing explainers, finishes `PENDING` files the skill owns, and reports stale ones without rewriting them. `true` also rewrites stale explainers in scope. |
| `contract_filename` | `README.md` | Use `EGM.md` for trees bootstrapped with that name. |
| `extra_sources` | none | Human-maintained documents the repository explainer may cite, such as a runbook. |
| `readme_pointer` | `false` | `true` adds the [pointer line](#pointer-line) under each contract's H1, linking to the explainer that covers it, which for a folded contract is the parent's. Pointers are added for finalized explainers and, on internal runs, for human-owned ones. A contract with no H1 gets no line, and the report lists it. A later run restores a removed line. Off by default for teams that treat READMEs as human-owned. |

### Finding Contracts

A file named `contract_filename` counts as an EGM contract when it contains the
`EGM_BLUEPRINT_START` sentinel, or the Interface, Invariants and Side Effects
headings from bootstrap's package template, or a "Subdirectories & Boundaries"
or "Subdirectories & System Boundaries" heading from its other templates. Other
READMEs are ignored. Skills share no code, so `SKILL.md` states this walk itself
and does not call bootstrap's. If more than 15 contracts are found, the skill
pauses and asks the user to approve the full run.

Writers do not use human notes in a contract as a source of facts, and the fact
checker reports any claim that only a human note supports. Human notes are text
outside the sentinels or, in a contract without sentinels, text outside the
template's sections. Editing a note still changes the contract hash, so it can
trigger a rewrite.

### Which Directories Get an Explainer

A directory gets its own explainer when any of these applies, and the
pass-through exception wins over all but the first: it is the repository root;
its contract describes a feature, an external system, a scheduled job, money
spent, or data people read; or it has child contracts. A **pass-through**
contract, with exactly one child contract and no interface, invariants or side
effects of its own, folds. Everything else folds into the nearest parent's
"What's inside" table. The report lists any contract that would fold into a
human-owned parent, because that parent will not be rewritten. If the repository
root has no contract, no repository explainer is written, and the report says so.

### Existing Explainers

The skill treats a file as its own only when its footer is readable and its
`output` hash matches the file. A hash shows that the content is unchanged, not
who wrote it. Before writing, the skill classifies any file already at the
target path. This check runs before any staleness check:

| What is there | Treated as | What the skill does |
| :------------ | :--------- | :------------------ |
| No file | Free | Writes a new explainer. |
| No `egm-explain` footer | Human-written | Never writes, moves or renames it. On internal runs the parent links to it as is. On shareable runs it stays unlinked and is listed under "Not shareable". Report: "Skipped: human-written". It is not a source, so no other explainer cites its claims. |
| A footer that cannot be parsed, or that is not on the last line | Human-written | Same as above. Report: "Skipped: unreadable footer". |
| A footer whose `output` hash does not match, with any fingerprint value | Edited by hand | Same as human-written, including on `refresh`. Report: "Skipped: edited by hand". When the footer's finalized fingerprint is also out of date, the report says "edited by hand; sources have changed since". |
| `fingerprint:PENDING` with a matching `output` hash | The skill's unfinished file | Overwrites it. |
| A finalized footer with a matching `output` hash | The skill's own file | Rewrites it only when stale and `refresh` is true. Otherwise leaves it unchanged and reports staleness. |
| A skill-owned file whose own contract is gone | Orphaned | Never deletes it or rewrites it. Report: "Orphaned", with a suggestion to remove it. This row takes priority over the `PENDING` and finalized rows, because an orphan has no contract to rewrite from. |
| A skill-owned file in a directory that now folds | Now folded | Never deletes it or rewrites it. Report: "Now folded". Its contract stays an input to the parent. This row also takes priority over the `PENDING` and finalized rows. |

To hand a skipped directory back to the skill, a person deletes or renames the
file. The skill never removes a README pointer line; turning `readme_pointer`
off leaves existing lines in place. The report lists any pointer whose target
is missing. When a directory starts folding, a run with `readme_pointer` on
points its line at the parent's explainer.

### Pointer Line

The pointer is exactly one line, directly after the contract's H1, with no added
blank line:

```
> Plain-language version: [EXPLAINER.md](<relative path>) <!-- egm-explain:pointer -->
```

The hash script strips only a line that matches this form in full, and nothing
else, before it hashes a contract. Adding or losing the pointer therefore never
makes an explainer stale.

### Explainer Shape

Package explainers follow one outline: In one sentence; What it does; an
optional diagram; Who or what uses it; What it touches; What it costs; Rules it
always keeps; When something goes wrong; What's inside; and, on internal runs, a
footer linking the contract. The repository explainer adds What people see, Data
in and out, Schedule, Costs and guardrails, and the Glossary. Excluding
diagrams, package explainers target 60 lines and should stay under 80. This limit
does not block finalization: a longer explainer is finalized and listed in the
report. The repository explainer has no limit because it carries the glossary.

Package explainers define each project term in plain language where it first
appears and do not link to a glossary, so each one stands alone on any run. The
repository explainer's glossary covers terms from its own sources, including the
definitions in its child explainers. In both, a definition of general knowledge,
such as what a webhook is, needs no source. A claim about what the term does in
this system must trace to a source, and the fact checker reports any that do
not. A human-owned repository explainer gets no glossary, and the report says
so. Link checks cover the whole tree on every full run. A subtree or
package run checks only what it wrote and reports anything else as unchecked.

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

**Where it lives.** In the explainer's last line, and nowhere else. A finished
explainer and an unfinished one use these two forms:

```
<!-- egm-explain v1 source: <contract path> audience:<internal|shareable> fingerprint:sha256:<64 hex> output:sha256:<64 hex> -->
<!-- egm-explain v1 source: <contract path> audience:<internal|shareable> fingerprint:PENDING output:sha256:<64 hex> -->
```

Keeping it in the file means it moves, is reviewed and is versioned with the
explainer, and there is no separate state file to fall out of step. A
sidecar manifest was considered and rejected for that reason; the cost is that
a refresh can say an explainer is stale but not which input changed.

**What it covers.** The fingerprint is the SHA-256 of a sorted, newline-separated
list of records, one per input:

*   `template <version>` for the explainer template;
*   `setting audience=<value>`;
*   `contract <sha256> <path>` for its own contract and the contract of every
    directory folded into it;
*   `child <sha256> <path>` for each skill-owned child explainer, using its
    `output` hash. For a human-owned child, the parent records that directory's
    `contract` instead and uses only a one-line description from the contract
    and, on internal runs, the file's link. A child left `PENDING` by an earlier
    run and not rewritten in this run is treated the same way, without the link,
    and the report lists it;
*   `extra <sha256> <path>` for each named extra source (repository explainer
    only).

Paths are relative to the repository root with forward slashes, and the list is
sorted by byte order. Before hashing, text is read as UTF-8, CRLF becomes LF,
trailing whitespace on each line is removed, and the file ends in one newline.
The template version is declared in `templates.md`.

A small standard-library Python script computes all hashes so every host gets
the same result, and it ships with test vectors. The script is required: if it
cannot run, the skill stops before writing any explainer and says why.

A rewritten skill-owned child has a new `output` hash, so its parent goes stale
without a separate rule. The chain stops at a human-owned explainer: a change
below it reaches ancestors only if it changes that directory's contract. When a
person edits a child, the parent's records change, so the parent goes stale and
is rewritten using only the link and the contract description. An added, removed
or changed input, or a changed `audience`, makes the explainer stale. A rewrite
receives the previous explainer and reconciles it against its current sources,
keeping wording that is still accurate. This is best effort: the footer does not
say which input changed, so some unaffected text may be reworded. An `audience`
change is the exception: it regenerates the explainer from
its sources, so its earlier text is not carried over. The cost of a leaf change
still grows with tree depth (see Risks & Limits). A missing input other than the
explainer's own contract also counts as stale.

`output` is the SHA-256 of the normalized explainer with its footer line
removed. It is how the skill detects a hand edit (see
[Existing Explainers](#existing-explainers)).

**When it is finalized.** Last. Writers leave `fingerprint:PENDING` with an
`output` hash of what they wrote. The skill updates that hash after each of its
own edits. The final fingerprint is computed only after all of these have
finished for the explainer:

1.  the writer's draft;
2.  both reviews, and every fix the coordinator accepts from them;
3.  the mechanical checks: links, Mermaid types and, for shareable runs, the
3.  the mechanical checks: links and Mermaid types. The Mermaid check confirms
    the diagram type only and does not prove the diagram renders. On shareable
    runs the pattern scan also runs here, but a hit only goes in the report and
    does not block finalization.
Mechanical checks and any repair run inside each level, before the next level
reads the file, so a repair never changes an input a parent has already read. A
failed check gets one repair attempt. If it still fails, that explainer and its
ancestors stay PENDING, and the rest of the tree still finalizes. Checks on files
this run did not write only report.

Finalization runs bottom-up after every level has been written, reviewed,
corrected and checked. The skill records each input's hash when it reads the
input and compares it at finalization. If an input changed, or an explainer no
longer matches its `output` hash, that explainer stays PENDING or is treated as
edited by hand, and the report says why.

If any step fails or the run stops, the affected explainers and their ancestors
keep `fingerprint:PENDING`, and the next run overwrites them unless they were
edited. There is no resume: reviewed work on those files is redone. Any change
made outside the skill is treated as a hand edit, including one made by a
formatter. When most explainers in a run mismatch, the report names a formatter
as the likely cause.

### Goldfish Review

1.  **Fact check** (an inline reviewer prompt in `SKILL.md`, not a persona
    under `agents/`): sees the explainer and the sources its writer was given:
    its contracts, reviewed child explainers, and named extra sources. On a
    rewrite it does not see the previous explainer, and it is told not to read
    anything else. It reports any claim, number, node or arrow those sources do
    not support, and any shareable-mode leak. General-knowledge definitions of
    terms are exempt.
    `egm-codebase-details` is not used: its instructions require reading code,
    which this skill deliberately leaves out.
2.  **Plain-language reader** (`egm-comprehension` in `REVIEW` mode, explainer
    only): reports what it could not follow. The dispatch prompt overrides the
    persona's rule against flagging general engineering terms: "You are a product
    manager or operator, not an engineer. Flag general engineering terms that are
    not explained here." The paraphrase the persona returns goes in the run's
    working notes, not in the explainer.

Both reviewers return findings and do not edit files. The plain-language
reader runs under the host's read-only `egm-comprehension` adapter where one
exists. The fact checker is an inline prompt with no adapter, so on every host
it runs as a general-purpose subagent, and the report says that read-only was
an instruction, not a restriction. This limits
edits, not reads: a reviewer may still be able to open other files. Writers and
reviewers treat contracts and extra sources as data, not instructions. A host
with no subagents stops, because a review in the same context is not a Goldfish
review.

The coordinator applies source-supported fixes. Fact fixes land first.
A reader's suggested rewrite often guesses at facts it
cannot see, so each one is checked against the sources before it is applied;
rewrites that would need a missing fact are reported as "kept as is" and added
to the gaps. Applied fixes are checked against sources by the coordinator but
are not reviewed again.

A gap is a fact an explainer needs that its sources do not contain. Gaps appear
only in the run report, grouped by contract so that whoever maintains a contract
can act on them. They are not written into the explainer.

### Shareable Runs

`shareable` reduces internal detail. It is not a guarantee, and a person should
read the output before sharing it.

*   Writers receive the omission list, and the fact checker reports any item on
    it.
*   A mechanical scan flags email addresses, IP addresses and hostnames for a
    person to check.
*   The visible footer has no contract link, because contracts are not redacted.
*   A parent links only to shareable children. Any human-owned, hand-edited or
    internal explainer in scope is left unlinked and listed under "Not
    shareable", and the run reports that the tree is not ready to share. It is
    not a writer input: the parent records that directory's `contract` and uses
    only a one-line description from it.
*   PENDING files have not finished review and are never shareable.

### Cost Control

One writer per directory and two reviewers per explainer would mean about 45
subagents for a 15-explainer tree. Writers take 2 to 5 sibling directories each,
and a directory with no sibling gets its own writer. Each fact checker and
reader gets one explainer, because a shared batch would let a claim pass on
another directory's contract and would teach the reader terms from its siblings.
That is about 35 subagents for 15 explainers. The trial's batched run used 20 in
total, but it did not measure what batching cost in accuracy.

The safety gate shows the expected number of explainers and subagents before any
are spawned. Runs larger than the 20-contract trial are untested.

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

This was one run on one repository, using a draft that recorded only the
contract hash, so 'all hashes match' refers to that earlier scheme. The trial
did not exercise the composite fingerprint, ownership rules, PENDING recovery,
level-by-level review, per-explainer reviewers or inline definitions, and it did
not measure whether non-engineers find the output useful. The Stage 2
implementation should repeat the trial on the final design and have non-engineers
read the output and say whether it helps.

The run led to eight design changes: hash after the pointer, fold pass-through
contracts, `extra_sources` for runbook facts, the 80-line ceiling, checking
reader rewrites against sources, a glossary covering every linked term, batched
subagents, and gaps grouped by contract. Review later replaced four of them:
hashing after the pointer became excluding the pointer from the hash, batched
subagents became batched writers with one reviewer pair per explainer, the linked
glossary became inline definitions in package explainers, and the 80-line ceiling
became a reported limit.

## Risks & Limits

| Risk | Effect | Mitigation or accepted limit |
| :--- | :----- | :--------------------------- |
| A contract is wrong or has drifted | An explainer repeats it confidently, and the checks pass. | Accuracy is stated only relative to the contracts. The report recommends `/egm-drift-report` first. |
| Non-engineers act on wrong information | Decisions rest on an error. | Fact check, source-checked fixes and a link to the contract in internal mode. Remaining errors are not measured yet. |
| Redaction misses something | Internal detail is shared. | See [Shareable Runs](#shareable-runs). A person must read the output first. |
| One filename, two audiences | Internal and shareable versions cannot coexist in one tree. | Accepted. Generate the shareable version on a separate branch or copy. |
| Contracts or extra sources contain instructions or secrets | Agents with write access may act on them or copy them. | Source files are treated as data, and writers may write only the explainers assigned to them. Secrets already in contracts are out of scope, and the pattern scan is only a partial check. |
| A leaf change rewrites all ancestors | Cost, reworded text and merge conflicts in the root explainer. | Accepted. Rewrites try to keep accurate wording, but some rewording is expected. Resolve a merge conflict by taking one side whole and rerunning. |
| A formatter or format-on-commit hook changes explainers | Changed files count as edited by hand and stop refreshing, and their parents are rewritten from only a link and a contract description. | Normalization covers line endings and trailing whitespace only. When most explainers in a run mismatch, the report names a formatter as the likely cause. Exclude explainers from the formatter, or delete the affected files and rerun. |
| Explainers go stale between runs | Readers cannot tell. | Accepted. Staleness is detected only when the skill runs. |
| Large trees | The coordinator holds findings for the whole run. The largest tree tested has 20 contracts. | The safety gate shows the expected subagent count. There is no tested upper limit. |
| Concurrent runs | Runs can overwrite each other's PENDING files. | Not supported. A mismatch is detected at finalization (see [Freshness](#freshness)). |

## Alternatives Considered

| Alternative | Why not |
| :---------- | :------ |
| A plain-language section inside each README | Spends agent context on prose agents do not need, and `/egm-bootstrap` updates could overwrite it. A one-line pointer costs little if it is lost; a whole section does not. |
| Generate explainers from code | Duplicates `/egm-bootstrap` and gives up a single reviewed source, since contracts can be checked with `/egm-drift-report`. |
| A flag on `/egm-bootstrap` | Different audience and different reviewers, and a flag would tie explainer refreshes to bootstrap runs. |
| One repository overview only | No entry point at the folder level, where people land from GitHub. |
| A sidecar manifest for fingerprints | A separate state file can fall out of step with the explainer. Its benefit is naming which input changed. |
| Footer presence alone decides ownership | Simpler and needs no hash, but a person who edits and leaves the footer in place loses that edit on the next rewrite. |
| Build each explainer only from its own and folded contracts | Removes the ancestor cascade and most ordering rules, but a parent's description depends on what its contract rolls up, and the trial used child text. Open; see [Decisions](#decisions). |

## Decisions

Settled with maintainers on [#228](https://github.com/google/elephant-goldfish-model/pull/228):

1.  The default filename stays `EXPLAINER.md`.
2.  The README pointer line is opt-in (`readme_pointer`, default `false`).
3.  The fact checker stays inline, reading only the supplied sources, rather
    than becoming a persona or reusing `egm-codebase-details`.

Open for maintainers, raised by review and not yet decided:

1.  Should each explainer be built only from its own and folded contracts, with
    no child explainers as inputs?
2.  Should `audience: shareable` ship in the first version, or be deferred?
3.  Should the first version cover every selected directory, or the repository
    explainer plus directories someone names?
4.  Can every supported host run the required Python hash script?

## Implementation Files

| File Path | Type | Purpose & Reason for Existence |
| :-------- | :--- | :----------------------------- |
| `skills/egm-explain/SKILL.md` | Skill Definition | Implements `/egm-explain`: discovery, folding, batched writers, diagrams, glossary, linking, running the hash script, review and verification. |
| `skills/egm-explain/references/templates.md` | Templates | Package and repository explainer outlines. |
| `skills/egm-explain/scripts/explain_hash.py` | Script | Computes the normalized hashes and fingerprints, so results match across hosts. |
| `tests/unit/test_explain_hash.py` | Unit Tests | Runs the script's test vectors under `pytest tests/unit`, which `TEST.md` points to. |
| `skills/egm-explain/TEST.md` | Test Plan | Points to `pytest tests/unit` and lists the manual scenarios to run from `test_scenarios.yaml`. |
| `skills/egm-explain/test_scenarios.yaml` | Evaluation Scenarios | No contracts, diagram grounding, pass-through fold, pointer changes do not make an explainer stale, shareable redaction, refresh after child or extra-source changes, audience changes, read-only reviewer findings, human-written and hand-edited explainers left alone, the README pointer added only when `readme_pointer` is true, interrupted run and PENDING recovery, an edited PENDING file, an unreadable footer, formatter changes, orphaned and now-folded explainers, a human-owned explainer mid-tree, the safety gate, a changed input during a run, a default run reporting without rewriting, an explicit audience change without `refresh`, a hash script that cannot run, a shareable run with a human-owned explainer in scope, a repaired child that does not stall its parent, a general-knowledge definition passing the fact check, an over-long explainer being reported, and a `PENDING` child left out of a partial run. |
| `skills/egm-explain/assets/icon.svg` | Icon | Speech bubble in the blue group from `skill_icons.md` (`#1b6ef3` / `#7cacf8`). |
| `skills/egm-explain/agents/openai.yaml` | Host Metadata | Display name, description and icon for OpenAI hosts. |

Registering the skill also touches `scripts/pack_plugin.py` (which must also
package the hash script), `tests/unit/test_harnesses.py`,
`tests/unit/test_packaging.py`, `README.md`, `docs/getting_started.md`, the site
components that list skills (`Skills.astro`, `Loop.astro`, `SkillIcon.astro`),
`docs/designs/skill_icons.md` ("seven skill marks" and "All seven marks" also
need updating), the skill counts that are instructions in step 5 of
`docs/cursor.md` and in `docs/opencode.md` ("seven commands" and "all seven
skills are discoverable"), and the regenerated `distributions/claude`. The dated
verification notes in `docs/copilot.md`, `docs/muse.md` and
`docs/harnesses.md` stay unchanged.

## References

*   [Bootstrap design](bootstrap.md), whose safety gate approach and contract
    templates this skill follows.
*   [Drift report design](drift_report.md), which keeps the contracts
    themselves current.
