# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Exercise the workflow's required-result gate without running hosted jobs."""

import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]


def workflow() -> dict:
  return yaml.safe_load((ROOT / ".github/workflows/tests.yml").read_text())


def test_ci_waits_for_all_validation_jobs() -> None:
  jobs = workflow()["jobs"]
  assert set(jobs["ci"]["needs"]) == set(jobs) - {"ci"}
  assert jobs["ci"]["name"] == "CI"
  assert jobs["ci"]["if"] == "${{ always() }}"
  assert jobs["unit"]["strategy"]["fail-fast"] is False
  assert set(jobs["unit"]["strategy"]["matrix"]["os"]) == {
      "ubuntu-24.04", "windows-2025",
  }


def test_release_installs_hashed_wheels_before_tag_checkout() -> None:
  release = yaml.safe_load(
      (ROOT / ".github/workflows/release.yml").read_text())
  release_steps = release["jobs"]["build"]["steps"]
  install = ("python -m pip install --require-hashes --only-binary=:all: "
             "-r .github/requirements-release.txt")
  unit_steps = workflow()["jobs"]["unit"]["steps"]
  assert "python -m pip install --group test" in [step.get("run") for step in unit_steps]
  install_index = next(i for i, step in enumerate(release_steps)
                       if step.get("run") == install)
  tag_index = next(i for i, step in enumerate(release_steps)
                   if step.get("id") == "source")
  assert install_index < tag_index, "Older tags may not define the test group"


def test_release_signing_cannot_execute_build_dependencies() -> None:
  release = yaml.safe_load(
      (ROOT / ".github/workflows/release.yml").read_text())
  jobs = release["jobs"]
  assert release["permissions"] == {}
  assert jobs["build"]["permissions"] == {"contents": "read"}
  assert jobs["draft"]["permissions"] == {"actions": "read", "contents": "write"}
  signer = jobs["attest"]
  assert signer["needs"] == "build"
  assert {"build", "attest"} <= set(jobs["draft"]["needs"])
  assert signer["permissions"] == {
      "contents": "read", "id-token": "write", "attestations": "write",
  }
  allowed_actions = {"actions/download-artifact", "actions/attest"}
  for step in signer["steps"]:
    if "uses" in step:
      action, revision = step["uses"].split("@")
      assert action in allowed_actions
      assert len(revision) == 40 and all(c in "0123456789abcdef" for c in revision)
    else:
      # Do not execute downloaded scripts or install code in the signing job.
      assert step["run"] == "cd release && sha256sum -c SHA256SUMS"
  upload = next(s for s in jobs["build"]["steps"]
                if s.get("uses", "").startswith("actions/upload-artifact@"))
  for consumer in (signer, jobs["draft"]):
    download = next(s for s in consumer["steps"]
                    if s.get("uses", "").startswith("actions/download-artifact@"))
    assert download["with"]["name"] == upload["with"]["name"]
    assert "run-id" not in download["with"]


def test_release_lock_pins_direct_and_transitive_dependencies() -> None:
  import re

  lock = (ROOT / ".github/requirements-release.txt").read_text()
  requirements = [line for line in lock.splitlines()
                  if line and not line.startswith("#")]
  pattern = r"([\w-]+)==([\d.]+) --hash=sha256:[0-9a-f]{64}"
  assert all(re.fullmatch(pattern, line) for line in requirements)
  pinned = dict(re.match(pattern, line).groups() for line in requirements)
  assert set(pinned) == {"pytest", "PyYAML", "iniconfig", "packaging", "pluggy"}
  project = (ROOT / "pyproject.toml").read_text()
  for name in ("pytest", "PyYAML"):
    assert f'"{name.lower()}=={pinned[name]}"' in project.lower()


@pytest.mark.parametrize("results,success", [
    ({"unit": "success"}, True),
    ({"unit": "failure"}, False),
    ({"unit": "cancelled"}, False),
    ({"unit": "skipped"}, False),
    ({"unit": "success", "site-validation": "success"}, True),
    ({"unit": "success", "site-validation": "failure"}, False),
    ({"unit": "success", "site-validation": "cancelled"}, False),
    ({"unit": "success", "site-validation": "skipped"}, False),
])
def test_ci_requires_successful_results(results: dict, success: bool) -> None:
  step = workflow()["jobs"]["ci"]["steps"][0]
  assert step["env"]["NEEDS_JSON"] == "${{ toJSON(needs) }}"
  shell = shutil.which("bash")
  assert shell, "POSIX bash is required for workflow shell checks"
  completed = subprocess.run(
      [shell, "-e", "-c", step["run"]],
      env={**os.environ, "NEEDS_JSON": json.dumps({
          name: {"result": result} for name, result in results.items()
      })},
      text=True, capture_output=True, timeout=10,
  )
  assert (completed.returncode == 0) is success, (
      completed.stdout + completed.stderr
  )
