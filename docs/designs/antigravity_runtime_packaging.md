# Antigravity runtime packaging

- **Author:** @aaravkhanal
- **Status:** Proposal. Maintainer scope approval and design review pending.
- **Date:** 2026-11-05
- **Tracking:** [Antigravity strict validation #272](https://github.com/google/elephant-goldfish-model/issues/272)

## Problem and goals

The repository root is both EGM's development checkout and the current
Antigravity plugin source. Installing that tree copies contributor files into
the plugin. In particular, `AGENTS.md` is repository guidance, but Antigravity
interprets a plugin-root `AGENTS.md` as misplaced rule content; moving it to
`rules/AGENTS.md` would load EGM contributor instructions in users' workspaces.
The root manifest also lacks the top-level `logo` field Antigravity recommends.

Provide a tested Antigravity runtime directory that excludes contributor-only
files, carries complete Antigravity metadata, and passes strict validation
before installation. Preserve the shared skills, personas, and standards so
their relative resource reads continue to work. Keep the repository's root
`AGENTS.md` available to contributors.

Strict validation applies to the generated runtime and installed plugin. The
development checkout itself is not a distributable Antigravity runtime and is
not required to pass strict validation while it contains contributor files.
This adjusts the root-check expectation in #272; maintainers must confirm this
scope before implementation. Do not describe #272 as fully fixed until the
installed runtime validates and the documented installation path uses it.

## Scope

Goals:

- Extend the existing allowlist packager with an Antigravity target, reusing
  shared runtime resources without copying the Claude or OpenAI adapters.
- Include an Antigravity-valid manifest and all referenced assets in the
  package. Keep shared identity and version fields aligned with the canonical
  root manifest and test that alignment.
- Exclude root contributor instructions, tests, site content, distribution
  outputs, and development-only files from the Antigravity runtime.
- Document a clean local build, `agy plugin validate --strict`, and install
  flow for the generated directory. Do not claim that direct installation of
  the unfiltered GitHub repository passes strict validation.
- Test package contents, manifest references, metadata consistency, and
  rejection of unsafe paths using offline unit tests.
- Record native `agy` validation and installation results with the exact CLI
  version. Keep native verification outstanding if that CLI is unavailable.

Non-goals:

- Moving, renaming, or copying `AGENTS.md` into `rules/`.
- Changing Antigravity's validator or suppressing its warning in EGM.
- Adding Antigravity-specific skill or persona forks, hooks, MCP servers, or
  permission changes.
- Claiming full Antigravity support from package validation alone. The existing
  end-to-end workflow and isolation gates still apply.
- Publishing an Antigravity Marketplace listing or generated release artifact.
- Changing Claude or OpenAI package contents or support claims.

## Package contract

Add `agy` as a third explicit target in the existing runtime packager, subject
to maintainer approval of this design. The target produces a fresh
`egm-agy/` directory and reproducible `egm-agy.zip`, following the existing
output, path-safety, and overwrite rules. The package contains only the shared
runtime allowlist and the Antigravity manifest/assets it requires. It excludes
the root `AGENTS.md`, development instructions, CI configuration, tests, site,
design documents, and other host adapters.

Use the root `plugin.json` as the starting point for common metadata, then
produce or select an Antigravity-compatible manifest without mutating the
source tree. Add the top-level logo reference required by the current
Antigravity manifest guidance and ensure the referenced asset is packaged.
Do not duplicate canonical metadata by hand; unit tests must fail when shared
identity or version fields drift.

Keep `skills/`, `agents/`, and `resources/` at the plugin root. Preserve every
resource path read by the shared skills, along with the guides and licenses
needed at runtime. Never place EGM development guidance under `rules/`.

## Installation and validation

The documented Antigravity CLI flow builds the runtime from a checkout, runs
`agy plugin validate --strict` against `egm-agy/`, then installs that directory
with `agy plugin install`. It must not install the unfiltered repository root
as the distributable plugin. The guide must state that building requires a
local checkout and Python, and must not imply that a generated directory is
available directly from the GitHub repository until a separate release path
exists.

The generated directory and installed plugin must contain the same runtime
files and metadata. Validate the clean output before installation and inspect
the installed plugin identity and discovered skills after installation. Do
not claim that validating the repository root is a supported check; root
validation may continue to report contributor files by design.

## Alternatives

| Option | Decision |
| --- | --- |
| Move contributor `AGENTS.md` to `rules/AGENTS.md` | Reject. It would turn repository contribution policy into an always-on rule for plugin users. |
| Remove or rename the root contributor instructions | Reject unless maintainers explicitly decide how contributors will receive the same guidance. It would alter the development workflow to satisfy a packaging check. |
| Add only a top-level logo | Insufficient. It removes the metadata hint but leaves strict validation failing on root `AGENTS.md`. |
| Keep installing the full checkout | Reject for strict distribution. It includes development-only content and cannot meet the warning-free validation contract safely. |
| Build an allowlisted Antigravity runtime | Preferred. It preserves the repo instructions while giving users a clean plugin directory to validate and install. |

## Implementation and acceptance gates

This proposal changes no manifests, packaging code, installation instructions,
generated distributions, or support claims. After this design is reviewed and
merged, a separate implementation PR may:

1. Add the `agy` target and its manifest/asset handling to the approved
   packaging design and existing packager tests.
2. Add a root-manifest logo only if it is correct for all current consumers;
   otherwise generate the Antigravity manifest from canonical metadata.
3. Update the Antigravity install guide to build, validate, and install the
   generated runtime, clearly replacing direct full-repository installation.
4. Verify package exclusions, referenced-file inclusion, deterministic output,
   path safety, and metadata parity in unit tests.
5. Run `agy plugin validate --strict` and install the package on a recorded
   supported CLI version. If native tests cannot run, mark them not run and do
   not claim the issue is fully resolved.
6. Run the required end-to-end Antigravity brainstorm, draft, and review
   workflows before changing support status.

The maintainer must confirm the revised acceptance criterion for #272: strict
validation of the generated/installed runtime is required; strict validation
of the development checkout root is not. If that criterion is not accepted,
pause implementation and record the maintainer-selected approach instead of
changing contributor instructions implicitly.
