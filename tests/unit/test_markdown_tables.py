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

"""Unit tests that keep Markdown tables renderable on GitHub."""

import pathlib
import re

# Vendored trees whose markdown is not ours to validate.
IGNORED_DIRS = ("node_modules",)

FENCE_PATTERN = re.compile(r"```[\s\S]*?```")
# A g3doc multi-line table continues a row on lines framed by ':'.
CONTINUATION_PATTERN = re.compile(r"^:.*:\s*$")


def test_tables_have_no_multiline_continuation_rows(
    repo_root: pathlib.Path,
) -> None:
  """Verifies that no table uses g3doc ':' continuation rows.

  GitHub Flavored Markdown has no continuation rows: it shows each ':' line
  as a separate, broken row (issue #193).
  """
  markdown_files = [
      p
      for p in repo_root.rglob("*.md")
      if not any(
          part.startswith(".") or part in IGNORED_DIRS
          for part in p.relative_to(repo_root).parts
      )
  ]

  failures = []
  for md_file in markdown_files:
    content = md_file.read_text(encoding="utf-8", errors="ignore")
    # Blank out fenced blocks but keep their newlines so line numbers hold.
    content = FENCE_PATTERN.sub(lambda m: "\n" * m.group(0).count("\n"), content)
    previous = ""
    for number, line in enumerate(content.splitlines(), start=1):
      if CONTINUATION_PATTERN.match(line) and previous.startswith(("|", ":")):
        failures.append(f"{md_file.relative_to(repo_root)}:{number}")
      previous = line

  assert not failures, (
      "Multi-line table rows do not render on GitHub. Put each row on one"
      " line:\n" + "\n".join(failures)
  )
