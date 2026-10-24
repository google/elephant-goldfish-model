# EGM Testing Playbook

This document provides a step-by-step developer playbook for running unit tests across the EGM skill suite.

---

## Setup

### A. Python Environment Setup
Create and activate an isolated Python 3.10+ virtual environment:

```bash
# Navigate to the repository root
cd /path/to/egm_opensource

# Create virtual environment
python3 -m venv .venv

# Activate environment
source .venv/bin/activate

# Install testing dependencies
pip install -r requirements-dev.txt
```

---

## Unit Tests

Unit tests run offline without network access, API keys, or model
dependencies. They validate YAML frontmatter schemas and relative link
integrity, the portable plugin manifest, shared metadata consistency, and
marketplace/component paths.

```bash
# Run all unit tests
pytest tests/unit

# Run with verbose output
pytest tests/unit -v

# Run a specific unit test module
pytest tests/unit/test_frontmatter.py -v
pytest tests/unit/test_link_integrity.py -v
```
---

## Native Claude Reviewer Probe (Opt-in)

With an authenticated Claude Code 2.1.271+ installation, run:

```bash
EGM_CLAUDE_LIVE=1 pytest tests/integration/test_claude.py
```

This uses the account's model quota. It loads a copy of the plugin, invokes
the review skill, and checks that a native reviewer reads only its persona and
sees no parent or project `CLAUDE.md` context. See [Claude integration](docs/claude.md).
---

## Native Codex Integration Tests (Opt-in)

Opt-in integration tests run the live candidate through a temporary Codex marketplace:

```sh
EGM_CODEX_LIVE=1 pytest tests/integration/test_codex.py -v
```

Tests verify candidate installation, fresh-context reviewer isolation, and workflow artifacts.
Each test runs with an authenticated Codex CLI in an isolated sandbox.
See [Codex integration](docs/codex.md).

---

## Harness Test Record

A harness counts as supported after `/egm-brainstorm`, `/egm-draft`, and
`/egm-review` run end to end through its plugin install (see
[Harnesses](docs/harnesses.md)). Add a row for each run.

| Harness | Version | Date | Install | Brainstorm | Draft | Review | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Antigravity CLI | 1.4.5 | 2026-10-22 | Pass; validator warnings | Pass (fixture) | Pass (fixture) | Pass (fixture) | Temporary HOME with no hooks, MCP servers, or other plugins. The isolation probe passed on the native child transcript. 16 native reviewers ran. Stages 5 to 9 ran in sequence by timestamp. All required reads occurred. Five stage reports exist. No code was written. The final design differs from the draft in one `Status` line. Not tested: interactive approvals, `egm-bootstrap`, and synthesizer nesting. The bootstrap skill is larger than the load limit. |
| Claude Code | 2.1.308 | 2026-10-22 | Pass (`--plugin-dir`) | Pass (fixture) | Pass (fixture) | Pass after fix (fixture) | Isolation probe passed. Initial stage-order failure retained; focused nine-reviewer rerun verifies sequential stages and required reads. Process shutdown and parent no-shell fixture limits remain in the full report. |
| Claude Cowork | Opus 5.5 Medium, connected cloud task | 2026-10-22 | Pass (ZIP) | Completed with direct-dispatch recovery | Completed | Partial: stages 5–7 | Usage limit interrupted stage 8. Final artifacts, stage 9 and actual isolation-child output remain unverified; #105. Earlier complete run is reported separately. |
| OpenAI Codex | 0.163.0 | 2026-10-22 | Pass | Pass (fixture) | Pass (fixture) | Pass (fixture) | Two live tests passed in 573.13s; isolation, 15 native reviewers, ordered stages and required reads verified. |
| ChatGPT Work | GPT-6.1 Sol, Light | 2026-10-22 | Pass; installed hashes verified | Completed | Completed | Nine native reviewers completed | Fresh probe returned UNKNOWN. Artifact download/final audit and full child tool traces remain outstanding; #106. |

### Interpreting native test results

Keep full run reports in the [PR description](https://github.com/google/elephant-goldfish-model/pull/103).
This table is a summary. Record the tested commit, client version, commands,
native evidence, and limitations in each report. Parse JSONL on literal LF;
Python `splitlines()` also splits valid Unicode characters inside JSON strings.

Track open cloud verification gaps in [#105 (Cowork)](https://github.com/google/elephant-goldfish-model/issues/105) and [#106 (ChatGPT Work)](https://github.com/google/elephant-goldfish-model/issues/106).

- Inspect native tool traces for reviewer launches, completion, and intended resource reads.
- Verify sequential stage execution and persona lenses in addition to artifact existence.
- Distinguish fixture design findings from execution failures of the review workflow.
- Keep installation, execution, and transcript isolation results recorded separately.
