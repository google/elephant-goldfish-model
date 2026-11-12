# Verification and Evaluation Commands for `egm-bootstrap`

Frontmatter and link checks run in `pytest tests/unit` (see [TESTING.md](../../TESTING.md)).

## Concurrency Verification

Use a fixture with at least five worker partitions and several source chunks
per worker. Inspect native launch/completion timestamps: at most two workers
and two scouts per worker may overlap (four scouts total). Repeat with lower
host limits and without nested delegation: excess work queues or scouts run
inline, every chunk is still processed, and no workers wait indefinitely for
slots they themselves occupy. At the >15-directory gate, verify that known
scope and concurrency limits are shown and unknown costs remain unknown.

## Manual Verification Scenarios

1. **Small Tree Execution (Sequential)**:
   - Target a directory with 2-5 subdirectories.
   - Verify that the root processes directories sequentially; read-only scouts may still be delegated.
   - Verify generated `README.md` files contain Interface, Invariants, Side Effects, and relative links.
2. **Safety Gate Threshold (>15 Subdirectories)**:
   - Target a directory with 16+ subdirectories.
   - Verify that discovery pauses upon reaching >15 directories and requests user confirmation in chat before proceeding.
3. **Inline Scout Fallback**:
   - Run in an environment without task delegation tools.
   - Verify that the agent reads source files and performs the scout steps inline, then generates and checks the contracts.
   - Repeat with more than 15 directories and verify that the user confirmation gate still applies.
