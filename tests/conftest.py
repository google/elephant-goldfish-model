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

"""Shared pytest configuration and root discovery fixtures."""

import pathlib
from typing import List

import pytest


@pytest.fixture(scope="session")
def repo_root() -> pathlib.Path:
  """Return the root of this repository."""
  return pathlib.Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def discovered_skills(repo_root: pathlib.Path) -> List[pathlib.Path]:
  """Returns all skill directory paths under the skills root."""
  skills_dir = repo_root / "skills"
  skills = [
      p for p in skills_dir.iterdir()
      if p.is_dir() and not p.name.startswith((".", "_"))
  ]
  assert skills, f"No skills discovered in {skills_dir}"
  return sorted(skills)
