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

"""Unit tests for starter task curation guidance and outcome tracking."""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
CONTRIBUTING_PATH = ROOT / "CONTRIBUTING.md"
OUTCOMES_PATH = ROOT / "docs" / "verification" / "starter-task-outcomes.md"


def test_contributing_documents_starter_task_standards_and_outcome_log() -> None:
    """Verifies CONTRIBUTING.md links the outcome log and states starter task rules."""
    text = CONTRIBUTING_PATH.read_text(encoding="utf-8")
    assert "docs/verification/starter-task-outcomes.md" in text
    assert "two business days" in text
    assert "clear scope" in text
    assert "observable" in text
    assert "acceptance criteria" in text
    assert "validation command" in text


def test_starter_task_outcomes_has_required_tracking_fields() -> None:
    """Verifies the starter task outcome log defines all required #332 fields."""
    assert OUTCOMES_PATH.is_file()
    text = OUTCOMES_PATH.read_text(encoding="utf-8")
    for required_field in (
        "Review period",
        "Starter queue",
        "Time to first response",
        "Tasks completed",
        "Data gaps",
        "Adjustments",
    ):
        assert required_field in text, f"Missing '{required_field}' in {OUTCOMES_PATH}"

    assert "two business days" in text
    for issue_num in ("#332", "#502", "#503", "#504", "#506"):
        assert issue_num in text, f"Missing {issue_num} in {OUTCOMES_PATH}"
