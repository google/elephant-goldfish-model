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

"""Unit tests for Style Goldfish calibration and Phase 5 boundary handoffs."""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_style_goldfish_defines_defensive_prose_calibration_actions() -> None:
  """Verifies Style Goldfish audits defensive caveats using DROP/CALIBRATE/RELOCATE/KEEP."""
  style_text = (ROOT / "agents" / "style.md").read_text(encoding="utf-8")
  for action in ("DROP", "CALIBRATE", "RELOCATE", "KEEP"):
    assert f"`{action}`" in style_text, (
        f"Missing editorial calibration action {action} in agents/style.md"
    )
  assert "Defensive Caveats & Uncalibrated Claims" in style_text


def test_implementation_readiness_standard_defines_file_boundary_handoff() -> None:
  """Verifies Implementation Readiness standard defines a Phase 5 file boundary."""
  standard_text = (
      ROOT
      / "resources"
      / "document_standards"
      / "implementation-readiness-standard.md"
  ).read_text(encoding="utf-8")
  assert "Target Scope & File Boundary" in standard_text
  assert "repository-relative" in standard_text
  assert "Phase 5 write allowlist" in standard_text
