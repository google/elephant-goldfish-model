# Test Plan: EGM in Chat

Frontmatter, scenario, and packaging checks run in `pytest tests/unit` (see [TESTING.md](../../../TESTING.md)).

## Protocol Verification Checklist

Install the same `egm-openai.zip` in clean web and desktop chats. Record its
checksum, version, host version or date, install result, and actual tools.
These manual checks are required before merge; offline tests are insufficient.
On both surfaces, verify:

-   **Intake:** Asks whether the goal is to explore an idea, shape a plan, or
    review a document. Needs no terminal, repository, or local files.
-   **Same-context disclosure:** Ends each critique with a one-line
    same-context disclosure. Never claims independent or Goldfish review.
-   **Decision:** Recomputes totals and dates from the document's own figures,
    holds only for a blocker, and does not phrase a fix as a precondition.
-   **Missing capability:** When the tools required for a full EGM request are
    absent, names the missing tool and offers same-context document work.
-   **Available capability:** When required tools exist, points to full EGM in
    the same plugin. Does not claim tools are absent because the chat is on web.
-   **Full skills:** In a capable desktop chat, run `egm-brainstorm`, `egm-draft`,
    and `egm-review`; retain native isolation evidence. In a restricted chat,
    invoke a full skill and verify it stops before unsupported operations.
