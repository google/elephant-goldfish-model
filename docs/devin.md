# Devin CLI and Devin Desktop

Experimental local integration. The package shares EGM's seven skills and ten
personas. Cloud sessions are outside this integration's scope.

## Build and install

From this checkout, build a runtime directory into a new output folder:

```sh
python3 scripts/pack_plugin.py --target devin --output /tmp/egm-devin-build
devin plugins install --local /tmp/egm-devin-build/egm-devin
devin plugins info egm
```

Keep the runtime directory: local installation links to it. Restart the local
session after changing the package. To remove it, run
`devin plugins remove egm --local`.

Use the built runtime rather than installing the repository root. Devin injects
a plugin's root `AGENTS.md` into sessions; the repository's file is for contributors.
The builder replaces it with the Devin runtime instructions and omits development
files and Claude-specific agent adapters. `.devin-plugin/plugin.json` takes
precedence over the portable root manifest. Metadata comes from `plugin.json`.

## Use

In CLI, invoke `/egm:egm-brainstorm`, `/egm:egm-draft`, or `/egm:egm-review`.
In Devin Desktop, start a local session on this machine, inspect the plugin and
skills in Open Customizations, and use the same namespaced commands.
Confirm `egm` is visible before starting. Desktop discovery needs separate live
verification; do not assume a CLI install proves Desktop execution.

Devin's `run_subagent` creates independent conversation chains; use
`read_subagent` as exposed by the session to retrieve results. Native plugin
profiles use the `egm:` namespace and persona frontmatter names. When a named
profile is unavailable, dispatch an explore subagent to read `agents/<file>.md`
from the installed runtime. Use direct dispatch when nesting is unavailable.
If subagents are disabled by settings or organization policy, stop Goldfish
reviews. Never perform the review in the drafting conversation.

The shared personas request read-only behavior but do not declare Devin tool
allowlists. Do not claim these prompts enforce tool permissions. Prefer the
built-in read-only explore profile when enforced read-only tools are needed.
Fresh parent-turn isolation does not establish exclusion of project or user rules.

## Recorded discovery

On 2026-11-08, Devin CLI 3000.11.234 installed the generated runtime locally.
`devin plugins info egm` listed seven skills, ten named profiles, and the runtime
`AGENTS.md` rule. Desktop and end-to-end workflow checks remain unverified.

## Verification checklist

Record the Devin version and surface separately for each run:

1. Inspect `devin plugins info egm` and `devin skills list`: all seven skills
   should resolve, with the runtime rule rather than contributor rules.
2. In a disposable project, run brainstorm, draft, and all five review phases.
   Confirm persona and document-standard reads resolve inside the runtime.
3. Put a unique sentinel in the parent conversation, never in the review task.
   Inspect reviewer traces for parent-turn isolation, independently of host rules.
4. Check named profile registration, read-only tool restrictions, and direct
   dispatch when nesting is unavailable. Record actual tools and failures.
5. Disable subagents and verify reviews stop without producing a review verdict.
6. Repeat discovery and workflow checks in Desktop local sessions.

Packaging and discovery alone do not qualify this harness as supported.

## References

- [Devin plugin format and installation](https://docs.devin.ai/cli/extensibility/plugins/overview)
- [Devin subagents and permissions](https://docs.devin.ai/cli/subagents)
