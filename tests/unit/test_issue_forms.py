# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Validate the GitHub issue forms and the docs that link to them."""

from pathlib import Path
import re

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = ROOT / ".github/ISSUE_TEMPLATE"
FORMS = {
    "bug_report.yml": "Bug",
    "feature_proposal.yml": "Feature",
    "task.yml": "Task",
}
DOCS_LINKING_TEMPLATES = ("CONTRIBUTING.md", "AI_POLICY.md", "ACCESSIBILITY.md")


def form(name: str) -> dict:
  return yaml.safe_load((TEMPLATE_DIR / name).read_text(encoding="utf-8"))


def fields(name: str) -> list:
  return [item for item in form(name)["body"] if item["type"] != "markdown"]


def test_only_yaml_forms_and_chooser_config_exist() -> None:
  assert {p.name for p in TEMPLATE_DIR.iterdir()} == set(FORMS) | {"config.yml"}
  assert yaml.safe_load((TEMPLATE_DIR / "config.yml").read_text())[
      "blank_issues_enabled"] is False


@pytest.mark.parametrize("name,issue_type", FORMS.items())
def test_forms_keep_native_type_and_required_core_fields(
    name: str, issue_type: str) -> None:
  data = form(name)
  assert data["name"] and data["description"]
  assert data["type"] == issue_type
  for item in fields(name):
    assert item["type"] == "textarea"
    assert item["id"] and item["attributes"]["label"]
    assert isinstance(item["validations"]["required"], bool)
  assert all(item["validations"]["required"] for item in fields(name)[:3])


def test_bug_evidence_is_optional_and_sanitized() -> None:
  evidence = fields("bug_report.yml")[-1]
  assert evidence["id"] == "evidence"
  assert evidence["validations"]["required"] is False
  assert "Remove secrets" in evidence["attributes"]["description"]


def test_feature_inquiry_keeps_design_gates() -> None:
  notice = form("feature_proposal.yml")["body"][0]
  assert notice["type"] == "markdown"
  for gate in ("design-ready", "pr-ready", "Refs #<issue>", "Closes #<issue>"):
    assert gate in notice["attributes"]["value"]


@pytest.mark.parametrize("doc", DOCS_LINKING_TEMPLATES)
def test_docs_link_to_existing_forms(doc: str) -> None:
  text = (ROOT / doc).read_text(encoding="utf-8")
  referenced = set(re.findall(r"template=([\w.]+)", text))
  referenced |= set(re.findall(r"ISSUE_TEMPLATE/([\w.]+)", text))
  assert referenced, f"{doc} should link to an issue form"
  assert referenced <= set(FORMS), referenced
