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
skill change can leave its page behind. These tests fail when a page and
its SKILL.md disagree, so both are updated in the same change.

Checked facts (#391): every skill has exactly one page, each page links to
its own skill, each page example invokes the documented slash command and
shows an argument where the skill requires one, each page names the skill's
primary output artifact while SKILL.md still names it, every artifact
filename a page mentions in prose appears in SKILL.md, and SKILL.md still
documents the inputs listed for it.

OUTPUTS, INPUTS, and REQUIRED_EXAMPLE_ARG below state the facts a page must
carry today. When a skill changes one of those facts, update the matching
table and docs/site/skills/<name>.md in the same change.
"""

import pathlib
import re

import pytest
import yaml

PAGES_DIR = pathlib.Path("docs/site/skills")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
FENCE_RE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
ARTIFACT_RE = re.compile(r"`([^`\n]+\.md)`")

# Primary output artifact each page must name. The name must also appear in
# the skill's SKILL.md, so a rename there fails the test and forces an
# update to both the page and this table.
OUTPUTS = {
    "egm-bootstrap": ("README.md",),
    "egm-brainstorm": ("concepts_brief.md",),
    "egm-draft": ("design_draft.md",),
    "egm-drift-report": ("{YYYY-MM-DD}_DRIFT_REPORT.md",),
    "egm-resolve": ("goldfish_review_report.md",),
    "egm-review": ("consolidated_review_report.md",),
    "egm-review-loop": ("goldfish_review_report.md",),
}

# Documented input parameters each SKILL.md must still list. Renaming or
# removing one fails the test and forces an update to this table.
INPUTS = {
    "egm-bootstrap": ("path", "target_filename"),
    "egm-draft": ("Context File",),
    "egm-resolve": ("TargetFile", "FindingsList"),
    "egm-review": ("TargetFile",),
    "egm-review-loop": ("TargetFile", "Reviewers", "Standards", "GoldfishContext"),
}

# Skills whose documented input is a path or document argument. Their page
# example must show an argument after the command.
REQUIRED_EXAMPLE_ARG = {
    "egm-bootstrap", "egm-drift-report", "egm-review", "egm-review-loop",
}


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
  if name in REQUIRED_EXAMPLE_ARG:
    remainder = fence.replace(command, "", 1).strip()
    assert remainder, (
        f"{PAGES_DIR}/{name}.md must show an argument after {command} because"
        f" skills/{name}/SKILL.md requires one"
    )


@pytest.mark.parametrize("name", _skill_names())
def test_page_names_a_current_output_artifact(name: str) -> None:
  anchors = OUTPUTS.get(name)
  assert anchors, (
      f"OUTPUTS in tests/unit/test_site_skill_pages.py lists no artifact for"
      f" {name}"
  )
  for anchor in anchors:
    assert anchor in _page(name), (
        f"{PAGES_DIR}/{name}.md does not name the output artifact {anchor}."
        " Update the page or the OUTPUTS table in"
        " tests/unit/test_site_skill_pages.py"
    )
    assert anchor in _skill_text(name), (
        f"skills/{name}/SKILL.md no longer names {anchor}. If the artifact"
        f" was renamed, update {PAGES_DIR}/{name}.md and the OUTPUTS table"
        " in tests/unit/test_site_skill_pages.py"
    )


@pytest.mark.parametrize("name", _skill_names())
def test_page_prose_names_only_documented_artifacts(name: str) -> None:
  skill = _skill_text(name)
  for token in ARTIFACT_RE.findall(_prose(name)):
    assert token in skill, (
        f"{PAGES_DIR}/{name}.md mentions {token}, which"
        f" skills/{name}/SKILL.md does not document. Rename or remove it,"
        " or restore the artifact name in the skill"
    )


@pytest.mark.parametrize("name", _skill_names())
def test_skill_still_documents_listed_inputs(name: str) -> None:
  for parameter in INPUTS.get(name, ()):
    assert f"`{parameter}`" in _skill_text(name), (
        f"skills/{name}/SKILL.md no longer documents `{parameter}`. Update"
        " the INPUTS table in tests/unit/test_site_skill_pages.py, and the"
        f" page {PAGES_DIR}/{name}.md if it names the input"
    )
