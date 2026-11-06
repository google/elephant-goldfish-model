# Antigravity runtime packaging

- **Author:** @aaravkhanal
- **Status:** Proposal. Maintainer scope approval and design review pending.
- **Date:** 2026-11-05
- **Tracking:** [Antigravity strict validation #272](
  https://github.com/google/elephant-goldfish-model/issues/272)

## Problem and goals

The repository root is both EGM's development checkout and the current
Antigravity plugin source. Installing that tree copies contributor files into
the plugin. In particular, `AGENTS.md` is repository guidance, but Antigravity
interprets a plugin-root `AGENTS.md` as misplaced rule content; moving it to
`rules/AGENTS.md` would load EGM contributor instructions in users' workspaces.
The root manifest also lacks the top-level `logo` field Antigravity recommends.

The repository already has an allowlisted runtime package. On Antigravity CLI
1.4.12, installing a fresh `pack_plugin.py --target openai` output in a scratch
home registered 7 skills and 9 agents. The installed tree matched the generated
tree byte for byte. Strict validation reported only the logo hint on both
trees; adding a top-level `logo` to a copy of `plugin.json` cleared that hint.
The repository root still fails strict validation on `AGENTS.md`, as reported
in #272.

Use the existing allowlisted OpenAI runtime output as the Antigravity install
source, add the shared top-level logo metadata, and update all documented
Antigravity install paths to use the generated output. Keep the root
`AGENTS.md` available to contributors and out of installed plugins.

Strict validation applies to the generated runtime and installed plugin. The
development checkout itself is not a distributable runtime and is not required
to pass strict validation while it contains contributor files. This adjusts
the root-check expectation in #272; maintainers must confirm this scope before
implementation. Do not describe #272 as fully fixed until the generated
runtime validates and the documented install paths use it.

## Scope

Goals:

- Reuse `scripts/pack_plugin.py --target openai` and its existing allowlist.
  Do not add a separate Antigravity target or duplicate runtime inventory.
- Add a top-level `logo` field to the canonical root `plugin.json`, pointing to
  the bundled `assets/icon.svg`, and verify that it remains compatible with
  all current consumers. The field will be included in both generated runtime
  packages because the root manifest is shared.
- Update every Antigravity install guide: the CLI command in `README.md` and
  `docs/harnesses.md`; the Antigravity App and IDE manual copy steps in
  `docs/harnesses.md`; and the generated copy at
  `distributions/claude/README.md` and
  `distributions/claude/docs/harnesses.md`.
- Build the OpenAI runtime, validate that generated directory with
  `agy plugin validate --strict`, and install that directory rather than the
  unfiltered repository root.
- Test metadata and asset references, runtime contents and exclusions,
  generated distribution freshness, and existing OpenAI/Claude package behavior.
- Record native `agy` validation and installation results with the exact CLI
  version. Keep native verification outstanding if the CLI is unavailable.

Non-goals:

- Moving, renaming, or copying `AGENTS.md` into `rules/`.
- Changing Antigravity's validator or suppressing its warning in EGM.
- Adding an Antigravity-specific target, manifest fork, skill fork, or persona
  fork to the packager.
- Adding hooks, MCP servers, or permission changes.
- Claiming full Antigravity support from package validation alone. The existing
  end-to-end workflow and isolation gates still apply.
- Publishing an Antigravity Marketplace listing or generated release artifact.
- Changing Claude or OpenAI package contents or support claims, except for the
  shared top-level manifest field described in this design.

## Package and manifest contract

Use the existing `--target openai` package as the allowlisted Antigravity
runtime. Its generated output excludes root contributor instructions and
other development-only files while preserving shared skills, agents,
resources, guides, assets, and license files. Keep the current package layout
and output naming; do not add a third target or independently maintained file
inventory for Antigravity.

Add the top-level `logo` field to root `plugin.json` with a relative reference
to `assets/icon.svg`. The icon is already included by the shared allowlist.
Keep host-specific `extensions.com.openai.interface` metadata intact. Extend
`scripts/pack_plugin.py` to validate the top-level logo reference for both
package targets, so missing or unbundled logo paths fail the build. Test the
root and packaged manifest references alongside the existing host manifest
checks. Regenerate `distributions/claude` from the packager after shared
manifest and guide changes; do not edit generated files independently.

## Installation and validation

The Antigravity CLI flow builds the existing OpenAI runtime from a checkout,
validates the generated `egm-openai/` directory with
`agy plugin validate --strict`, then installs that directory with
`agy plugin install`. The README and harness guide must no longer direct CLI
users to install the unfiltered repository root.

For the Antigravity App and IDE, document copying the generated runtime's
contents into `~/.gemini/config/plugins/egm/` instead of copying the full
checkout. State that building requires a local checkout and Python. Do not
imply that a generated directory is available directly from the GitHub
repository until a separate release path exists.

This changes the README's one-command GitHub install into a local clone, build,
validation, and install sequence. A later generated branch or release could
restore a one-command URL install. Keep that publication path out of this
proposal; the existing [Claude release branch design](claude_release_branch_distribution.md)
is a reference for a separate design.

The generated directory and installed plugin must contain the same runtime
files and metadata. Inspect the installed plugin identity and discovered
skills after installation. Root validation may continue to report contributor
files by design; do not claim it passes strict validation.

## Alternatives

| Option | Decision |
| --- | --- |
| Move contributor `AGENTS.md` to `rules/AGENTS.md` | Reject. It would turn repository contribution policy into an always-on rule for plugin users. |
| Remove or rename the root contributor instructions | Reject unless maintainers explicitly decide how contributors will receive the same guidance. |
| Add a third Antigravity package target | Not needed if the existing OpenAI runtime output validates and installs correctly after the shared logo field is added. Reconsider only if native install testing finds a host-specific package requirement. |
| Add only a top-level logo and keep installing the full checkout | Insufficient. It clears the metadata hint but leaves strict validation failing on root `AGENTS.md`. |
| Reuse the existing OpenAI runtime output with shared logo metadata | Preferred. It uses the tested allowlist, avoids duplicate packaging logic, and keeps contributor files out of the installed plugin. Until a release path exists, CLI users clone and build locally instead of installing from one URL. |
| Publish the generated runtime to a branch or release and keep `agy plugin install <URL>` | Defer. It preserves the one-command install but needs a publication path like the [Claude release branch design](claude_release_branch_distribution.md). |

## Implementation and acceptance gates

This proposal changes no manifests, packaging code, installation instructions,
generated distributions, or support claims. After maintainers approve the
scope and this design is reviewed and merged, a separate implementation PR
may:

1. Add the top-level logo to the canonical manifest and verify the field and
   asset across all existing package targets.
2. Update the README, `docs/harnesses.md`, and generated
   `distributions/claude/README.md` and
   `distributions/claude/docs/harnesses.md` for CLI, App, and IDE installation.
3. Regenerate the Claude distribution and test freshness, links, package
   contents, metadata references, logo-path rejection, and existing host
   manifests.
4. Repeat `agy plugin validate --strict` and installation on the generated
   OpenAI runtime using a recorded CLI version. Both passed on 1.4.12 for the
   current runtime files; repeat after implementation changes and confirm the
   logo hint is gone. If native tests cannot run, mark them not run and do not
   claim #272 is fully resolved.
5. Run the required Antigravity brainstorm, draft, and review workflows before
   changing support status.

The maintainer must confirm the revised acceptance criterion for #272: strict
validation of the generated/installed runtime is required; strict validation
of the development checkout root is not. If that criterion is not accepted,
pause implementation and record the maintainer-selected approach instead of
changing contributor instructions implicitly.
