# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for EGM input preflight inventory, verification, and early halting."""

import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
  sys.path.insert(0, str(ROOT))

from tests.input_preflight import (
    InputType,
    classify_input,
    run_preflight,
    verify_input_item,
)


def test_classify_input_types() -> None:
  """Verifies classification into text, image, and attachment."""
  assert classify_input("doc.md") == InputType.TEXT
  assert classify_input("notes.txt") == InputType.TEXT
  assert classify_input("script.py") == InputType.TEXT
  assert classify_input("diagram.png") == InputType.IMAGE
  assert classify_input("mockup.jpg") == InputType.IMAGE
  assert classify_input("architecture.svg") == InputType.IMAGE
  assert classify_input("bundle.tar.gz") == InputType.ATTACHMENT
  assert classify_input("data.bin") == InputType.ATTACHMENT
  assert classify_input("report.pdf") == InputType.ATTACHMENT


def test_preflight_text_only_input(tmp_path: Path) -> None:
  """Automated test: verifies text-only input passes with correct inventory counts."""
  file1 = tmp_path / "design.md"
  file1.write_text("# Design Document\nDetails here.", encoding="utf-8")
  file2 = tmp_path / "context.txt"
  file2.write_text("Context information.", encoding="utf-8")

  result = run_preflight([file1, file2])

  assert result.passed is True
  assert result.error is None
  assert result.counts == {"text": 2, "image": 0, "attachment": 0}
  assert len(result.items) == 2
  assert all(item.readable for item in result.items)
  assert result.items[0].identity == str(file1)
  assert result.items[0].input_type == InputType.TEXT
  assert result.items[1].identity == str(file2)
  assert result.items[1].input_type == InputType.TEXT


def test_preflight_mixed_text_and_images(tmp_path: Path) -> None:
  """Automated test: verifies mixed text and images pass with correct counts."""
  doc = tmp_path / "spec.md"
  doc.write_text("# Spec\nDiagram attached.", encoding="utf-8")
  diagram = tmp_path / "flowchart.png"
  diagram.write_bytes(b"\x89PNG\r\n\x1a\nfake_image_bytes")
  icon = tmp_path / "icon.svg"
  icon.write_text("<svg></svg>", encoding="utf-8")

  result = run_preflight([doc, diagram, icon])

  assert result.passed is True
  assert result.error is None
  assert result.counts == {"text": 1, "image": 2, "attachment": 0}
  assert len(result.items) == 3
  assert all(item.readable for item in result.items)


def test_preflight_missing_image_stops_with_actionable_error(tmp_path: Path) -> None:
  """Automated test: verifies a missing image halts run with an actionable error."""
  doc = tmp_path / "spec.md"
  doc.write_text("# Spec with missing screenshot", encoding="utf-8")
  missing_image = tmp_path / "nonexistent_screenshot.png"

  result = run_preflight([doc, missing_image])

  assert result.passed is False
  assert result.error is not None
  assert "Required image input" in result.error
  assert str(missing_image) in result.error
  assert "absent (file not found)" in result.error
  assert result.counts["image"] == 1
  assert result.counts["text"] == 1


def test_preflight_unreadable_attachment_stops_with_actionable_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
  """Automated test: verifies an unreadable attachment halts with an actionable error."""
  doc = tmp_path / "spec.md"
  doc.write_text("# Spec with unreadable attachment", encoding="utf-8")
  unreadable_file = tmp_path / "secure_payload.bin"
  unreadable_file.write_bytes(b"sensitive payload bytes")

  real_access = os.access

  def deny_attachment(path: os.PathLike[str], mode: int) -> bool:
    if Path(path) == unreadable_file:
      return False
    return real_access(path, mode)

  monkeypatch.setattr(os, "access", deny_attachment)

  result = run_preflight([doc, unreadable_file])

  assert result.passed is False
  assert result.error is not None
  assert "Required attachment input" in result.error
  assert str(unreadable_file) in result.error
  assert "unreadable" in result.error


def test_preflight_records_result(tmp_path: Path) -> None:
  """Verifies the preflight record formatting captures counts, types, and items."""
  doc = tmp_path / "overview.md"
  doc.write_text("# Overview", encoding="utf-8")
  chart = tmp_path / "chart.png"
  chart.write_bytes(b"\x89PNG")

  result = run_preflight([doc, chart])
  record = result.format_record()

  assert "Preflight Input Verification: PASSED" in record
  assert "1 text, 1 image, 0 other attachment(s)" in record
  assert f"`{doc}` (text): readable (text)" in record
  assert f"`{chart}` (image): readable (image)" in record


def test_skills_and_resources_define_input_preflight_contracts() -> None:
  """Verifies that skills and execution instructions specify the input preflight contract."""
  instructions = (ROOT / "resources" / "execution_instructions.md").read_text(
      encoding="utf-8"
  )
  assert "## Input Preflight & Verification" in instructions
  assert "Inventory" in instructions
  assert "Readability Verification" in instructions
  assert "Early Halt on Missing or Unreadable Inputs" in instructions

  review_loop = (ROOT / "skills" / "egm-review-loop" / "SKILL.md").read_text(
      encoding="utf-8"
  )
  assert "Input Preflight Verification" in review_loop
  assert "text" in review_loop and "image" in review_loop and "attachment" in review_loop
  assert "actionable error" in review_loop
