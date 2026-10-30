# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Install an experimental OpenCode V1 bundle without changing user config."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]
HOST_VERSION = "1.18.29"
REVIEWERS = (
    "codebase_details", "comprehension", "design_critic",
    "implementation_readiness", "structural", "style", "zoom_out",
)


def name(path: Path) -> str:
    """Read the canonical name without a runtime YAML dependency."""
    header = path.read_text(encoding="utf-8").split("---", 2)[1]
    match = re.search(r"^name: (egm-[a-z-]+)$", header, re.MULTILINE)
    if not match:
        raise ValueError(f"Missing canonical name: {path}")
    return match[1]


def install(destination: Path) -> Path:
    """Create a new installation; refuse to overwrite any existing path."""
    destination = destination.expanduser().absolute()
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    destination = destination.resolve()
    # Check resolved parents too: paths enter glob rules and prompt templates.
    if "\\" in destination.as_posix() or any(
        c in str(destination) for c in '*?[]{}!@`$\n\r'
    ):
        raise ValueError("Installation path contains template or glob characters")
    # Read rules match worktree-relative paths and "*" spans "/", so "*.env.*"
    # would deny every bundle read below such a path.
    if ".env." in str(destination).lower():
        raise ValueError("Installation path matches the .env read rules")
    if destination.is_relative_to(ROOT):
        raise ValueError("Install outside the source tree")
    destination.mkdir(parents=True)
    bundle = destination / "bundle"
    bundle.mkdir()
    for directory in ("skills", "agents", "resources", "docs"):
        shutil.copytree(ROOT / directory, bundle / directory)
    for filename in ("plugin.json", "LICENSE", "README.md", "TESTING.md"):
        shutil.copy2(ROOT / filename, bundle / filename)

    guide = bundle / "docs/opencode.md"
    context = (
        f"Read {guide} first. EGM bundle root: {bundle}. "
        "Resolve agents/, resources/, and docs/ against this root. "
        "Resolve references/ against the canonical skill directory. "
        "Resolve user files and outputs against the project working directory. "
    )
    agents = {}
    for reviewer in REVIEWERS:
        persona = bundle / "agents" / f"{reviewer}.md"
        agents[name(persona)] = {
            "description": f"EGM read-only {reviewer} reviewer (experimental)",
            "mode": "subagent",
            "color": "#E86E00",
            "permission": {
                "*": "deny",
                # Later rules win, so "*" alone would override OpenCode's default .env rules.
                "read": {
                    "*": "allow", "*.env": "deny", "*.env.*": "deny",
                    "*.env.example": "allow", "mcp:*": "deny",
                },
                "glob": "allow", "grep": "allow",
                "external_directory": {"*": "deny", f"{bundle}/**": "allow"},
            },
            "prompt": context + f"Read {persona} before the target and supplied standards. "
            "Return findings to the caller. Do not write reports or delegate. "
            "Read prior reports only when explicitly supplied and required by the canonical stage. "
            "Do not retrieve unsolicited history, memory, or earlier reviewer findings. "
            "Report inaccessible required files as an incomplete review.",
        }
    agents["egm"] = {
        "description": "EGM orchestrator (experimental OpenCode V1)",
        "mode": "primary",
        "color": "#1B6EF3",
        "permission": {
            "*": "ask",
            "read": {"*": "allow", "*.env": "ask", "*.env.*": "ask", "*.env.example": "allow"},
            "glob": "allow", "grep": "allow",
            "skill": {"*": "deny", "egm-*": "allow"},
            "task": {"*": "deny", **{key: "allow" for key in agents}},
            "external_directory": {"*": "ask", f"{bundle}/**": "allow"},
        },
        "prompt": context + "Follow the canonical skill. Dispatch reviewers directly "
        "with task and the registered persona name as subagent_type. "
        "Omit task_id for every independent review; never resume a reviewer. "
        "Wait for foreground completion. Pass only the task, absolute resource paths, "
        "target, standards, and selected reading list, not conversation history. "
        "Stop if delegation or a required completion is missing. "
        "When running brainstorm before draft, complete all six brainstorm "
        "reviewers and synthesize their findings into concepts_brief.md before drafting. "
        "In review, write each completed stage report before starting the next stage. "
        "Before Step 8, verify zoom_out_report.md exists in the artifact directory "
        "and pass its absolute path to the reviewer; stop if it is missing. "
        "Write reports yourself. Preserve every human approval gate.",
    }
    skills = destination / "skills"
    skills.mkdir()
    commands = {}
    for skill in sorted((bundle / "skills").glob("*/SKILL.md")):
        skill_name = name(skill)
        (skills / skill_name).symlink_to(skill.parent, target_is_directory=True)
        commands[skill_name] = {
            "description": f"Run {skill_name} (experimental)",
            "agent": "egm",
            "template": context + f"Read and execute {skill}.\nUser request: $ARGUMENTS",
        }
    config = destination / "opencode.json"
    config.write_text(json.dumps({
        "$schema": "https://opencode.ai/config.json",
        "autoupdate": False,
        "default_agent": "egm",
        "skills": {"paths": [str(skills)]},
        "agent": agents,
        "command": commands,
    }, indent=2) + "\n", encoding="utf-8")
    metadata = json.loads((bundle / "plugin.json").read_text(encoding="utf-8"))
    (destination / "installation.json").write_text(json.dumps({
        "name": metadata["name"], "version": metadata["version"],
        "host_version": HOST_VERSION, "status": "experimental",
        "sha256": {
            path.relative_to(destination).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(bundle.rglob("*")) if path.is_file()
        },
    }, indent=2) + "\n", encoding="utf-8")
    return config


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="New, fixed installation directory")
    print(install(parser.parse_args().destination))
