# Plugin-Root Path Resolution

Bundled personas (`agents/<file>.md`), standards
(`resources/document_standards/<standard>.md`), and harness guides (`docs/`)
sit at the plugin root. The root is two directories above this skill's
folder (`<plugin-root>/skills/egm-review/`). A fresh Goldfish context cannot
resolve relative plugin paths on its own.

*   **omp**: `skill://` reads cannot leave the skill's own folder. Resolve
    the physical root first. Run `realpath skill://egm-review`. Or read
    `skill://egm-review` and take the physical path from the result header.
    Then read plugin-root files by absolute path. A spawned subagent can do
    the same, because it receives the session's skills.
*   **Claude Code and Cowork**: use the `${CLAUDE_PLUGIN_ROOT}` value already
    substituted in the invoked skill.
*   **Codex and ChatGPT Work**: follow the Codex integration guide at
    `<plugin-root>/docs/codex.md`.

A failed skill-relative lookup does not mean the file is absent from the
plugin. Never substitute files with similar names from the user's project
for bundled personas or standards. Pass each spawned reviewer the absolute
paths of its persona file and its standard. If you cannot find a plugin-root
file after you resolve the root, say so and stop.
