# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Check the separate web chat package, which the shared skill tests skip."""

import json
from pathlib import Path
import re
import runpy
from xml.etree import ElementTree
import zipfile

import yaml

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "chatgpt-web"
SKILL = WEB / "skills/egm-in-chat"
PACKER = runpy.run_path(str(ROOT / "scripts/pack_plugin.py"))


def test_skill_stays_out_of_shared_skills() -> None:
  # Every coding harness and both desktop bundles read skills/.
  assert not (ROOT / "skills/egm-in-chat").exists()
  assert "egm-in-chat" not in PACKER["SKILLS"]


def test_skill_instructions() -> None:
  _, header, body = (SKILL / "SKILL.md").read_text(encoding="utf-8").split("---", 2)
  frontmatter = yaml.safe_load(header)
  assert frontmatter["name"] == SKILL.name
  assert frontmatter["description"].strip()
  # The web host must be able to choose the skill by itself.
  assert "disable-model-invocation" not in frontmatter
  assert len(body.strip().encode("utf-8")) <= 24_000
  assert "Same-context review, not independent." in body
  assert "full EGM" in body


def test_skill_scenarios() -> None:
  data = yaml.safe_load((SKILL / "test_scenarios.yaml").read_text(encoding="utf-8"))
  assert data["skill"] == SKILL.name
  assert data["scenarios"]
  for scenario in data["scenarios"]:
    assert scenario["scenario_id"] and scenario["eval_type"]
    assert (ROOT / scenario["system_prompt"]["skill_file"]).is_file()
    for turn in scenario["turns"]:
      for assertion in turn["assertions"]:
        re.compile(assertion["pattern"])


def test_skill_interface_and_icon() -> None:
  interface = yaml.safe_load(
      (SKILL / "agents/openai.yaml").read_text(encoding="utf-8"))["interface"]
  assert interface["display_name"] == "EGM for ChatGPT"
  assert 25 <= len(interface["short_description"]) <= 64
  assert f"${SKILL.name}" in interface["default_prompt"]
  assert interface["brand_color"].lower() == "#1b6ef3"
  for field in ("icon_small", "icon_large"):
    svg = ElementTree.parse(SKILL / interface[field]).getroot()
    assert svg.get("viewBox") == "0 0 24 24"
    assert svg.findtext("{http://www.w3.org/2000/svg}title")
    colors = {
        value.lower() for element in svg.iter()
        for key, value in element.attrib.items()
        if key in ("fill", "stroke") and value != "none"
    }
    assert colors == {"#1b6ef3", "#7cacf8"}


def test_manifest_needs_no_local_executor() -> None:
  text = (WEB / "plugin.json").read_text(encoding="utf-8")
  assert "requires_local_executor" not in text
  manifest = json.loads(text)
  assert manifest["name"] == SKILL.name
  assert re.fullmatch(r"\d+\.\d+\.\d+", manifest["version"])
  interface = manifest["extensions"]["com.openai"]["interface"]
  for field, limit in (
      ("displayName", 30), ("shortDescription", 30),
      ("longDescription", 4000), ("developerName", 80),
  ):
    assert 0 < len(interface[field]) <= limit, field


def test_web_bundle_is_complete_and_reproducible(tmp_path: Path) -> None:
  folder, archive = PACKER["build_web"](ROOT, tmp_path / "first")
  _, repeated = PACKER["build_web"](ROOT, tmp_path / "second")
  assert archive.read_bytes() == repeated.read_bytes()
  with zipfile.ZipFile(archive) as bundle:
    assert bundle.testzip() is None
    assert set(bundle.namelist()) == {
        "LICENSE", "plugin.json",
        "skills/egm-in-chat/SKILL.md",
        "skills/egm-in-chat/agents/openai.yaml",
        "skills/egm-in-chat/assets/icon.svg",
    }
    for info in bundle.infolist():
      assert info.date_time == (1980, 1, 1, 0, 0, 0)
      assert bundle.read(info) == (folder / info.filename).read_bytes()
