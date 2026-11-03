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
from typing import Any, Callable, List

try:
  import pytest
  fixture = pytest.fixture
except ImportError:
  def fixture(*args: Any, **unused_kwargs: Any) -> Any:
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
      return fn
    if len(args) == 1 and callable(args[0]):
      return args[0]
    return decorator


@fixture(scope="session")
def repo_root() -> pathlib.Path:
  """Resolves the repository root directory across repository layouts."""
  current = pathlib.Path(__file__).resolve().parent
  for candidate in [current] + list(current.parents):
    if (candidate / "plugins" / "egm").exists():
      return candidate / "plugins" / "egm"
    if (candidate / "skills").exists() and (candidate / "agents").exists():
      return candidate
  return current.parent


@fixture(scope="session")
def skills_dir(repo_root: pathlib.Path) -> pathlib.Path:
  """Locates the skills directory dynamically."""
  direct_path = repo_root / "skills"
  if direct_path.exists():
    return direct_path

  oss_path = repo_root / "plugins" / "egm" / "skills"
  if oss_path.exists():
    return oss_path

  raise FileNotFoundError(f"Skills directory not found relative to {repo_root}")


@fixture(scope="session")
def discovered_skills(skills_dir: pathlib.Path) -> List[pathlib.Path]:
  """Returns all skill directory paths under the skills root."""
  skills = [
      p for p in skills_dir.iterdir()
      if p.is_dir() and not p.name.startswith((".", "_"))
  ]
  assert skills, f"No skills discovered in {skills_dir}"
  return sorted(skills)
