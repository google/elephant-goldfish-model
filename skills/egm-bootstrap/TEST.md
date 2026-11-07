# Verification and Evaluation Commands for `egm-bootstrap`

Frontmatter and link checks run in `pytest tests/unit` (see [TESTING.md](../../TESTING.md)).

## Manual Verification Scenarios

Before using a project formatter, verify that its configured presence alone
does not authorize execution. With no explicit approval (including a headless
run), inspect native tool traces: no formatter, package installation, or
repository configuration/plugin code may execute. Formatting must continue
through file edits. Repeat with approval for one exact formatter command and
verify that only the authorized command runs.

1. **Small Tree Execution (Sequential)**:
   - Target a directory with 2-5 subdirectories.
   - Verify that the agent executes sequentially without spawning subagents.
   - Verify generated `README.md` files contain Interface, Invariants, Side Effects, and relative links.
2. **Safety Gate Threshold (>15 Subdirectories)**:
   - Target a directory with 16+ subdirectories.
   - Verify that discovery pauses upon reaching >15 directories and requests user confirmation in chat before proceeding.
3. **Subagent Halting Gate**:
   - Run in an environment without task delegation tools.
   - Verify that the prominent halting banner is displayed and execution stops immediately.
