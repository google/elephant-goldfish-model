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

"""Offline schema and completeness checks for EECS 481 student submissions."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EECS481_DIR = ROOT / "contributions" / "eecs481"
SCHEMAS_DIR = EECS481_DIR / "schemas"


def _load_json(path: Path) -> dict:
  return json.loads(path.read_text(encoding="utf-8"))


def test_eecs481_schemas_exist() -> None:
  hw2_schema = _load_json(SCHEMAS_DIR / "hw2_test_expansion.json")
  hw3_schema = _load_json(SCHEMAS_DIR / "hw3_pr_assessment.json")
  assert hw2_schema["title"] == "EECS481_HW2_Submission"
  assert hw3_schema["title"] == "EECS481_HW3_Submission"


def test_hw2_submissions_conform() -> None:
  schema = _load_json(SCHEMAS_DIR / "hw2_test_expansion.json")
  required = set(schema["required"])
  submissions = sorted(
      (EECS481_DIR / "hw2-test-expansion" / "submissions").glob("*.json")
  )
  assert submissions, "Expected at least one HW2 sample submission"
  for filepath in submissions:
    data = _load_json(filepath)
    assert required.issubset(data.keys()), f"Missing fields in {filepath.name}"
    assert isinstance(data["contributor_id"], str) and data["contributor_id"].strip()
    assert isinstance(data["target_project"], str) and data["target_project"].strip()
    assert isinstance(data["baseline_test_count"], int) and data["baseline_test_count"] >= 1
    assert isinstance(data["final_test_count"], int) and data["final_test_count"] >= data["baseline_test_count"]
    assert 0 <= float(data["baseline_coverage_percent"]) <= 100
    assert float(data["final_coverage_percent"]) >= float(data["baseline_coverage_percent"])
    assert isinstance(data["test_cases"], list) and len(data["test_cases"]) >= 1
    for case in data["test_cases"]:
      assert {"test_name", "test_code", "targets_defect"}.issubset(case.keys())
      assert isinstance(case["test_name"], str) and case["test_name"].strip()
      assert isinstance(case["test_code"], str) and case["test_code"].strip()
      assert isinstance(case["targets_defect"], bool)


def test_hw3_submissions_conform() -> None:
  schema = _load_json(SCHEMAS_DIR / "hw3_pr_assessment.json")
  required = set(schema["required"])
  submissions = sorted(
      (EECS481_DIR / "hw3-pr-assessment" / "submissions").glob("*.json")
  )
  assert submissions, "Expected at least one HW3 sample submission"
  for filepath in submissions:
    data = _load_json(filepath)
    assert required.issubset(data.keys()), f"Missing fields in {filepath.name}"
    assert isinstance(data["contributor_id"], str) and data["contributor_id"].strip()
    assert isinstance(data["repository"], str) and data["repository"].strip()
    assert isinstance(data["pr_number"], int) and data["pr_number"] >= 1
    assert isinstance(data["ground_truth_is_bad"], bool)
    assert data["decision"] in {"ACCEPT", "REJECT", "REQUEST_CHANGES"}
    assert isinstance(data["review_summary"], str) and len(data["review_summary"].strip()) > 10
    assert isinstance(data["detected_defects"], list)
    for defect in data["detected_defects"]:
      assert {"file", "line", "severity", "explanation"}.issubset(defect.keys())
      assert defect["severity"] in {"CRITICAL", "MAJOR", "MINOR"}
      assert isinstance(defect["line"], int) and defect["line"] >= 1
