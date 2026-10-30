# Contributor vs. Maintainer Role Disambiguation & Author Resolution

*   **Author:** JayadityaGit
*   **Status:** Draft
*   **Date:** 2026-10-30

--------------------------------------------------------------------------------

## Overview

Disambiguate the roles of external contributors and core maintainers during specification drafting and design reviews. The feature resolves author identity locally from `git config user.name` with an interactive chat fallback. In drafting guidelines, it replaces the ambiguous "Owner Decides" doctrine with "Author Decides Architecture". It mandates objective technical justifications for rejected alternatives (banning unsupported "Rejected by maintainer" claims) and standardizes proposal status tracking (`Draft | Proposed | In Review | Approved`) across Elephant-Goldfish Model (EGM) templates.

--------------------------------------------------------------------------------

## The Problem

When external contributors use EGM to draft specifications for upstream repositories:
1. **False Maintainer Attribution**: EGM drafting instructions label the operator as the "Owner" ("Owner Decides Architecture" guideline) and leave the `Author` template unguided. Without explicit instructions, LLMs frequently attribute the document to `<repo> maintainers`.
2. **Misattributed Upstream Rejections**: When a contributor rejects design alternatives during ideation or drafting, the model records the rejection as "Rejected by maintainer". This misrepresents upstream maintainer consensus when maintainers have not yet reviewed the proposal.
3. **Missing Author Resolution**: Without guidance to inspect local git configuration, models hallucinate author identities or project ownership.

--------------------------------------------------------------------------------

## Goals

* **Automated Author Resolution**: Auto-populate `Author` via local `git config user.name` with interactive prompt fallback across `skills/egm-draft/SKILL.md` and `skills/egm-brainstorm/SKILL.md`.
* **Role-Accurate Drafting Semantics**: Replace "Owner Decides Architecture" with "Author Decides Architecture" in `skills/egm-draft/SKILL.md`.
* **Technical Rejection Enforcement**: Require alternatives to record objective technical trade-offs (e.g., `Rejected by author: [technical rationale]`); strictly forbid writing `Rejected by maintainer` unless citing verified maintainer comments or issue URLs.
* **Proposal Status Tracking**: Standardize `Status: [Draft | Proposed | In Review | Approved]` in `skills/egm-draft/references/design_doc.md`.

--------------------------------------------------------------------------------

## Non-Goals

* **Remote Network Role Detection**: No `gh` CLI network queries or GitHub permission scraping; execution remains fully offline-capable.
* **Role Metadata in Frontmatter**: Do not store transient repository permission roles (`Role: Contributor | Maintainer`) in document headers.
* **Cryptographic Identity Verification**: No GPG/SSH commit signature verification or OAuth credential generation.
* **Automated GitHub PR Approvals**: No modifications to repository branch protection or PR merge authority rules.
* **Retroactive Spec Rewrites**: No automated migration sweeps across existing historical design docs in `docs/designs/`.

--------------------------------------------------------------------------------

## Critical User Journeys (CUJs)

### CUJ 1: Contributor with Configured Git Identity

*   **Given**: An external contributor working in a cloned repository with `git config user.name` configured.
*   **When**: The contributor invokes `/egm-draft` to generate a feature specification.
*   **Then**: EGM reads local git configuration and initializes the document header with the contributor's name as `Author` and sets `Status: Draft` without interrupting the session.

### CUJ 2: Contributor in Interactive Session Without Git Config

*   **Given**: An interactive session where `git config user.name` is unconfigured or returns empty.
*   **When**: The contributor invokes `/egm-draft`.
*   **Then**: EGM prompts the contributor in chat: `"Please specify your author name or GitHub handle for the design document:"`, records the response in the header, and proceeds with drafting.

--------------------------------------------------------------------------------

## Technical Plan

### Offline Author Discovery Routine

The intake phase of `skills/egm-draft/SKILL.md` and `skills/egm-brainstorm/SKILL.md` executes a simple offline discovery routine:

1. **Local Git Query**: Check local `git config user.name`.
2. **Environment Fallback**: If unset or failing, inspect environment variables `GIT_AUTHOR_NAME`, `USER`, or `USERNAME`.
3. **Interactive Fallback**: If identity remains unset, prompt the user in chat for their author name or GitHub handle.

### Terminology & Drafting Doctrine Refactoring

In `skills/egm-draft/SKILL.md`:
* **Rename Rule 13**: Change "Owner Decides Architecture" to "Author Decides Architecture". Clarify that the proposal author selects architectural options during drafting, while upstream PR approval authority remains strictly with repository maintainers under `AGENTS.md`.
* **Alternatives Rejection Attribution (Step 4)**: Mandate that rejections document the proposal author's rationale:
  * Format: `Rejected by author: [technical trade-offs such as latency, complexity, or scope]`.
  * Attribution constraint: Do not attribute rejections to "maintainer" unless quoting an upstream maintainer issue, discussion, or PR URL.

### Template & Standard Enhancements

* **`skills/egm-draft/references/design_doc.md`**: Update header metadata block to standardize status values and lifecycle:
  ```markdown
  # [Feature/Project Name]

  *   **Author:** [Author Name or GitHub Handle]
  *   **Status:** [Draft | Proposed | In Review | Approved]
  *   **Date:** [YYYY-MM-DD]
  ```
  *Status Lifecycle*:
  * `Draft`: Actively authored locally by the contributor.
  * `Proposed`: Shared as an RFC or inquiry issue for team awareness.
  * `In Review`: Submitted as a formal Stage-1 Design Doc PR under maintainer review.
  * `Approved`: Formally merged into `docs/designs/` by repository maintainers.
* **`skills/egm-brainstorm/SKILL.md`**: Update `concepts_brief.md` template to include `* **Author:** [Author Name or GitHub Handle]` resolved via the same offline routine.
* **`resources/document_standards/feature-spec-standard.md`**: Update "The Alternatives Rule" to mandate that rejection rationales cite technical trade-offs and specifically disallow ungrounded appeals to authority ("Rejected by maintainer").

--------------------------------------------------------------------------------

## Alternatives Considered

### Alternative A: Remote GitHub API & CLI Role Querying
*   **Pros**: Could theoretically attempt to inspect upstream repository permissions or team memberships directly.
*   **Cons**: Violates offline-first execution; introduces network latency, authentication failure modes (unauthenticated `gh` CLI), and platform lock-in (fails on local git, GitLab, or Bitbucket).
*   **Reason for Rejection**: Rejected by author: Adds high external dependency complexity and failure modes for a problem that is fundamentally solved by local prompt guidance and local git configuration.

### Alternative B: Mandatory Interactive Author Prompt on Every Session
*   **Pros**: Guarantees the user explicitly confirms their identity on every invocation.
*   **Cons**: Introduces repetitive, unnecessary friction on every design drafting session even when local git identity is already established.
*   **Reason for Rejection**: Rejected by author: Creates unnecessary cognitive friction; inspecting local git config with interactive fallback achieves parity with zero redundant prompts.

--------------------------------------------------------------------------------

## Risks & Mitigations

### Risk 1: Execution in Environments Without Git Installed
*   **Mitigation**: The author discovery routine treats shell command failures and missing binaries as non-fatal. Any failure immediately triggers fallback to environment variables (`GIT_AUTHOR_NAME`, `USER`, `USERNAME`) or chat prompt.

