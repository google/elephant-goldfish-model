# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Preflight inventory and readability verification for EGM inputs."""

from dataclasses import dataclass
from enum import Enum
import os
from pathlib import Path
from typing import Optional, Union

IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp", ".tiff"
}
TEXT_EXTENSIONS = {
    ".md", ".txt", ".json", ".yaml", ".yml", ".py", ".js", ".ts", ".html",
    ".htm", ".css", ".sh", ".c", ".h", ".cpp", ".cc", ".rs", ".go", ".java",
    ".xml", ".toml", ".rst", ".adoc",
}


class InputType(str, Enum):
  TEXT = "text"
  IMAGE = "image"
  ATTACHMENT = "attachment"


def classify_input(path_or_name: Union[str, Path]) -> InputType:
  """Classify an input path or filename into text, image, or attachment."""
  ext = Path(path_or_name).suffix.lower()
  if ext in IMAGE_EXTENSIONS:
    return InputType.IMAGE
  if ext in TEXT_EXTENSIONS:
    return InputType.TEXT
  return InputType.ATTACHMENT


@dataclass
class InputItem:
  identity: str
  input_type: InputType
  readable: bool
  error_message: Optional[str] = None


@dataclass
class PreflightResult:
  passed: bool
  counts: dict[str, int]
  items: list[InputItem]
  error: Optional[str] = None

  def format_record(self) -> str:
    """Format the preflight result as a markdown record block."""
    status_str = "PASSED" if self.passed else "FAILED"
    lines = [
        f"### Preflight Input Verification: {status_str}",
        f"- **Inventory**: {self.counts['text']} text, {self.counts['image']} image, {self.counts['attachment']} other attachment(s)",
    ]
    for item in self.items:
      mark = "✓" if item.readable else "✗"
      status_detail = f"readable ({item.input_type.value})" if item.readable else f"UNREADABLE: {item.error_message}"
      lines.append(f"  * [{mark}] `{item.identity}` ({item.input_type.value}): {status_detail}")
    if self.error:
      lines.append(f"- **Error**: {self.error}")
    return "\n".join(lines)


def verify_input_item(path: Union[str, Path]) -> InputItem:
  """Verify that an input item exists and is readable."""
  p = Path(path)
  input_type = classify_input(p)
  identity = str(p)

  if not p.exists():
    return InputItem(
        identity=identity,
        input_type=input_type,
        readable=False,
        error_message=(
            f"Required {input_type.value} input '{identity}' is absent (file not found)."
        ),
    )

  if not os.access(p, os.R_OK):
    return InputItem(
        identity=identity,
        input_type=input_type,
        readable=False,
        error_message=(
            f"Required {input_type.value} input '{identity}' is unreadable (permission denied)."
        ),
    )

  if input_type == InputType.TEXT:
    try:
      with open(p, "r", encoding="utf-8", errors="strict") as f:
        f.read(1024)
    except Exception as e:
      return InputItem(
          identity=identity,
          input_type=input_type,
          readable=False,
          error_message=f"Required text input '{identity}' is unreadable ({e}).",
      )
  else:
    try:
      with open(p, "rb") as f:
        f.read(1024)
    except Exception as e:
      return InputItem(
          identity=identity,
          input_type=input_type,
          readable=False,
          error_message=f"Required {input_type.value} input '{identity}' is unreadable ({e}).",
      )

  return InputItem(identity=identity, input_type=input_type, readable=True)


def run_preflight(inputs: list[Union[str, Path]]) -> PreflightResult:
  """Run preflight inventory and verification over all required inputs."""
  items: list[InputItem] = []
  counts = {"text": 0, "image": 0, "attachment": 0}
  errors: list[str] = []

  for inp in inputs:
    item = verify_input_item(inp)
    items.append(item)
    counts[item.input_type.value] += 1
    if not item.readable and item.error_message:
      errors.append(item.error_message)

  passed = len(errors) == 0
  combined_error = "\n".join(errors) if errors else None

  return PreflightResult(
      passed=passed,
      counts=counts,
      items=items,
      error=combined_error,
  )
