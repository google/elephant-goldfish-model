# Test Plan: Goldfish Review Loop Skill

Frontmatter and link checks run in `pytest tests/unit` (see [TESTING.md](../../TESTING.md)).

## Protocol Verification Checklist

### Resource boundaries

Run these cases in a disposable workspace and inspect native read and
delegation traces, repeating for direct and synthesizer dispatch. Offline
schema checks do not run these cases or establish host enforcement; these
are prompt rules, not a filesystem sandbox.

| Case | Input | Expected evidence |
| --- | --- | --- |
| Canonical resources | `style`, `feature-spec-standard`, then installed absolute paths | Both dispatch modes read the same installed files. |
| Workspace override | A workspace `agents/style.md` with a unique marker | Relative resource paths resolve from the plugin; the workspace file is never read. |
| Escaping resource | `../outside.md`, an outside absolute path, `..\outside.md`, or an installed persona symlink pointing outside | Intake rejects the resource before reading or launching reviewers. |
| Linked context escape | Target links to an outside file, URL, and workspace symlink to an outside file | Interactive intake requests approval before reading/fetching; headless intake omits them and reports omissions. |
| Approved context | User explicitly supplies an outside context file or URL | Read only the approved resource; additional links and redirect destinations undergo the same boundary check. |

### Existing protocol

When evaluating or exploring `egm-review-loop` interactively in chat, verify:

-   **Step 1 (Intake & Config):** Validates required inputs, resolves standard paths, and saves each URL in `GoldfishContext` as a file before the first round, asking for a local copy of any page that cannot be saved.
-   **Step 2.1 (Target Resolution):** Unconditionally re-scans line numbers before auditing.
-   **Step 2.2 (Review Swarm):** Spawns subagents (or sequentially iterates personas in degraded mode) across requested standards.
-   **Step 2.3 & 2.4 (Resolve Handoff & Turn Boundary):** Hands findings to `egm-resolve` and respects human decision gates.
-   **Step 2.4 (Round Control):** Keeps contested and accepted findings settled, re-opens fixed findings that reviewers raise again, judges clean rounds before applying fixes, records failed reviewers (and reviewers with no status in the synthesizer summary) as not run, stops after two consecutive clean rounds, and asks the user at the 5-round cap or on churn.
