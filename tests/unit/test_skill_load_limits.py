# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Keep complete skill instructions within Antigravity's body load limit."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("skill", sorted((ROOT / "skills").glob("*/SKILL.md")),
                         ids=lambda skill: skill.parent.name)
def test_skill_body_fits_antigravity(skill: Path) -> None:
  body = skill.read_text(encoding="utf-8").split("---", 2)[2].strip()
  size = len(body.encode("utf-8"))
  assert size <= 24_000, (
      f"{skill.parent.name}: {size} bytes exceeds Antigravity's 24,000-byte "
      "skill body limit; move details into an explicitly read reference"
  )
