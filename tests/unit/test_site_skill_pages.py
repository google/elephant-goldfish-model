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

"""Unit tests that keep the website skill pages in step with each SKILL.md.

The website renders one hand-written reader page per skill from
docs/site/skills/. The instructions live in skills/<name>/SKILL.md, and a
skill change can leave its page behind. These tests check the stable,
structural facts that must not drift: page coverage, the skill link,
frontmatter name, the example command, and output artifact names. They do
not compare prose, so wording can change in one place without editing the
other.
"""

import pathlib
import re

import pytest
import yaml

PAGES_DIR = pathlib.Path("docs/site/skills")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
FENCE_RE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
ARTIFACT_RE = re.compile(r"`([^`\n]+)`")


def _repo_root() -> pathlib.Path:
  return pathlib.Path(__file__).resolve().parents[2]


def _skill_names() -> tuple[str, ...]:
  skills = _repo_root() / "skills"
  return tuple(sorted(path.name for path in skills.iterdir() if path.is_dir()))


def _page(name: str) -> str:
  return (_repo_root() / PAGES_DIR / f"{name}.md").read_text(encoding="utf-8")


def _skill_text(name: str) -> str:
  return (_repo_root() / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


def _frontmatter(name: str) -> dict:
  match = FRONTMATTER_RE.match(_skill_text(name))
  assert match, f"skills/{name}/SKILL.md has no frontmatter"
  data = yaml.safe_load(match.group(1))
  assert isinstance(data, dict), f"skills/{name}/SKILL.md has no frontmatter map"
  return data


def _prose(name: str) -> str:
  """Return page text without frontmatter and fenced example blocks."""
  return FENCE_RE.sub("", FRONTMATTER_RE.sub("", _page(name), count=1))


def _example_fence(name: str, command: str) -> str | None:
  for fence in FENCE_RE.findall(_page(name)):
    if command in fence:
      return fence
  return None


def _artifact_names(text: str) -> set[str]:
  names = set()
  for token in ARTIFACT_RE.findall(text):
    token = token.strip("\"'")
    if token.endswith(".md"):
      names.add(pathlib.PurePosixPath(token).name)
  return names


def test_every_skill_has_exactly_one_page() -> None:
  pages = {path.stem for path in (_repo_root() / PAGES_DIR).glob("*.md")}
  skills = set(_skill_names())
  missing = sorted(skills - pages)
  extra = sorted(pages - skills)
  assert not missing, f"{PAGES_DIR}/ is missing pages for: {missing}"
  assert not extra, f"{PAGES_DIR}/ has pages without a skill: {extra}"


@pytest.mark.parametrize("name", _skill_names())
def test_page_matches_the_skill_name(name: str) -> None:
  assert _frontmatter(name)["name"] == name, (
      f"skills/{name}/SKILL.md frontmatter name must match its directory"
  )


@pytest.mark.parametrize("name", _skill_names())
def test_page_links_to_its_own_skill(name: str) -> None:
  assert f"skills/{name}/SKILL.md" in _page(name), (
      f"{PAGES_DIR}/{name}.md must link to skills/{name}/SKILL.md"
  )


@pytest.mark.parametrize("name", _skill_names())
def test_page_example_invokes_the_skill(name: str) -> None:
  command = f"/{name}"
  fence = _example_fence(name, command)
  assert fence is not None, (
      f"{PAGES_DIR}/{name}.md shows no example invoking {command}"
  )


@pytest.mark.parametrize("name", _skill_names())
def test_page_prose_names_documented_artifacts(name: str) -> None:
  documented = _artifact_names(_skill_text(name))
  mentioned = _artifact_names(_prose(name))
  assert mentioned, f"{PAGES_DIR}/{name}.md names no output artifact"
  assert mentioned <= documented, (
      f"{PAGES_DIR}/{name}.md names artifacts that"
      f" skills/{name}/SKILL.md does not document:"
      f" {sorted(mentioned - documented)}"
  )
