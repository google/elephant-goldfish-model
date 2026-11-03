# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Keep the Pi package's copies of the shared bundle identical to the source.

Pi resolves package resources inside the package root, so `distributions/pi/`
carries its own copies of the skills, personas, document standards, and runtime
docs. Those copies, and the metadata in `distributions/pi/package.json`, must
match the canonical files at the repository root.

`--check` reports drift without writing. `--write` copies the canonical files
again. Hand-written Pi files are never rewritten, and this script never deletes
anything: an unexpected file inside the package is reported as an error so a
person decides what to do with it.
"""

import argparse
import json
from pathlib import Path
import re
import sys

COPY = (
    "LICENSE",
    "skills/*/SKILL.md", "skills/*/references/*.md",
    "skills/*/references/*.json",
    "agents/*.md", "resources/*.md", "resources/document_standards/*.md",
    "docs/claude.md", "docs/codex.md", "docs/faq.md", "docs/getting_started.md",
    "docs/harnesses.md", "docs/index.md", "docs/muse.md", "docs/privacy.md",
    "docs/releases.md",
)
HAND_WRITTEN = ("package.json", "PORTING-NOTES.md", "README.md",
                "subagents/*.md")
# Markdown written or copied into the package: every relative reference in it
# must resolve inside the package, because a reader has no repository above it.
REFERENCE_SOURCES = "*.md"
# A porting note documents the checkout around the package, so it may link into
# the repository. It is the only file allowed a target outside the package root.
ESCAPE_EXEMPT = frozenset({"PORTING-NOTES.md"})
REFERENCE_SCHEMES = ("http://", "https://", "mailto:", "file://", "//")
LINK_PATTERN = re.compile(r"\]\(([^)]+)\)")
ATTRIBUTE_PATTERN = re.compile(
    r"""(?:src|href)\s*=\s*["']([^"']+)["']""")
SKILLS = (
    "egm-bootstrap", "egm-brainstorm", "egm-draft", "egm-drift-report",
    "egm-resolve", "egm-review", "egm-review-loop",
)
PERSONAS = (
    "bootstrap_orchestrator", "codebase_details", "comprehension",
    "design_critic", "implementation_readiness", "structural", "style",
    "synthesizer", "zoom_out",
)
STANDARDS = (
    "feature-spec", "heilmeier", "implementation-readiness",
    "re-implementation", "zoom-out",
)
# Metadata fields the Pi manifest repeats from the canonical portable manifest.
METADATA = ("name", "version", "description", "homepage", "repository", "license")


def expected_files(root: Path) -> dict[str, bytes]:
  """Map every copied package path to the canonical bytes it must hold."""
  files = {}
  for pattern in COPY:
    for path in sorted(root.glob(pattern)):
      if path.is_file():
        files[path.relative_to(root).as_posix()] = path.read_bytes()
  for name in (f"skills/{skill}/SKILL.md" for skill in SKILLS):
    if name not in files:
      raise ValueError(f"Missing canonical file: {name}")
  if not files:
    raise ValueError(f"No canonical files found under {root}")
  return files


def references(text: str) -> list[str]:
  """Return the relative targets a Markdown file asks the reader to open."""
  return [match.group(1).strip() for match in LINK_PATTERN.finditer(text)] + [
      match.group(1).strip() for match in ATTRIBUTE_PATTERN.finditer(text)
  ]


def is_external(target: str) -> bool:
  """Say whether a target is an anchor, absolute, templated, or off-host."""
  return (
      not target
      or target.startswith(("#", "/", "$"))
      or target.startswith(REFERENCE_SCHEMES)
      # Templates, placeholders, and bracketed examples are not real paths.
      or any(char in target for char in "{}<>[]")
  )


def reference_problems(package: Path) -> list[str]:
  """Fail on a relative reference an installed package cannot resolve.

  Copied bytes can be correct while a reference inside them points at a file
  the package does not carry. Resolve each target from the referencing file and
  require it on disk inside the package root, so a checkout that happens to
  surround the package cannot satisfy a link the installed package lacks.
  `ESCAPE_EXEMPT` names the only file allowed to link outside the root.
  """
  problems = []
  root = package.resolve()
  for source in sorted(package.rglob(REFERENCE_SOURCES)):
    if not source.is_file():
      continue
    relative_source = source.relative_to(package).as_posix()
    for target in references(source.read_text(encoding="utf-8")):
      if is_external(target):
        continue
      relative = target.split("#", 1)[0]
      if not relative:
        continue
      resolved = (source.parent / relative).resolve()
      if not resolved.exists():
        problems.append(
            f"{relative_source}: unresolved reference: {target}")
      elif not resolved.is_relative_to(root) and relative_source not in ESCAPE_EXEMPT:
        problems.append(
            f"{relative_source}: reference escapes the package: {target}")
  return problems


def manifest_problems(root: Path, package: Path) -> list[str]:
  """Check Pi manifest metadata and resource declarations."""
  try:
    pi_manifest = json.loads((package / "package.json").read_text())
  except (OSError, ValueError) as error:
    return [f"distributions/pi/package.json: {error}"]
  canonical = json.loads((root / "plugin.json").read_text())
  problems = [
      f"package.json {field} does not match plugin.json: "
      f"{pi_manifest.get(field)!r} != {canonical.get(field)!r}"
      for field in METADATA
      if pi_manifest.get(field) != canonical.get(field)
  ]
  if pi_manifest.get("author") != canonical.get("author"):
    problems.append("package.json author does not match plugin.json")
  if "pi-package" not in pi_manifest.get("keywords", []):
    problems.append("package.json keywords must include pi-package")
  if pi_manifest.get("pi", {}).get("skills") != ["./skills"]:
    problems.append('package.json pi.skills must be ["./skills"]')
  return problems


def content_problems(root: Path, package: Path) -> list[str]:
  """Check copied bytes, hand-written coverage, and stray files."""
  problems = []
  files = expected_files(root)
  for relative, data in files.items():
    target = package / relative
    if not target.is_file():
      problems.append(f"missing: {relative}")
    elif target.read_bytes() != data:
      problems.append(f"differs from source: {relative}")
  required = [f"agents/{name}.md" for name in PERSONAS] + [
      f"resources/document_standards/{name}-standard.md" for name in STANDARDS
  ] + list(HAND_WRITTEN)
  for relative in required:
    if not list(package.glob(relative)):
      problems.append(f"missing: {relative}")
  known = set(files)
  for pattern in HAND_WRITTEN:
    known.update(path.relative_to(package).as_posix()
                 for path in package.glob(pattern))
  stray = sorted(path.relative_to(package).as_posix()
                 for path in package.rglob("*")
                 if path.is_file()
                 and path.relative_to(package).as_posix() not in known)
  problems.extend(f"unexpected file: {name}" for name in stray)
  return problems


def write(root: Path, package: Path) -> list[str]:
  """Copy the canonical files into the package and report what changed."""
  changed = []
  for relative, data in expected_files(root).items():
    target = package / relative
    if target.is_file() and target.read_bytes() == data:
      continue
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    changed.append(relative)
  return changed


def main(argv: list[str] | None = None) -> int:
  """Return nonzero when the package differs from a clean copy."""
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--check", action="store_true",
                      help="report drift without writing (default)")
  parser.add_argument("--write", action="store_true",
                      help="copy the canonical files into distributions/pi")
  args = parser.parse_args(argv)
  root = Path(__file__).resolve().parents[1]
  package = root / "distributions" / "pi"
  if not package.is_dir():
    print(f"Missing package directory: {package}", file=sys.stderr)
    return 1
  if args.write:
    for relative in write(root, package):
      print(f"wrote: {relative}")
  problems = manifest_problems(root, package) + content_problems(root, package)
  problems += reference_problems(package)
  for problem in problems:
    print(problem, file=sys.stderr)
  if problems:
    return 1
  print("Pi package matches the canonical bundle and its manifest metadata.")
  return 0


if __name__ == "__main__":
  sys.exit(main())
