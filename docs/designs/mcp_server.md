# Read-only EGM MCP server

**Status:** Proposed (Stage 1 design for #553)
**Owner:** @aaravkhanal
**Date:** 2026-11-28

## Problem

An MCP host cannot discover EGM reviewer personas or standards without a user
copying files by hand. A local, read-only server can expose those existing
materials and check that a findings payload has the shape expected by the
review workflow. It must not turn the local repository into a general-purpose
filesystem or command interface.

## Goals

- Start as a local subprocess using MCP stdio transport and the protocol's
  initialize/tools lifecycle.
- Expose exactly four tools: `list_personas`, `get_persona`, `get_standard`,
  and `validate_findings`.
- Read only explicitly allowed Markdown files below the repository root.
- Keep the project-supported Python 3.10 baseline.
- Keep all review execution, model calls, and changes to repository files out of
  scope.
- Document setup, host configuration, and the security boundary.

## Non-goals

- Write or edit tools, shell execution, model calls, subagent dispatch, network
  clients, telemetry, or arbitrary file access.
- HTTP transport, authentication, multi-user operation, or host adapters.
- Release, marketplace, or plugin packaging.
- Replacing the EGM skills or their review/resolution process.

## Proposed design

### Process and protocol

Add a small server entry point at `scripts/egm_mcp_server.py`. Launch it as a
stdio subprocess from the repository root after installing its optional
dependency group. Use the official MCP Python SDK `mcp==1.30.0`, the latest v1.x
maintenance release at design time. It supports Python 3.10 and the requested
initialize handshake. The current SDK 2.x line raises the Python minimum to
3.11; adopting it would break the documented runtime baseline. Keep this
dependency isolated in an `mcp` dependency group; do not add it to the
default/test groups or any release package. Upgrade the exact pin only through
dependency review and protocol/client compatibility tests.

The SDK owns JSON-RPC framing, initialization, capability negotiation,
`tools/list`, `tools/call`, and graceful shutdown. The server declares only the
tools capability, with no prompts, resources, or tool-list-change notifications.
The stdio contract requires each stdout line to be a valid MCP message; logs
and diagnostics go to stderr. No custom JSON-RPC implementation is added.

### Tool contracts

`tools/list` returns exactly the four tools below. All schemas are JSON Schema
objects with `additionalProperties: false`; missing, extra, or wrong-typed tool
arguments produce a normal MCP invalid-params/tool error without a traceback or
file-system detail.

| Tool | Input | Result |
| --- | --- | --- |
| `list_personas` | `{}` | Sorted list of agent identifiers (filename stems) and their repository-relative paths. It reads no file contents. |
| `get_persona` | `{"name": "<identifier>"}` | UTF-8 text of one allowed `agents/<identifier>.md` file. |
| `get_standard` | `{"name": "<identifier>"}` | UTF-8 text of one allowed `resources/document_standards/<identifier>.md` file. |
| `validate_findings` | `{"findings": [...]}` | `{ "valid": boolean, "errors": [...] }`; it validates structure only and performs no filesystem access. |

The findings input is an array of at most 200 objects. Each object requires
non-empty string fields `id`, `reviewer`, `severity`, `affected_scope`,
`discrepancy_description`, and `rationale`. `severity` is one of `Blocker`,
`Major`, or `Nit`, matching `egm-resolve`. Other fields are rejected. Strings
are capped at 8,000 characters and arrays at 200 items to bound parsing and
response size. Validation reports each invalid array index, field, and concise
reason; it does not echo submitted text. An empty array is valid. This tool
checks shape only, not whether findings are true, safe, or supported by the
target document.

Unknown identifiers, malformed argument objects, traversal strings, absolute
paths, and paths with separators are rejected before any read. The tool
identifier is a name, never a caller-provided path.

### File boundary

Derive the repository root from the resolved entry-point path, never from the
process working directory or a client-supplied value. Construct the persona and
standard registries from direct-child `.md` files in `agents/` and
`resources/document_standards/`, respectively. Do not recurse or expose other
directories. Resolve each candidate strictly and reject it unless its resolved
path remains beneath both the repository root and its designated directory;
this prevents symlinks from escaping the allowlist. Read as UTF-8 and fail
closed for missing files, invalid encoding, or containment failures. Return
only the requested file's text.

These files contain instructions intended for agents. Their text is untrusted
input from the MCP client's perspective: the server returns it as data and
does not execute, interpret, or follow it. A client decides how to present and
use tool output.

### Security posture and limits

The process has the permissions of the user who starts it; “read-only” describes
the server's tool behavior, not an operating-system sandbox. The server itself
performs no writes, subprocess launches, network requests, or telemetry. A
compromised dependency or host still runs with the invoking user's permissions.
The narrow tool registry and resolved-path checks reduce accidental exposure,
but do not protect against a compromised local checkout or a malicious MCP
client. Users should connect only a trusted local checkout and should review
tool names and results in their MCP host.

## Alternatives considered

1. **Official MCP SDK 1.x (proposed).** Reuses a maintained implementation of
   the protocol and stdio lifecycle while retaining Python 3.10. Pinning the
   dependency adds install surface, but avoids maintaining protocol framing and
   edge cases in this repository.
2. **Hand-written stdlib JSON-RPC loop.** Avoids an external runtime dependency,
   but requires EGM to implement and maintain MCP framing, initialization,
   capability negotiation, errors, and future protocol details. This is a
   larger correctness and maintenance burden for a protocol integration.
3. **Official SDK 2.x.** Provides the current SDK line, but requires Python 3.11+
   and follows a newer protocol lifecycle than this issue's requested
   initialize handshake. It would force a runtime change or a split runtime
   contract.
4. **Expose files as MCP resources instead of tools.** Resources suit static
   file retrieval, but the issue explicitly requests four callable tools,
   including a deterministic findings validator. Keep this iteration's public
   surface limited to those four tools; resource exposure can be considered
   separately if clients need subscription or URI-based browsing.

## Implementation plan and acceptance checks

1. Add an isolated exact-pinned `mcp` dependency group and the stdio entry point;
   keep Python 3.10 compatibility and run it only from a source checkout.
2. Implement an explicit tool registry and strict argument schemas. Use
   canonical identifier validation and resolved-path containment before reads.
3. Implement structural findings validation with bounded input and deterministic
   errors, following the contract above.
4. Add focused unit tests for each tool, malformed and extra arguments, unknown
   names, traversal/absolute/separator inputs, symlink escape, missing/invalid
   UTF-8 files, findings required fields/severity/limits, and proof that
   validation performs no file reads.
5. Add stdio end-to-end tests using an MCP client: initialize, list tools, call
   each tool, exercise an invalid call, verify clean shutdown, and assert stdout
   contains protocol messages only. Add a short usage/security document.
6. Run the unit suite and lint on Python 3.10 and the newest CI Python version;
   verify the pinned dependency installation and an MCP Inspector connection
   against the exact source checkout.

Implementation scope is limited to `pyproject.toml`, `scripts/egm_mcp_server.py`,
`tests/unit/test_mcp_server.py`, `docs/mcp_server.md`, and the relevant testing
documentation. If a lockfile or a separate dependency group test is required by
maintainer guidance, update only the lockfile and corresponding focused tests.

## Open questions for design review

- Is a source-checkout-only server with a separately installed, exact-pinned
  SDK dependency the right first delivery, given that release packaging is an
  explicit non-goal?
- Should the allowlist enumerate every agent file dynamically as proposed, or
  should maintainers curate a fixed set of externally exposed personas?
- Do maintainers want the findings shape above to be canonical, or should the
  validator accept the exact report object emitted by another existing workflow?
- Which MCP client/version should be used for the compatibility smoke test?

## References

- Issue [#553](https://github.com/google/elephant-goldfish-model/issues/553).
- [MCP stdio transport](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)
  and [tool protocol](https://modelcontextprotocol.io/specification/2025-11-25/server/tools).
- [Official MCP Python SDK 1.30.0](https://github.com/modelcontextprotocol/python-sdk/tree/v1.30.0)
  (Python 3.10 support and legacy initialize lifecycle).
- [EGM findings and resolution contract](../../skills/egm-resolve/SKILL.md).
