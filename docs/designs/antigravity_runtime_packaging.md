# Antigravity runtime packaging

- **Author:** @aaravkhanal
- **Status:** Proposal. Maintainer scope approval and design review pending.
- **Date:** 2026-11-09
- **Tracking:** #272 (Antigravity strict validation)

## Problem and goals

The repository root is both EGM's development checkout and the current
Antigravity plugin source. Installing that tree copies contributor files into
the plugin. In particular, `AGENTS.md` is repository guidance, but Antigravity
interprets a plugin-root `AGENTS.md` as misplaced rule content; moving it to
`rules/AGENTS.md` would load EGM contributor instructions in users' workspaces.
The top-level manifest logo was added by #336. The root checkout still includes
contributor instructions, so strict validation of the full checkout remains a
separate concern from validating a distributable runtime.

The repository already has an allowlisted runtime package. On Antigravity CLI
1.4.12, installing a fresh `pack_plugin.py --target openai` output in a scratch
home registered every packaged skill and agent. The installed tree matched the
generated tree byte for byte. Strict validation reported only the logo hint on
both trees; adding a top-level `logo` to a copy of `plugin.json` cleared that
hint. A later Antigravity CLI 1.5.1 check on a disposable runtime with that logo
passed strict validation and registered all packaged skills and agents. The
repository root still warns about `AGENTS.md`, as reported in #272. These
results predate #336's logo change; strict validation of a runtime built from
the current `main` has not yet been recorded.

Use the existing allowlisted OpenAI runtime output as the Antigravity install
source and update all documented Antigravity install paths to use the generated
output. Keep the root `AGENTS.md` available to contributors and out of
installed plugins.

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
- Verify that the top-level `logo` field added by #336 points to the bundled
  `assets/icon.svg` and remains compatible with both existing package targets.
  Test that the packager rejects a missing or unbundled top-level logo path.
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
- Changing skill or persona contents, or changing Claude/OpenAI support claims.

## Package and manifest contract

Use the existing `--target openai` package as the allowlisted Antigravity
runtime. Its generated output excludes root contributor instructions and
other development-only files while preserving shared skills, agents,
resources, guides, assets, and license files. Keep the current package layout
and output naming; do not add a third target or independently maintained file
inventory for Antigravity.

The root `plugin.json` already has a top-level logo from #336, pointing to
`assets/icon.svg`, which the shared allowlist includes. Keep host-specific
`extensions.com.openai.interface` metadata intact. Extend
`scripts/pack_plugin.py` to validate the top-level logo reference for both
package targets, so missing or unbundled logo paths fail the build. Test the
root and packaged manifest references alongside existing host manifest
checks. Regenerate `distributions/claude` from the packager after guide
changes; do not edit generated files independently.

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
proposal; the existing
[Claude release branch design](claude_release_branch_distribution.md) is a
reference for a separate design.

The generated directory and installed plugin must contain the same runtime
files and metadata. Inspect the installed plugin identity and discovered
skills after installation. Root validation may continue to report contributor
files by design; do not claim it passes strict validation.

## Alternatives

| Option | Decision |
| --- | --- |
| Move contributor `AGENTS.md` to `rules/AGENTS.md` | Reject. It would turn repository contribution policy into an always-on rule for plugin users. |
| Remove or rename the root contributor instructions | Reject unless maintainers explicitly decide how contributors will receive the same guidance. |
| Add a third Antigravity package target | Not needed if the existing OpenAI runtime output validates and installs correctly. Reconsider only if native install testing finds a host-specific package requirement. |
| Add only a top-level logo and keep installing the full checkout | Insufficient. The logo is already present after #336, while root `AGENTS.md` still triggers strict validation. |
| Reuse the existing OpenAI runtime output | Preferred. It uses the tested allowlist, avoids duplicate packaging logic, and keeps contributor files out of the installed plugin. Until a release path exists, CLI users clone and build locally instead of installing from one URL. |
| Publish the generated runtime to a branch or release and keep `agy plugin install <URL>` | Defer. It preserves the one-command install but needs a publication path like the [Claude release branch design](claude_release_branch_distribution.md). |

## Implementation and acceptance gates

This proposal changes no manifests, packaging code, installation instructions,
generated distributions, or support claims. After maintainers approve the
scope and this design is reviewed and merged, a separate implementation PR
may:

1. Verify that the top-level logo from #336 is included in both generated
   packages, and add packager validation for missing or unbundled logo paths.
2. Update the README, `docs/harnesses.md`, and generated
   `distributions/claude/README.md` and
   `distributions/claude/docs/harnesses.md` for CLI, App, and IDE installation.
3. Regenerate the Claude distribution and test freshness, links, package
   contents, metadata references, logo-path rejection, and existing host
   manifests.
4. Run `agy plugin validate --strict` and install the generated OpenAI runtime
   using a recorded CLI version. Strict validation and installation passed on
   1.4.12 before #336; validation passed on a disposable logo-enabled runtime
   on 1.5.1. Repeat both against the implementation output and verify the logo
   renders in the App. If native tests cannot run, mark them not run and do not
   claim #272 is fully resolved.
5. Run the required Antigravity brainstorm, draft, and review workflows before
   changing support status.

The maintainer must confirm the revised acceptance criterion for #272: strict
validation of the generated/installed runtime is required; strict validation
of the development checkout root is not. If that criterion is not accepted,
pause implementation and record the maintainer-selected approach instead of
changing contributor instructions implicitly.
