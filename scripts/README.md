# Scripts

## Overview
Build and release helper scripts for the Elephant-Goldfish Model (EGM) runtime packaging pipeline.

## Interface
- [scripts/pack_plugin.py:SHARED] Declares the shared runtime files and glob patterns copied into every bundle.
- [scripts/pack_plugin.py:HOST] Declares the host-specific manifests and assets for the `claude` and `openai` targets.
- [scripts/pack_plugin.py:SKILLS] Lists the seven EGM skills included in every runtime bundle.
- [scripts/pack_plugin.py:REQUIRED_SHARED] Declares the shared and host-required files that every runtime bundle must contain.
- [scripts/pack_plugin.py:build] Builds a portable runtime folder and reproducible ZIP archive from the repository root.
- [scripts/pack_plugin.py:build] Accepts `--target claude` or `--target openai` and an `--output` directory.
- [scripts/pack_plugin.py:build] Copies the shared and host-declared runtime files into the output folder.
- [scripts/pack_plugin.py:build] Writes the runtime folder and ZIP with fixed entry order, timestamps, and permissions.
- [scripts/prepare_release.py:HOST_MANIFESTS] Lists the portable and host manifests whose versions must match the release tag.
- [scripts/prepare_release.py:version_for_tag] Validates the release tag and every shipped manifest version, returning the version without the leading `v`.
- [scripts/prepare_release.py:prepare] Builds versioned runtime archives, a SHA256SUMS checksum manifest, and draft release notes.

## Invariants
- [scripts/pack_plugin.py:build] Refuses to overwrite an existing output folder or archive.
- [scripts/pack_plugin.py:build] Refuses runtime output that contains the source tree.
- [scripts/pack_plugin.py:build] Rejects symlinked runtime paths and resolved paths outside the source root.
- [scripts/pack_plugin.py:build] Rejects a bundle when any `REQUIRED_SHARED` file or host manifest is missing.
- [scripts/pack_plugin.py:build] Rejects runtime packages that declare hooks or MCP/app dependencies.
- [scripts/pack_plugin.py:build] Rejects invalid manifest agent references and unbundled icon or logo references.
- [scripts/prepare_release.py:prepare] Requires a 40-character lowercase hexadecimal source commit and a new output directory.
- [scripts/prepare_release.py:prepare] Removes the destination directory when any archive, checksum, or release-note write fails.

## Side Effects
- [scripts/pack_plugin.py:build] Writes runtime folders and ZIP archives to the output directory.
- [scripts/prepare_release.py:prepare] Writes versioned archives, `SHA256SUMS`, and `RELEASE_NOTES.md`, cleaning up on failure.

## Verification
- Run: `python3 -m pytest`
- Run: `python3 scripts/pack_plugin.py --target claude --output /tmp/egm-release`
- Run: `python3 scripts/prepare_release.py --tag vX.Y.Z --commit <40-character-sha> --output /tmp/egm-release`
