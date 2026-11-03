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

"""Unit tests for SKILL.md YAML frontmatter validation."""

import pathlib
from typing import Any, Dict, List
import yaml


def extract_frontmatter(file_path: pathlib.Path) -> Dict[str, Any]:
  """Extracts and parses YAML frontmatter from a Markdown file."""
  content = file_path.read_text(encoding="utf-8")
  lines = content.splitlines()

  # Look for opening and closing frontmatter delimiters
  if not lines or lines[0].strip() != "---":
    # Check if there are leading license comments or shebang before frontmatter
    start_idx = -1
    for idx, line in enumerate(lines[:15]):
      if line.strip() == "---":
        start_idx = idx
        break
    if start_idx == -1:
      raise ValueError(
          f"No leading frontmatter delimiter ('---') found in {file_path}"
      )
    lines = lines[start_idx:]

  end_idx = -1
  for idx, line in enumerate(lines[1:], start=1):
    if line.strip() == "---":
      end_idx = idx
      break

  if end_idx == -1:
    raise ValueError(
        f"No closing frontmatter delimiter ('---') found in {file_path}"
    )

  yaml_text = "\n".join(lines[1:end_idx])
  data = yaml.safe_load(yaml_text)
  if not isinstance(data, dict):
    raise ValueError(
        f"Frontmatter in {file_path} did not parse into a dictionary"
    )
  return data


def test_all_skills_have_valid_frontmatter(
    discovered_skills: List[pathlib.Path],
) -> None:
  """Verifies that every skill contains a valid SKILL.md with schema keys."""
  for skill_path in discovered_skills:
    skill_file = skill_path / "SKILL.md"
    assert skill_file.exists(), f"SKILL.md missing in {skill_path}"

    frontmatter = extract_frontmatter(skill_file)
    assert "name" in frontmatter, (
        f"'name' key missing from frontmatter in {skill_file}"
    )
    assert "description" in frontmatter, (
        f"'description' key missing from frontmatter in {skill_file}"
    )
    assert (
        isinstance(frontmatter["name"], str) and frontmatter["name"].strip()
    ), f"'name' must be a non-empty string in {skill_file}"
    assert (
        isinstance(frontmatter["description"], str)
        and frontmatter["description"].strip()
    ), f"'description' must be a non-empty string in {skill_file}"

    # Validate optional schema attributes if present
    if "disable-model-invocation" in frontmatter:
      assert isinstance(frontmatter["disable-model-invocation"], bool), (
          f"'disable-model-invocation' must be a boolean in {skill_file}"
      )
