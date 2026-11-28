# Tag Review Findings with Supporting Evidence

- **Author:** @n3wth
- **Status:** Proposed (Stage 1 Design Doc)
- **Date:** 2026-11-28
- **Scope issue:** #433

## Overview

In the Elephant-Goldfish Model (EGM), **Goldfish** reviewers are fresh-context, read-only subagents that audit a target document (`TargetFile`), while the **Elephant** is the persistent primary agent that resolves findings. Today, Goldfish reviewers report every finding with a severity (`Blocker`, `Major`, `Nit`) and an affected scope, without stating what the finding rests on. A defect visible in the reviewed document, a mismatch with a referenced file, and a question the reviewer cannot answer from anything it read all arrive in the same shape.

This design adds one required field to every review finding: its **Evidence Basis** (`Document`, `Referenced file`, or `Owner question`) together with a concrete citation or question. The eight reviewer personas (`agents/*.md`) emit the field, [the synthesizer](../../agents/synthesizer.md) carries it into synthesized reports while grouping owner questions apart from defects, and [the resolution skill](../../skills/egm-resolve/SKILL.md) uses the basis directly when categorizing findings—mapping `Owner question` to `ESCALATE` by default.

This is a prompt-only change to `agents/*.md` and `skills/egm-resolve/SKILL.md`. It leaves [the review skill](../../skills/egm-review/SKILL.md) (13,420 bytes) unchanged.

## The Problem

