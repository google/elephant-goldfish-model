# Test Plan: EGM Ask Skill

Frontmatter and link checks run in `pytest tests/unit` (see [TESTING.md](../../TESTING.md)).

## Protocol Verification Checklist

When evaluating `egm-ask` interactively in chat, verify:

-   **Read-only:** The skill creates, edits, and deletes no file, runs no shell
    command other than `ls` and `cat`, spawns no subagent, and runs no other
    skill.
-   **Step 1 (Classify):** Each question is sorted into Next step, Skill
    choice, Troubleshooting, or Out of scope, and only that row's files are
    read. An empty question is treated as Next step.
-   **Step 2 (Stage):** Artifacts are found by name in the working directory
    (or `EGM artifact directory:`), the harness artifact directory, then
    `scratch/`. The only workspace content read is the `Status: resolved` and
    `**Target:**` lines of `goldfish_review_report.md`. The stage comes from the
    "What to Run Next" table in `docs/getting_started.md`.
-   **Hints, not proof:** Review reports lead to a question about whether the
    review finished. Unclear cases are reported as unknown with the artifacts
    listed.
-   **Before implementation:** Implementation is suggested only after the
    target design is confirmed, no review is pending, and the user confirms
    approval.
-   **Pending steps:** While another skill waits for an answer, the skill
    answers the question, picks no option, and tells the user to answer the
    pending step directly.
-   **Reply:** Plain English, at most three next steps and 20 lines. Commands
    use the harness's form (`/egm:egm-<name>` in Claude Code) and every source
    is listed.

## Manual Setup

Run each case from an empty scratch folder with the EGM plugin installed.
Create only the artifact files the case names; their contents can be empty,
except `goldfish_review_report.md`, which needs a `**Target:**` line and,
for resolved cases, a first line `Status: resolved`.
