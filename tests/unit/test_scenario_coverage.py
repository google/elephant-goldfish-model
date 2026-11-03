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

"""Unit tests verifying behavioral scenario coverage across all skills."""

import pathlib
from typing import List
import yaml


def test_all_skills_have_co_located_test_scenarios(
    discovered_skills: List[pathlib.Path],
) -> None:
  """Verifies every discovered skill package contains test_scenarios.yaml."""
  for skill_path in discovered_skills:
    scenarios_file = skill_path / "test_scenarios.yaml"
    assert scenarios_file.exists(), (
        f"Missing required co-located test_scenarios.yaml in {skill_path}"
    )

    data = yaml.safe_load(scenarios_file.read_text(encoding="utf-8"))
    assert isinstance(data, dict), (
        f"{scenarios_file} must parse as a dictionary"
    )
    assert data.get("skill") == skill_path.name, (
        f"'skill' in {scenarios_file} ({data.get('skill')}) must match "
        f"directory name {skill_path.name}"
    )

    scenarios = data.get("scenarios", [])
    assert scenarios, f"{scenarios_file} must define at least one scenario"
    for sc in scenarios:
      assert "scenario_id" in sc, (
          f"Scenario in {scenarios_file} missing 'scenario_id'"
      )
      assert "eval_type" in sc, (
          f"Scenario in {scenarios_file} missing 'eval_type'"
      )
      assert "turns" in sc and sc["turns"], (
          f"Scenario in {scenarios_file} missing non-empty 'turns'"
      )
