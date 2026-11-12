# Directory packages

Build a runtime folder and ZIP using only Python's standard library:

```sh
python3 scripts/pack_plugin.py --target claude --output /tmp/egm-release
python3 scripts/pack_plugin.py --target openai --output /tmp/egm-release
```

The output contains `egm-claude/` and `egm-claude.zip`, or `egm-openai/`
and `egm-openai.zip`. Existing outputs are refused. ZIP entry order,
timestamps, and permissions are fixed; identical inputs produce identical
archives on the same Python/zlib runtime.

The allowlist includes skill instructions and references, personas, standards,
runtime guides, manifests, and icons. It excludes the site, tests, workflows,
marketplace catalogs, hooks, and build tools. Claude retains its native agent
adapters; OpenAI excludes Claude components. Runtime files are nonexecutable.
Symlinked runtime paths and escaping manifest references are rejected.
Contributor instructions, the AI policy, and the Markdown PR template are
excluded. Runtime documentation links to their repository copies.
No workflow configuration ships.
The runtime guide list is explicit. New host guides do not enter these archives
until their package requirements are reviewed.

Do not commit the generated runtime or ZIPs to `main`. The Claude marketplace
catalog installs from the repository root, so a second copy would add a nested
Claude manifest that Cowork rejects. For Anthropic's directory, the portal reads
a repository, plugin path, and tracked branch. It does not accept a ZIP. Publish
the runtime to a generated branch as described in
[Claude release-branch distribution](designs/claude_release_branch_distribution.md)
before submitting.
For OpenAI, upload `egm-openai.zip`. Build output
alone does not establish installation, workflow support, or directory approval.
