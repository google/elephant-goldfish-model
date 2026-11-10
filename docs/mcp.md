# EGM MCP Server (experimental)

Elephant-Goldfish Model can also run as a Model Context Protocol (MCP) server, exposing its read-only reviewer capabilities to any MCP-capable host (for example ChatGPT, Gemini CLI, or an MCP client).

## Status

* Read-only tools only: list_personas, get_persona, get_standard, validate_findings.
* stdio transport; no network egress, no write tools, no shell access.
* No telemetry: the server reads only files under the local EGM source tree and returns text to the host.

## Running

python adapters/egm_mcp/server.py

## Security posture

The server refuses invalid names, confines reads to the EGM source tree, and returns only data. Reviewer personas themselves remain read-only and enforce the untrusted-content-as-data rule.
