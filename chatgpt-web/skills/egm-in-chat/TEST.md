# Test Plan: EGM in Chat

Frontmatter, scenario, and packaging checks run in `pytest tests/unit` (see [TESTING.md](../../../TESTING.md)).

## Protocol Verification Checklist

When evaluating `egm-in-chat` in a web chat host, verify:

-   **Intake:** Asks whether the goal is to explore an idea, shape a plan, or
    review a document. Needs no terminal, repository, or local files.
-   **Same-context disclosure:** Ends each critique with a one-line
    same-context disclosure. Never claims independent or Goldfish review.
-   **Decision:** Recomputes totals and dates from the document's own figures,
    holds only for a blocker, and does not phrase a fix as a precondition.
-   **Missing capability:** When asked to inspect a repository or run
    independent reviewers, says the host cannot, narrows the task, and points
    to full EGM.
