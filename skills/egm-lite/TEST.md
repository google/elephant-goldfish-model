# Test Plan: EGM-Lite Skill

Frontmatter, link checks, and scenario coverage run in `pytest tests/unit` (see [TESTING.md](../../TESTING.md)).

## Protocol Verification Checklist

When evaluating or exploring `egm-lite` interactively in chat, verify:

-   **Step 1 (Critique Pause):** The agent adopts the **Goldfish (Critic)**
    persona, leads with a plain-English `> **BLUF:**` blockquote (followed by
    `---`) on whether the approach is ready for `exec` or blocked, challenges
    assumptions without editing repository code, documents competing approaches
    in `egm_lite_alternatives.md` without inline discussion when multiple viable
    options exist (omitting it for trivial or single-path tasks), and prompts for
    `checklist` (or fast-path `exec`).
-   **Step 2 (Lightweight Checklist):** Upon `checklist`, the agent adopts the
    **Elephant (Planner)** persona, outputs an itemized checklist of change
    targets (with files and referenced specs as clickable file and line-range
    links), rationales, and any user-agreed pre-review exclusions as GFM task
    list checkboxes (`- [ ]`), and pauses without editing code.
-   **Step 3 (Exec Protocol):** Upon `exec` (or clicking **Proceed**), the agent
    adopts the **Elephant (Builder)** persona, initializes or updates
    `egm_lite_checklist.md` first if `checklist` was bypassed (or applies any
    inline artifact comments accompanying approval), implements only the
    approved checklist items (no YAGNI), runs local tests covering affected
    targets, marks completed items with `- [x]`, leads with a `> **BLUF:**` on
    escalation halts, autonomous self-repairs, or multi-file summaries (omitting
    it on clean single-target runs), and gates on prompting for `review` or
    `goldfish`.
-   **Step 4 (Mean Code Review):** Upon `review` or `goldfish`, the agent adopts
    the **Goldfish (Reviewer via Subagent)** persona (spawning via the harness's
    fresh-context subagent tool or stopping if none is available), enforces a
    strictly binary review response (findings only vs. explicit `[✅ LGTM]` on
    zero findings), evaluates against the Adversarial Review Rubric (skipping
    pre-review exclusions and accepted `CONTEST` rationales, and suppressing
    stylistic nitpicks), and halts to await the subagent's response.
-   **Step 5 (Post-Review Resolution Gate):** Upon receiving the subagent's
    findings, the agent adopts the **Elephant (Resolver)** persona, keeping
    triage presentation-only without file-editing or VCS tools, opens with a
    plain-English `> **BLUF:**` blockquote (followed by `---`) led by
    **`[🛠️ X FIX | 🛡️ Y CONTEST]`** (or **`[✅ LGTM]`** on a clean pass), triages
    findings into continuous numbered and priority-tagged `[X] [PY]` items
    (`P0`..`P3`) sorted in descending severity order into `PROPOSE FIX` patches
    vs. `CONTEST` items (persisting accepted `CONTEST` rationales in
    `egm_lite_checklist.md` across loops), and prompts for `checklist` or
    fast-path `exec`.
-   **Code References & Non-Sycophantic Posture:** Referenced local files and line
    ranges use clickable links, and responses lead with technical risks or
    defects without flattering adjectives or polite apologies.
