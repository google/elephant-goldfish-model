# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Report whether an EGM install is complete. Reads files only; changes nothing."""

import argparse
import json
from pathlib import Path
import re
import runpy
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REQUIRED = runpy.run_path(str(HERE / "pack_plugin.py"))["REQUIRED_SHARED"]
HOSTS = {"claude": "Claude Code", "codex": "Codex CLI", "agy": "Antigravity CLI"}
WHOLE_PLUGIN = ("Install the whole plugin: skills read agents/ and "
                "resources/ at run time, so copying skills/ alone breaks EGM.")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def finding(check: str, status: str, detail: str, fix: str = "") -> dict:
  return {"check": check, "status": status, "detail": detail, "fix": fix}


def check_manifest(root: Path) -> tuple[str, list[dict]]:
  """Read the portable manifest and report the plugin version."""
  path = root / "plugin.json"
  if not path.is_file():
    return "unknown", [finding("manifest", "FAIL", "Missing plugin.json",
                               WHOLE_PLUGIN)]
  try:
    manifest = json.loads(path.read_text(encoding="utf-8"))
  except (OSError, ValueError) as error:
    return "unknown", [finding("manifest", "FAIL", f"Unreadable plugin.json: {error}",
                               "Reinstall from the repository or a release ZIP.")]
  version = str(manifest.get("version", "unknown"))
  return version, [finding("manifest", "PASS", f"plugin.json is valid, version {version}")]


def check_resources(root: Path) -> list[dict]:
  """Name each required file that is missing, with one remedy."""
  results = []
  for name in REQUIRED:
    path = root / name
    if not path.is_file():
      results.append(finding("resource", "FAIL", f"Missing {name}", WHOLE_PLUGIN))
    elif any((root / Path(*Path(name).parts[:i])).is_symlink()
             for i in range(1, len(Path(name).parts) + 1)):
      results.append(finding("resource", "WARN", f"Symlinked path {name}",
                             "Hosts may not follow symlinks; install a plain copy."))
  if not results:
    results.append(finding("resource", "PASS",
                           f"All {len(REQUIRED)} required files are present"))
  return results


def check_skills(root: Path) -> list[dict]:
  """Confirm every skill has frontmatter with a name and description."""
  results = []
  for skill in sorted(root.glob("skills/*/SKILL.md")):
    match = FRONTMATTER.match(skill.read_text(encoding="utf-8", errors="replace"))
    keys = set(re.findall(r"^([A-Za-z-]+):", match.group(1), re.MULTILINE)) if match else set()
    if not {"name", "description"} <= keys:
      results.append(finding("skill", "FAIL",
                             f"{skill.relative_to(root)} lacks name or description frontmatter",
                             "Reinstall; the file is truncated or edited."))
  if not results:
    results.append(finding("skill", "PASS", "Skill frontmatter is present"))
  return results


def check_hosts(execute: bool) -> list[dict]:
  """Detect host CLIs on PATH. Anything undetectable stays UNKNOWN."""
  results = []
  for command, label in HOSTS.items():
    path = shutil.which(command)
    if not path:
      results.append(finding("host", "UNKNOWN", f"{label}: `{command}` not on PATH"))
    elif not execute:
      results.append(finding("host", "UNKNOWN", f"{label}: found, version not queried"))
    else:
      try:
        run = subprocess.run([path, "--version"], capture_output=True, text=True,
                             timeout=5, check=False)
        version = (run.stdout or run.stderr).strip().splitlines()[0]
        results.append(finding("host", "PASS", f"{label}: {version}"))
      except (OSError, IndexError, subprocess.TimeoutExpired):
        results.append(finding("host", "UNKNOWN", f"{label}: version not readable"))
  results.append(finding(
      "isolation", "UNKNOWN",
      "Fresh-context reviewers cannot be proven by static checks",
      "Run the live probe described in TESTING.md."))
  return results


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--root", type=Path, default=HERE.parent,
                      help="installed plugin directory (default: this checkout)")
  parser.add_argument("--json", action="store_true", help="print JSON")
  parser.add_argument("--no-exec", action="store_true",
                      help="do not run host CLIs to read their versions")
  args = parser.parse_args(argv)
  root = args.root.resolve()
  version, results = check_manifest(root)
  results += check_resources(root) + check_skills(root) + check_hosts(not args.no_exec)
  failed = any(item["status"] == "FAIL" for item in results)
  if args.json:
    print(json.dumps({"root": str(root), "version": version, "ok": not failed,
                      "findings": results}, indent=2))
  else:
    print(f"EGM {version} at {root}")
    shown = set()
    for item in results:
      print(f"[{item['status']}] {item['check']}: {item['detail']}")
      if item["fix"] and item["fix"] not in shown:
        shown.add(item["fix"])
        print(f"       fix: {item['fix']}")
  return 1 if failed else 0


if __name__ == "__main__":
  sys.exit(main())
