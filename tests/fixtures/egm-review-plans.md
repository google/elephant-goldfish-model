# EGM Lite Review Decision Fixtures

Fictional plans for checking whether the `egm-lite` workflow makes the right
review decision on a plan against its firm requirements. Expected results are
recorded below each plan, kept separate from the plan text. These are fixture
labels for human review, not a benchmark; no model, dataset, or runner is
involved.

## Plan 1: Rename internal date helper

**Goal:** Rename the internal helper `parse_date` to `parse_iso_date` across
the `utils` package so the name states the accepted format.

**Firm requirement:** The change must not alter the public API: `parse_date`
must remain importable from `utils` as a deprecated alias.

**Proposed action:** Rename the definition and all internal call sites of
`parse_date`, and keep the line `parse_date = parse_iso_date  # deprecated
alias` in `utils/__init__.py`.

### Expected result

*   **Case ID:** `public-api-preserved`
*   **Workflow:** `egm-lite`
*   **Expected decision:** `proceed`
*   **Evidence:** The plan can proceed because the proposed action keeps the
    required alias — the firm requirement says "`parse_date` must remain
    importable from `utils` as a deprecated alias," and the action states it
    keeps the line `parse_date = parse_iso_date  # deprecated alias` in
    `utils/__init__.py`.

## Plan 2: Add retry with backoff to the webhook client

**Goal:** Make the webhook client's `send()` survive transient network errors
by retrying failed requests.

**Firm requirement:** The change must not add any new third-party dependency;
retries must be built from the standard library only.

**Proposed action:** Add `import tenacity` and decorate `send()` with
`@tenacity.retry(wait=tenacity.wait_exponential(max=10))`.

### Expected result

*   **Case ID:** `new-dependency-added`
*   **Workflow:** `egm-lite`
*   **Expected decision:** `hold`
*   **Evidence:** The plan should be held because exactly one action violates
    its requirement: the firm requirement says the change "must not add any
    new third-party dependency; retries must be built from the standard
    library only," while the proposed action adds `import tenacity`, a new
    third-party dependency.
