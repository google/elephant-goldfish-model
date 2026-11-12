<!--
Copyright 2026 Google LLC.
SPDX-License-Identifier: Apache-2.0
-->

# Unsupported Source Check

The Root Orchestrator runs this check once, before discovery.

1.  Run this command, replacing `<path>` with the target `path`:

    ```sh
    (cd "<path>" && { git ls-files -z --cached --others --exclude-standard 2>/dev/null ||
        find . -type f -print0; } | tr '\0' '\n' | sed 's|^\./||' |
      grep -Ev '(^|/)(\.|(node_modules|venv|dist|build|third_party)/)' |
      awk -F/ '$NF ~ /\.[^.]+$/ { e = $NF; sub(/.*\./, ".", e); n[e]++
        if (!(e in x)) x[e] = $0 } END { for (e in n) print n[e], e, x[e] }' |
      sort -rn)
    ```

    Each line gives a file count, an extension, and an example path. The listing
    honors `.gitignore` in a Git work tree, skips hidden and system directories
    as discovery does, and includes test directories.

    If this command cannot run in your shell (for example, PowerShell), produce
    the same per-extension counts with an equivalent command and the same
    exclusions. If you cannot, tell the user the check was skipped.

2.  Collect the extensions that look like source code (a programming, query, or
    schema language) but are not listed under *Source Code Files* in `SKILL.md`.
    Skip documentation, data, media, manifests, and lockfiles (for example `.md`,
    `.json`, `.yaml`, `.toml`, `.csv`, `.png`). When unsure, collect it.

3.  If any were collected, ask the user this question as written (using a
    structured question tool, if your harness has one, or plain chat), then
    wait for the answer.

    *   `question`: "This codebase contains source files that egm-bootstrap
        does not support: [`.ext` (N files, e.g. `path`), ...]. EGM has not been
        tuned for these languages. Do you still want to proceed?"
    *   `options`: `["Yes, proceed anyway", "No, abort execution"]`
    *   If the user selects abort, terminate execution immediately.
