"""Unit tests for the read-only EGM MCP stdio server tools."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_persona_names_include_security() -> None:
    sys.path.insert(0, str(ROOT / "adapters" / "egm_mcp"))
    import importlib
    module = importlib.import_module("server")
    names = [entry["name"] for entry in module.persona_names()]
    assert "design_critic" in names
    assert "security" in names


def test_get_persona_rejects_traversal() -> None:
    sys.path.insert(0, str(ROOT / "adapters" / "egm_mcp"))
    import importlib
    module = importlib.import_module("server")
    with pytest.raises(ValueError):
        module.get_persona("../../etc/passwd")


def test_get_standard_rejects_unknown() -> None:
    sys.path.insert(0, str(ROOT / "adapters" / "egm_mcp"))
    import importlib
    module = importlib.import_module("server")
    with pytest.raises(FileNotFoundError):
        module.get_standard("definitely-not-a-standard")


def test_validate_findings_accepts_valid() -> None:
    sys.path.insert(0, str(ROOT / "adapters" / "egm_mcp"))
    import importlib
    module = importlib.import_module("server")
    result = module.validate_findings(json.dumps({"findings": [{"severity": "Major"}]}))
    assert result["valid"] is True
    result = module.validate_findings("{not json")
    assert result["valid"] is False


def test_dispatch_tools_list_and_call_unknown() -> None:
    sys.path.insert(0, str(ROOT / "adapters" / "egm_mcp"))
    import importlib
    module = importlib.import_module("server")
    response = module.dispatch({
        "jsonrpc": "2.0", "id": 7, "method": "tools/list", "params": {}})
    assert response["id"] == 7
    assert "tools" in response["result"]
    unknown = module.dispatch({
        "jsonrpc": "2.0", "id": 8, "method": "tools/call",
        "params": {"name": "no_such_tool", "arguments": {}}})
    assert unknown["result"]["isError"] is True


def test_server_stdio_end_to_end() -> None:
    messages = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    ]
    script = (
        "import json,sys\n"
        "sys.path.insert(0, " + repr(str(ROOT / "adapters" / "egm_mcp")) + ")\n"
        "import server\n"
        "for line in sys.stdin:\n"
        "    line=line.strip()\n"
        "    if not line: continue\n"
        "    msg=json.loads(line)\n"
        "    resp=server.dispatch(msg)\n"
        "    if resp is not None:\n"
        "        sys.stdout.write(json.dumps(resp)+chr(10)); sys.stdout.flush()\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", script],
        input="\n".join(json.dumps(m) for m in messages) + "\n",
        capture_output=True, text=True, timeout=60, check=True,
    )
    lines = [json.loads(l) for l in proc.stdout.splitlines() if l.strip()]
    assert lines[0]["result"]["serverInfo"]["name"] == "egm"
    assert len(lines[1]["result"]["tools"]) == 4
