# Test Plan: EGM-Lite Skill

Frontmatter, link checks, and scenario coverage run in `pytest tests/unit` (see [TESTING.md](../../TESTING.md)).

## Protocol Verification Checklist

When evaluating or exploring `egm-lite` interactively in chat, verify:

-   **Phase 1 (Critique Pause):** The agent adopts the **Elephant (Critic)**
    persona in-session, leads with a plain-English `> **BLUF:**` blockquote
    (followed by `---`) on whether the approach is ready for `checklist` or
    blocked, challenges assumptions without editing repository code, documents
    competing approaches in `egm_lite_alternatives.md` without inline discussion
    when multiple viable options exist (omitting it for trivial or single-path
    tasks), and prompts for `checklist`.
-   **Phase 2 (Execution Checklist):** Upon `checklist`, the agent adopts the
    **Elephant (Planner)** persona, writes `egm_lite_checklist.md` with itemized
    change targets (as clickable file and line-range links), rationales,
    pre-review exclusions, accepted `CONTEST` rationales, and the Assumption
    Lifecycle Legend as GFM task list checkboxes (`- [ ]`), and chains
    immediately into Phase 3 in the same turn.
-   **Phase 3 (Automatic Specification Review):** Within the **same turn**
    immediately after Phase 2 writes `egm_lite_checklist.md`, the agent
    automatically spawns a fresh-context **Goldfish Specification Reviewer**
    subagent (`invoke_subagent`, `Agent`, or `spawn_agent`), injecting the
    checklist markdown and Specification Review Rubric (skipping pre-review
    exclusions and accepted `CONTEST` items, suppressing stylistic nitpicks, and
    forbidding AST/`git diff` checks), and halts to await the subagent's
    response. If no fresh-context subagent tool exists, it refuses a
    same-context review and falls back to human `Proceed` / `exec` approval.
-   **Phase 4 (Exec Protocol & Optional Re-Review):** Upon `exec` (or clicking
    **Proceed**) after specification verification/triage, the agent adopts the
    **Elephant (Builder)** persona, records the starting review baseline before
    editing, applies any inline checklist comments or agreed triage fixes,
    implements only approved checklist items (no YAGNI), runs local tests
    covering affected targets, marks completed items with `- [x]`, leads with a
    `> **BLUF:**` on escalation halts, autonomous self-repairs, or multi-file
    summaries (omitting it on clean single-target runs), and completes the
    task—offering `review` or `goldfish` strictly as an **optional**
    post-implementation diff re-review without auto-spawning Phase 5.
-   **Phase 5 (Optional Adversarial Diff Re-Review):** Upon an explicit
    post-implementation `review` or `goldfish` command, the agent collects all
    task changes against the recorded baseline (including task commits, staged
    and unstaged edits, deletions, and new untracked files while keeping
    unrelated pre-existing changes separate; stopping if the baseline is missing
    or any target cannot be inspected), spawns a fresh-context **Goldfish Code
    Reviewer** subagent (or stops if no subagent tool exists), enforces a binary
    review contract (`[✅ LGTM]` vs. findings only), and halts to await the
    subagent's response.
-   **Phase 6 (Unified Post-Review Resolution Gate):** Upon receiving subagent
    findings (from either Phase 3 spec review or Phase 5 diff re-review), the
    agent adopts the **Elephant (Resolver)** persona, discriminates
    pre-implementation vs. post-implementation state, keeps findings triage
    presentation-only without file-editing or VCS tools, opens with a
    plain-English `> **BLUF:**` blockquote (followed by `---`) led by
    **`[🛠️ X FIX | 🛡️ Y CONTEST]`** (or **`[✅ LGTM]`** on a clean pass),
    triages findings into continuous numbered `[X] [PY]` items (`P0`..`P3`)
    sorted in descending severity order, gates pre-implementation spec LGTM on
    `exec` / **Proceed** without premature task closure, and persists accepted
    `CONTEST` rationales in `egm_lite_checklist.md`.
-   **State Transitions & Non-Sycophantic Posture:** Out-of-order commands (such
    as `exec` or `review` directly after Phase 1 Critique Pause) emit a graceful
    `> **BLUF:** [State Advisory]` blockquote, referenced local files and line
    ranges use clickable links, and responses lead with technical risks or
    defects without flattering adjectives or polite apologies.
