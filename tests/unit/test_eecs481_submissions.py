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

import pytest

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
    assert isinstance(data, dict), f"Expected an object in {filepath.name}"
    assert required.issubset(data.keys()), f"Missing fields in {filepath.name}"
    assert isinstance(data["contributor_id"], str) and data["contributor_id"].strip()
    assert isinstance(data["target_project"], str) and data["target_project"].strip()
    assert isinstance(data["baseline_commit"], str)
    assert type(data["baseline_test_count"]) is int and data["baseline_test_count"] >= 1
    assert type(data["final_test_count"]) is int and data["final_test_count"] >= data["baseline_test_count"]
    for field in ("baseline_coverage_percent", "final_coverage_percent"):
      assert type(data[field]) in (int, float) and 0 <= data[field] <= 100
    assert data["final_coverage_percent"] >= data["baseline_coverage_percent"]
    assert isinstance(data["test_cases"], list) and len(data["test_cases"]) >= 1
    for case in data["test_cases"]:
      assert isinstance(case, dict)
      assert {"test_name", "test_code", "targets_defect"}.issubset(case.keys())
      assert isinstance(case["test_name"], str) and case["test_name"].strip()
      assert isinstance(case["test_code"], str) and case["test_code"].strip()
      assert isinstance(case["targets_defect"], bool)
      if "defect_description" in case:
        assert isinstance(case["defect_description"], str)


def test_hw3_submissions_conform() -> None:
  schema = _load_json(SCHEMAS_DIR / "hw3_pr_assessment.json")
  required = set(schema["required"])
  submissions = sorted(
      (EECS481_DIR / "hw3-pr-assessment" / "submissions").glob("*.json")
  )
  assert submissions, "Expected at least one HW3 sample submission"
  for filepath in submissions:
    data = _load_json(filepath)
    assert isinstance(data, dict), f"Expected an object in {filepath.name}"
    assert required.issubset(data.keys()), f"Missing fields in {filepath.name}"
    assert isinstance(data["contributor_id"], str) and data["contributor_id"].strip()
    assert isinstance(data["repository"], str) and data["repository"].strip()
    assert type(data["pr_number"]) is int and data["pr_number"] >= 1
    assert isinstance(data["ground_truth_is_bad"], bool)
    assert data["decision"] in {"ACCEPT", "REJECT", "REQUEST_CHANGES"}
    assert isinstance(data["review_summary"], str) and len(data["review_summary"].strip()) > 10
    assert isinstance(data["detected_defects"], list)
    for defect in data["detected_defects"]:
      assert isinstance(defect, dict)
      assert {"file", "line", "severity", "explanation"}.issubset(defect.keys())
      assert isinstance(defect["file"], str)
      assert isinstance(defect["explanation"], str)
      assert defect["severity"] in {"CRITICAL", "MAJOR", "MINOR"}
      assert type(defect["line"]) is int and defect["line"] >= 1


@pytest.mark.parametrize(("track", "field", "value"), [
    ("hw2-test-expansion", ("baseline_commit",), 123),
    ("hw2-test-expansion", ("baseline_test_count",), True),
    ("hw2-test-expansion", ("final_test_count",), True),
    ("hw2-test-expansion", ("baseline_coverage_percent",), "50"),
    ("hw2-test-expansion", ("baseline_coverage_percent",), False),
    ("hw2-test-expansion", ("final_coverage_percent",), "100"),
    ("hw2-test-expansion", ("final_coverage_percent",), 1000),
    ("hw2-test-expansion", ("final_coverage_percent",), True),
    ("hw2-test-expansion", ("test_cases", 0, "defect_description"), False),
    ("hw3-pr-assessment", ("pr_number",), True),
    ("hw3-pr-assessment", ("detected_defects", 0, "file"), 123),
    ("hw3-pr-assessment", ("detected_defects", 0, "explanation"), False),
    ("hw3-pr-assessment", ("detected_defects", 0, "line"), True),
])
def test_rejects_invalid_submission(
    track: str,
    field: tuple[str | int, ...],
    value: object,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
  source = next((EECS481_DIR / track / "submissions").glob("*.json"))
  data = _load_json(source)
  target = data
  for key in field[:-1]:
    target = target[key]
  target[field[-1]] = value
  submissions = tmp_path / track / "submissions"
  submissions.mkdir(parents=True)
  (submissions / "invalid.json").write_text(json.dumps(data), encoding="utf-8")
  monkeypatch.setitem(globals(), "EECS481_DIR", tmp_path)
  validate = (
      test_hw2_submissions_conform
      if track == "hw2-test-expansion" else test_hw3_submissions_conform
  )
  with pytest.raises(AssertionError):
    validate()
