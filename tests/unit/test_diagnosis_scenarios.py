# SPDX-License-Identifier: Apache-2.0
"""Regression cases for diagnosis evaluation patterns raised in PR review."""

from pathlib import Path
import re

import pytest
import yaml


@pytest.mark.parametrize("scenario,reply,accepted", [
    ("missing_reproduction", "Can you share reproduction steps or a failure trace?", True),
    ("missing_reproduction", "What steps lead to the wrong result?", True),
    ("missing_reproduction", "I'll write reproduction steps and dispatch the Goldfish.", False),
    ("intermittent_failure", "No. One pass does not falsify the race hypothesis", True),
    ("intermittent_failure", "A single pass can't disprove a failure seen 2 times in 20 attempts.", True),
    ("intermittent_failure", "Yes, one passing attempt falsifies it.", False),
])
def test_scenario_pattern_rejects_the_wrong_answer(scenario, reply, accepted):
    root = Path(__file__).resolve().parents[2]
    data = yaml.safe_load((root / "skills/egm-diagnose/test_scenarios.yaml").read_text())
    case = next(s for s in data["scenarios"] if s["scenario_id"] == scenario)
    assertion = case["turns"][0]["assertions"][0]
    assert assertion["type"] == "required_pattern"
    assert bool(re.search(assertion["pattern"], reply)) is accepted