1. **Defects and questions look identical**: A fresh-context Goldfish cannot distinguish a missing section in the design from an unverified external fact (such as a CLI flag or an uninspected directory) unless it states what it checked. Both arrive as `Major` or `Blocker` findings, forcing the author to spend time disproving questions as if they were defects.
2. **Duplicated reconstruction in `egm-resolve`**: [The resolution skill](../../skills/egm-resolve/SKILL.md) already separates findings into four categories: `PROPOSE FIX` (valid gap with a proposed edit), `CONTEST` (inaccurate critique refuted by readable evidence), `ESCALATE` (evidence lies outside every file the reviewer could read), and `DECLINE` (a `Nit` left unfixed). Today, the Elephant must re-derive what each Goldfish read in order to choose between `CONTEST` and `ESCALATE`.
3. **Eval measurement ambiguity**: Review benchmarks (#61 and #494) cannot reliably separate a false positive from an unresolved owner question when both share the same finding format.

## Goals & Non-Goals

### Goals

- Require every finding in `agents/*.md` (`Mode: REVIEW`), synthesized reports (`agents/synthesizer.md`), and `goldfish_review_report.md` (`skills/egm-resolve/SKILL.md`) to state an `Evidence Basis` (`Document`, `Referenced file`, or `Owner question`) and a citation or question.
- Group `Owner question` findings apart from `Document` and `Referenced file` defects in synthesized and resolution reports.
- Update `skills/egm-resolve/SKILL.md` so it uses `Evidence Basis` when selecting a resolution category, mapping `Owner question` to `ESCALATE` by default.
- Keep the implementation prompt-only within `agents/*.md` and `skills/egm-resolve/SKILL.md`, without modifying `skills/egm-review/SKILL.md`.

### Non-Goals

- No new severity levels and no change to how severity (`Blocker`, `Major`, `Nit`) is assigned.
- No change to [the review loop](../../skills/egm-review-loop/SKILL.md) convergence rules; unresolved `Blocker` or `Major` owner questions continue to follow existing round-resolution behavior until settled.
- No machine-readable findings file or sidecar ledger (#278 covers structured ledgers).
- No new reviewer personas, scripts, hooks, or runtime components.
- No change to which files a reviewer is permitted to read (`GoldfishContext` supporting-file lists and Stage 6 isolation remain unchanged).

## Alternatives Considered

1. **Infer evidence basis only inside `egm-resolve`**: Rejected because the Elephant would still have to reconstruct what each fresh-context Goldfish read, and synthesized reports read directly by human authors would still mix questions and defects.
2. **Add a fourth severity level (e.g., `Question`)**: Rejected because severity measures impact while evidence basis measures epistemic grounding. Changing severity levels would also alter convergence rules and existing evals.
3. **Emit a separate machine-readable findings file**: Rejected as out of scope (#278 covers structured ledgers) and incompatible with the prompt-only constraint.

## Technical Plan

### 1. Evidence Basis Taxonomy

Every finding in `Mode: REVIEW` must declare exactly one `Evidence Basis`:

| Basis | Meaning | Required Citation / Field |
| :---- | :------ | :------------------------ |
| `Document` | The finding is visible in the reviewed document itself (omission, contradiction, ambiguity, or structural/style flaw). | Line numbers or quoted text from `TargetFile`. |
| `Referenced file` | The finding comes from a file the document references or that the reviewer was permitted to read. | File path and symbol name or line numbers. |
| `Owner question` | The reviewer cannot confirm or refute the point from anything it read. | The specific question the document owner must answer. |

### 2. Reviewer Personas (`agents/*.md`)

Update the `IF Mode: REVIEW` output format in all eight reviewer personas (`agents/*.md`, listed in Section 5) to add two required fields per finding:
- **Evidence Basis**: `Document` | `Referenced file` | `Owner question`
- **Evidence / Question**: Line numbers/quote (`Document`), file path + symbol/lines (`Referenced file`), or the specific question for the owner (`Owner question`).

Include a one-line classification rule: if `TargetFile` fails to define a term or decision it introduces, the basis is `Document`, not `Owner question`; check `TargetFile` and readable referenced files before emitting `Owner question`.

### 3. Synthesizer (`agents/synthesizer.md`)

`agents/synthesizer.md` compiles parallel Goldfish outputs into `goldfish_review_report.md` (referred to as `review.md` in #433). Update `IF Mode: REVIEW` in `agents/synthesizer.md`:
- **Preserve & normalize**: Carry `Evidence Basis` and `Evidence / Question` into every consolidated finding. If a reviewer omits `Evidence Basis` or uses an unrecognized label, normalize it to `Owner question` (or infer `Document` / `Referenced file` only when an explicit line or file citation is present) so no finding is dropped.
- **Deduplicate cleanly**: When overlapping findings from multiple reviewers are merged, prefer a verifiable basis (`Document` or `Referenced file`) over `Owner question` (retaining both verifiable citations if both exist), drop the superseded `Owner question` framing, and place the merged item only in `## Prioritized Findings (Blockers -> Major -> Nits)`—never duplicated in `## Owner Questions`.
- **Separate sections**: Split the report into `## Prioritized Findings (Blockers -> Major -> Nits)` for `Document` and `Referenced file` findings, and `## Owner Questions` (ordered by severity) for `Owner question` findings.

### 4. Resolution (`skills/egm-resolve/SKILL.md`)

Update Step 2 (`Evaluate & Categorize`) and Step 3 (`Report Fixes`) in `skills/egm-resolve/SKILL.md`:
- **Default routing**: Map `Owner question` findings to `ESCALATE` by default without editing `TargetFile`, unless the Elephant can cite readable evidence that the reviewer could read (a file and symbol, or a decision recorded in `TargetFile`) that settles the question—in which case `CONTEST` or `PROPOSE FIX` applies with that citation.
- **Missing basis fallback**: For direct-dispatch runs (such as Stage 6 `egm-comprehension`, which bypasses `agents/synthesizer.md`), treat any finding lacking a valid `Evidence Basis` as `Owner question` unless its citation explicitly references lines in `TargetFile` or a readable file.
- **Report template**: Include `**Evidence Basis:**` and `**Evidence / Question:**` in `goldfish_review_report.md`, and group `## Owner Questions` separately from defect findings. Step 4 continues to surface all `ESCALATE` items first in chat regardless of which report section they came from.
- **Byte budget**: `skills/egm-resolve/SKILL.md` is currently 8,541 bytes (leaving 15,459 bytes of headroom under the 24,000-byte limit enforced by [the skill load-limit test](../../tests/unit/test_skill_load_limits.py)), so adding the field and section header fits without touching `skills/egm-review/SKILL.md`.

### 5. Stage 2 File Boundary & Validation Plan

**Target files for Stage 2 implementation:**
- `agents/codebase_details.md`, `agents/comprehension.md`, `agents/design_critic.md`, `agents/implementation_readiness.md`, `agents/inventive_catalyst.md`, `agents/structural.md`, `agents/style.md`, `agents/zoom_out.md`
- `agents/synthesizer.md`
- `skills/egm-resolve/SKILL.md`

**Verification in Stage 2:**
- Run `uv run --no-project --with pytest --with pyyaml pytest tests/unit` (verifying [skill load limits](../../tests/unit/test_skill_load_limits.py), [link integrity](../../tests/unit/test_link_integrity.py), and [markdown tables](../../tests/unit/test_markdown_tables.py)).
- Run an eval acceptance case (coordinated with #494): carry an `Owner question` finding from a Goldfish report through `agents/synthesizer.md` into `skills/egm-resolve/SKILL.md`, verifying that its `Evidence Basis` and status survive handoff and reach `ESCALATE` without becoming an evidence-backed defect.

## Risks & Mitigations

- **Misclassification between `Document` and `Owner question`**: A reviewer might label an undefined term in `TargetFile` as an `Owner question`, or over-use `Owner question` to avoid inspecting readable files. Mitigate with the explicit rule in `agents/*.md` requiring reviewers to check `TargetFile` and readable referenced files first and classify missing inline definitions as `Document`.
- **Direct dispatch vs. synthesizer parity**: Direct-dispatch runs (including Stage 6 `egm-comprehension`) bypass `agents/synthesizer.md`. Putting the required field in `agents/*.md` and the missing-basis fallback in `skills/egm-resolve/SKILL.md` ensures both paths behave consistently.

## Open Questions

- **Clean-round accounting in `egm-review-loop`**: Should an unresolved `Owner question` count against a clean round in `skills/egm-review-loop/SKILL.md`, or only `Document` and `Referenced file` defects? This is deferred from Stage 2; maintainers should decide whether to track it in a follow-up issue.
