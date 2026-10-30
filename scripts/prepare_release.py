# Copyright 2026 Google LLC. SPDX-License-Identifier: Apache-2.0
"""Build versioned runtime archives and a checksum manifest for a draft release."""

import argparse
import hashlib
import json
from pathlib import Path
import re

from pack_plugin import build


def version_for_tag(root: Path, tag: str) -> str:
    """Returns the tag version after validating all shipped manifests.

    Args:
        root: Repository root containing the portable and host manifests.
        tag: Release tag in vMAJOR.MINOR.PATCH format, without leading zeroes.

    Returns:
        The version without the leading v.

    Raises:
        ValueError: The tag is invalid or a manifest version does not match it.
    """
    if not re.fullmatch(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", tag):
        raise ValueError("Tag must be vMAJOR.MINOR.PATCH without leading zeroes")
    version = tag[1:]
    for relative in ("plugin.json", ".claude-plugin/plugin.json",
                     ".codex-plugin/plugin.json"):
        manifest = json.loads((root / relative).read_text(encoding="utf-8"))
        if manifest.get("version") != version:
            raise ValueError(f"{relative}: version must match {tag}")
    return version


def prepare(root: Path, tag: str, output: Path, commit: str) -> None:
    """Builds runtime archives, checksums, and draft notes in a new directory.

    Args:
        root: Repository root containing the runtime sources and manifests.
        tag: Release tag matching every shipped manifest version.
        output: New destination directory; an existing candidate is never replaced.
        commit: Caller-declared source identity as 40 lowercase hexadecimal digits.
            This function does not verify that it identifies the source checkout.

    Raises:
        ValueError: The tag, manifest versions, commit, or runtime inputs are invalid.
        FileExistsError: The destination already exists.
        OSError: Reading sources, building archives, or writing output fails.
    """
    version = version_for_tag(root, tag)
    if len(commit) != 40 or any(char not in "0123456789abcdef" for char in commit):
        raise ValueError("Source commit must be a full Git SHA")
    output.mkdir(parents=True, exist_ok=False)
    checksums = []
    for target in ("claude", "openai"):
        _, archive = build(root, target, output / "build")
        destination = output / f"egm-{target}-{version}.zip"
        archive.rename(destination)
        digest = hashlib.sha256(destination.read_bytes()).hexdigest()
        checksums.append(f"{digest}  {destination.name}\n")
    (output / "SHA256SUMS").write_text("".join(checksums), encoding="utf-8")
    (output / "RELEASE_NOTES.md").write_text(
        f"# EGM {version}\n\nDeclared source: `{commit}`\nTag: `{tag}`\n\n"
        "Local source identity is caller-supplied and is not verified by this script. "
        "Publish only workflow-built candidates after exact-artifact checks.\n\n"
        "Runtime archives: Claude and OpenAI. Verify downloads with "
        "`sha256sum -c SHA256SUMS`.\n\n"
        "For CI-built candidates, verify each ZIP with "
        "`gh attestation verify FILE --repo google/elephant-goldfish-model "
        "--signer-workflow google/elephant-goldfish-model/.github/workflows/release.yml "
        "--source-ref refs/heads/main`. "
        "Provenance identifies the main-branch workflow run; the tagged source "
        "commit is recorded above. Local builds have no attestation.\n\n"
        "## Changes\n\nMaintainer: summarize changes and migration steps before publishing.\n\n"
        "## Verification\n\nOffline unit tests and runtime packaging are checked by CI. "
        "Live installation, workflow execution, reviewer isolation, directory approval, "
        "and cloud-host support are not established by this build. "
        "Maintainer: attach exact-bundle host evidence and limitations before publishing.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prepare(Path(__file__).resolve().parents[1], args.tag, args.output, args.commit)
