# Test Plan: EGM-Lite Skill

Frontmatter, link checks, and scenario coverage run in `pytest tests/unit` (see [TESTING.md](../../TESTING.md)).

## Protocol Verification Checklist

When evaluating or exploring `egm-lite` interactively in chat, verify:

-   **Step 1 (Critique Pause):** The agent adopts the **Elephant (Critic)**
    persona, leads with a plain-English `> **BLUF:**` blockquote (followed by
    `---`) on whether the approach is ready for `checklist` or blocked,
    challenges assumptions without editing repository code, documents competing
    approaches in `egm_lite_alternatives.md` without inline discussion when
    multiple viable options exist (omitting it for trivial or single-path
    tasks), and prompts for `checklist` only, answering `exec` with a state advisory.
-   **Step 2 (Checklist & Spec Gating):**
    -   *Section 2A (Checklist Generation):* Upon `checklist`, the agent adopts
        the **Elephant (Planner)** persona, outputs an itemized checklist of
        change targets (with files and referenced specs as clickable file and
        line-range links), rationales, and any user-agreed pre-review exclusions
        as GFM task list checkboxes (`- [ ]`), evaluates deterministic
        complexity criteria (two or more production code files,
        async/concurrency, public APIs, or `[⚠️ UNVERIFIED]`/`[⏳ ACK]` tags),
        emits a BLUF that recommends the spec review (`goldfish` / `review`) on
        non-trivial tasks or says direct execution is reasonable on trivial/doc
        tasks, and in every case offers both `exec` and `goldfish` / `review`.
    -   *Section 2B (Stateless Spec Review):* Upon `goldfish` or `review`
        pre-implementation, the agent adopts the **Goldfish (Specification
        Reviewer)** persona via the harness's fresh-context subagent tool
        (halting if none is available), injects checklist markdown and the Spec
        Review Rubric (skipping pre-review exclusions and accepted `CONTEST`
        items, and forbidding AST/diff checks), and halts to await the response.
-   **Step 3 (Exec Protocol):** Upon `exec` (or clicking **Proceed**), the agent
    adopts the **Elephant (Builder)** persona. If following a verified
    specification, it reads `egm_lite_checklist.md` directly without re-creating
    it; if true fast-path, it initializes the checklist first. It implements
    only approved checklist items (covering code, specifications, or design
    docs), runs local tests covering affected targets (or N/A / linter for pure
    doc edits), marks completed items with `- [x]`, leads with a `> **BLUF:**`
    on escalations, self-repairs, or multi-file summaries (omitting on clean
    single-target runs), and gates on prompting for `review` or `goldfish`.
-   **Step 4 (Adversarial Diff Review):** Upon `review` or `goldfish`
    post-execution (or with no task in progress on an existing diff), the agent
    adopts the **Goldfish (Reviewer via Subagent)** persona (spawning via the
    harness's fresh-context subagent tool or stopping if none is available),
    restricts findings to material issues while suppressing stylistic nitpicks,
    enforces a strictly binary review response (findings only vs. explicit
    `[✅ LGTM]` on zero findings), evaluates against the Diff Review Rubric
    (adapted for documentation diffs by replacing runtime checks with factual
    consistency and markdown hygiene), and halts to await the subagent's
    response.
-   **Step 5 (Unified Post-Review Resolution Gate):** Upon receiving subagent
    findings (spec or diff review), the agent adopts the **Elephant (Resolver)**
    persona, keeping triage presentation-only without file mutations, opens with
    a plain-English `> **BLUF:**` blockquote (followed by `---`) led by
    **`[🛠️ X FIX | 🛡️ Y CONTEST]`** (or **`[✅ LGTM]`** on a clean pass), triages
    findings into continuous numbered and priority-tagged `[X] [PY]` items
    (`P0`..`P3`), branches on the review that responded (Pre-Implementation spec
    triage offers `checklist`, `exec`, or `goldfish` re-review and strictly
    forbids premature task closure; Post-Implementation diff review triage
    offers `checklist` or `exec`), and persists accepted `CONTEST` rationales in
    `egm_lite_checklist.md`.
-   **Standalone Diff Review:** In a fresh session, ask for a review of a
    supplied diff with no checklist. Run once with a clean reviewer response
    and once with findings. Both runs report the review in chat without
    reading or creating a checklist or offering `checklist` or `exec`.
    Repeat with an unrelated checklist present and verify it is untouched.
-   **Top-Level Invariants & Graceful Recovery:** `goldfish` and `review` are
    interchangeable aliases bound to state, invalid state leaps (e.g. diff
    review with nothing to review, spec review before checklist creation) emit a
    graceful `> **BLUF:** [State Advisory]` blockquote, and fast-path execution
    natively supports iterative specification and design doc updates.
-   **Code References & Non-Sycophantic Posture:** Referenced local files and
    line ranges use clickable links, internal operational directives are never
    echoed into user chat, and responses lead with technical risks or defects
    without flattering adjectives or polite apologies.
