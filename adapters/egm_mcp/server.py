# Copyright 2026 Google LLC.
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

"""Minimal, read-only MCP (Model Context Protocol) stdio server for EGM."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "egm", "version": "0.1.1"}

NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
STANDARD_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

PERSONAS_DIR = ROOT / "agents"
STANDARDS_DIR = ROOT / "resources" / "document_standards"


def persona_names() -> list:
    names = []
    for path in sorted(PERSONAS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        header = text.split("---", 2)[1]
        match = re.search(r"^name: (egm-[a-z0-9-]+)$", header, re.MULTILINE)
        if not match:
            continue
        names.append({"name": path.stem, "path": "agents/" + path.name})
    return names


def get_persona(name: str) -> str:
    if not NAME_PATTERN.match(name):
        raise ValueError("Invalid persona name")
    path = PERSONAS_DIR / (name + ".md")
    if not path.is_file():
        raise FileNotFoundError(name)
    return path.read_text(encoding="utf-8")


def get_standard(name: str) -> str:
    if not STANDARD_PATTERN.match(name):
        raise ValueError("Invalid standard name")
    path = STANDARDS_DIR / (name + "-standard.md")
    if not path.is_file():
        raise FileNotFoundError(name)
    return path.read_text(encoding="utf-8")


def validate_findings(findings_json: str) -> dict:
    try:
        findings = json.loads(findings_json)
    except json.JSONDecodeError as error:
        return {"valid": False, "reasons": ["not valid JSON: " + str(error)]}
    reasons = []
    if not isinstance(findings, dict):
        return {"valid": False, "reasons": ["findings must be a JSON object"]}
    if not isinstance(findings.get("findings"), list):
        reasons.append("missing findings array")
    if "conversations" in findings and not isinstance(findings.get("conversations"), dict):
        reasons.append("conversations must be an object")
    return {"valid": not reasons, "reasons": reasons}


def tool_definitions() -> list:
    return [
        {
            "name": "list_personas",
            "description": "List the read-only EGM goldfish personas available for review.",
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "get_persona",
            "description": "Return the canonical EGM persona prompt for a goldfish reviewer.",
            "inputSchema": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        },
        {
            "name": "get_standard",
            "description": "Return a bundled EGM document standard for reviewers.",
            "inputSchema": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        },
        {
            "name": "validate_findings",
            "description": "Validate a structured reviewer findings payload against the EGM worker contract shape.",
            "inputSchema": {
                "type": "object",
                "properties": {"findings_json": {"type": "string"}},
                "required": ["findings_json"],
            },
        },
    ]


def handle_tool(name: str, arguments: dict) -> dict:
    if name == "list_personas":
        return {"content": [{"type": "text", "text": json.dumps(persona_names())}]}
    if name == "get_persona":
        persona = get_persona(str(arguments.get("name", "")))
        return {"content": [{"type": "text", "text": persona}]}
    if name == "get_standard":
        standard = get_standard(str(arguments.get("name", "")))
        return {"content": [{"type": "text", "text": standard}]}
    if name == "validate_findings":
        findings_json = str(arguments.get("findings_json", "{}"))
        return {"content": [{"type": "text", "text": json.dumps(validate_findings(findings_json))}]}
    return {"content": [{"type": "text", "text": "Unknown tool: " + name}], "isError": True}


def dispatch(request: dict):
    method = request.get("method")
    request_id = request.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": request_id, "result": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        }}
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": tool_definitions()}}
    if method == "tools/call":
        params = request.get("params") or {}
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if not isinstance(arguments, dict):
            return {"jsonrpc": "2.0", "id": request_id, "error": {
                "code": -32602, "message": "Invalid params: arguments must be an object"}}
        outcome = handle_tool(str(name), arguments)
        return {"jsonrpc": "2.0", "id": request_id, "result": outcome}
    if request_id is None:
        return None
    return {"jsonrpc": "2.0", "id": request_id, "error": {
        "code": -32601, "message": "Method not found: " + str(method)}}


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = dispatch(message)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
