# Copyright 2026 Google LLC. SPDX-License-Identifier: Apache-2.0
"""Build versioned runtime archives and a checksum manifest for a draft release."""

import argparse
import hashlib
import json
from pathlib import Path
import re

from pack_plugin import build


def version_for_tag(root: Path, tag: str) -> str:
    """Require a normal vMAJOR.MINOR.PATCH tag matching every shipped manifest."""
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
    """Build into a new directory; never overwrite a previous candidate."""
    version = version_for_tag(root, tag)
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
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
        f"# EGM {version}\n\nSource: `{commit}`\nTag: `{tag}`\n\n"
        "Runtime archives: Claude and OpenAI. Verify downloads with "
        "`sha256sum -c SHA256SUMS`.\n\n"
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
