# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for relative Markdown link integrity."""

import pathlib
import re
from typing import Set

# Vendored trees whose markdown is not ours to validate.
IGNORED_DIRS = ("node_modules",)

IGNORED_SCHEMES = (
    "http://",
    "https://",
    "mailto:",
    "file://",
)

# Matches standard markdown links [text](target)
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^\)]+)\)")
# Matches markdown headers # Heading
HEADER_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


def extract_headers(content: str) -> Set[str]:
  """Extracts normalized slug anchors for headers in a Markdown document."""
  slugs = set()
  for match in HEADER_PATTERN.finditer(content):
    title = match.group(2).strip().lower()
    # Turn each space into its own hyphen, as GitHub does, so removed
    # punctuation leaves "--": "Tracks & Workflow" -> "tracks--workflow".
    slug = re.sub(r"[^a-z0-9 -]", "", title)
    slug = slug.replace(" ", "-")
    slugs.add(slug)
  return slugs


def test_heading_slug_keeps_one_hyphen_per_space() -> None:
  """Verifies removed punctuation leaves a double hyphen, as on GitHub."""
  assert extract_headers(
      "## Contribution Tracks & Workflow\n## Design Principles\n"
  ) == {"contribution-tracks--workflow", "design-principles"}


def test_relative_markdown_links_resolve_on_disk(
    repo_root: pathlib.Path,
) -> None:
  """Verifies that all local relative links resolve to existing files."""
  # Filter on the path inside the repo, not the absolute path: a checkout under
  # a dot-directory (~/.cache, ~/.local, ...) must not skip every file.
  markdown_files = [
      p
      for p in repo_root.rglob("*.md")
      if not any(
          part.startswith(".") or part in IGNORED_DIRS
          for part in p.relative_to(repo_root).parts
      )
  ]

  for md_file in markdown_files:
    content = md_file.read_text(encoding="utf-8", errors="ignore")

    # Strip code blocks and inline backtick spans to avoid matching examples
    clean_content = re.sub(r"```[\s\S]*?```", "", content)
    clean_content = re.sub(r"`[^`]*`", "", clean_content)
    headers = extract_headers(clean_content)

    for match in LINK_PATTERN.finditer(clean_content):
      target = match.group(2).strip()

      # Ignore external URLs, schemes, and shortlinks
      if any(target.startswith(scheme) for scheme in IGNORED_SCHEMES):
        continue

      # Ignore template variable placeholders (e.g. {id}, <path>)
      if (
          target.endswith(("_url", "_path", "_link"))
          or "{" in target
          or "<" in target
      ):
        continue

      # Intra-document anchor link
      if target.startswith("#"):
        anchor = target[1:].lower()
        # Verify anchor exists in current document
        rel_path = md_file.relative_to(repo_root)
        assert anchor in headers or not headers, (
            f"Broken intra-document anchor '{target}' in {rel_path}"
        )
        continue

      # Strip fragment if target references another file with anchor
      file_target = target.split("#")[0]
      if not file_target:
        continue

      resolved_path = (md_file.parent / file_target).resolve()
      if not resolved_path.exists() and (repo_root / file_target).exists():
        resolved_path = (repo_root / file_target).resolve()

      rel_path = md_file.relative_to(repo_root)
      assert resolved_path.exists(), (
          f"Broken relative link '[{match.group(1)}]({target})' in {rel_path}: "
          f"resolved path '{resolved_path}' does not exist on disk."
      )
