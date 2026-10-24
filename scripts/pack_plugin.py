# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Build runtime folders and reproducible ZIPs without development files."""

import argparse
import json
from pathlib import Path
import zipfile

SHARED = (
    "plugin.json", "LICENSE", "README.md", "TESTING.md",
    "CONTRIBUTING.md", "AI_POLICY.md", ".github/PULL_REQUEST_TEMPLATE.md",
    "skills/*/SKILL.md", "skills/*/references/*.md",
    "skills/*/references/*.json", "agents/*.md", "resources/*.md",
    "resources/document_standards/*.md", "docs/*.md", "docs/designs/*.md",
    "assets/*.svg", "assets/*.png",
)
HOST = {
    "claude": (".claude-plugin/plugin.json", ".claude-plugin/icon.png",
               ".claude-plugin/agents/*.md"),
    "openai": (".codex-plugin/plugin.json",),
}


def build(root: Path, target: str, output: Path) -> tuple[Path, Path]:
  """Write a new runtime folder and ZIP; refuse unsafe inputs or overwrites."""
  root = root.resolve()
  folder = output.resolve() / f"egm-{target}"
  archive = folder.with_suffix(".zip")
  if folder.exists() or archive.exists():
    raise ValueError("Output folder or ZIP already exists")
  if folder == root or root.is_relative_to(folder):
    raise ValueError("Output must not contain the source tree")
  files = set()
  for pattern in SHARED + HOST[target]:
    for path in root.glob(pattern):
      relative = path.relative_to(root)
      if any((root / Path(*relative.parts[:i])).is_symlink()
             for i in range(1, len(relative.parts) + 1)):
        raise ValueError(f"Symlink in runtime path: {relative}")
      if not path.resolve().is_relative_to(root):
        raise ValueError(f"Path outside source: {relative}")
      if path.is_file() and relative.as_posix() != "docs/directory.md":
        files.add(relative)
  for name in ("plugin.json", "LICENSE", "README.md", "TESTING.md",
               HOST[target][0]):
    if Path(name) not in files:
      raise ValueError(f"Missing required file: {name}")
  manifest = json.loads((root / HOST[target][0]).read_text())
  portable = json.loads((root / "plugin.json").read_text())
  openai = portable.get("extensions", {}).get("com.openai", {})
  if manifest.get("hooks") or portable.get("hooks") or openai.get("hooks"):
    raise ValueError("Directory packages cannot contain hooks")
  for metadata in (manifest, portable, openai):
    if any(metadata.get(key) for key in ("mcpServers", "mcp", "apps")):
      raise ValueError("This runtime builder does not package MCP or app dependencies")
  references = list(manifest.get("agents", []))
  interface = openai.get("interface", {})
  if target == "openai":
    interface = interface or manifest.get("interface", {})
    references += [interface[key] for key in ("composerIcon", "logo")]
  else:
    references.append(manifest.get("icon", "./.claude-plugin/icon.png"))
  for reference in references:
    path = Path(reference)
    if path.is_absolute() or ".." in path.parts or path not in files:
      raise ValueError(f"Unbundled manifest reference: {reference}")
  output.mkdir(parents=True, exist_ok=True)
  folder.mkdir()
  with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
    for relative in sorted(files):
      data = (root / relative).read_bytes()
      destination = folder / relative
      destination.parent.mkdir(parents=True, exist_ok=True)
      destination.write_bytes(data)
      destination.chmod(0o644)
      info = zipfile.ZipInfo(relative.as_posix(), (1980, 1, 1, 0, 0, 0))
      info.create_system = 3
      info.external_attr = 0o100644 << 16
      info.compress_type = zipfile.ZIP_DEFLATED
      bundle.writestr(info, data)
  return folder, archive


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--target", required=True, choices=HOST)
  parser.add_argument("--output", required=True, type=Path)
  args = parser.parse_args()
  runtime, bundle = build(Path(__file__).resolve().parents[1],
                          args.target, args.output)
  print(f"Runtime: {runtime}\nZIP: {bundle}")
