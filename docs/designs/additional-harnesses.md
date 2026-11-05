# Additional coding-agent harness support

- **Author:** [@n3wth](https://github.com/n3wth)
- **Status:** Proposal. Maintainer scope approval and design review pending.
- **Date:** 2026-10-24
- **Tracking:** [Cursor #145](https://github.com/google/elephant-goldfish-model/issues/145), [OpenCode #146](https://github.com/google/elephant-goldfish-model/issues/146), [Copilot CLI #147](https://github.com/google/elephant-goldfish-model/issues/147)

## Problem and goals

EGM needs more than a host that can discover SKILL.md files. Reviewers must
read shared personas and standards, run in fresh contexts, and produce auditable
results. Copying skills alone can leave relative resource paths broken.

Extend the shared EGM workflow to Cursor, OpenCode, and GitHub Copilot CLI.
Use small adapters for each host and the existing workflow test cases. Verify support for each host separately. One host can remain experimental while
another passes verification.

This proposal changes no runtime behavior and establishes no support claim.
It is independent of the packaging and release stack in #135, #136, and #137.
Experimental implementations can be prepared in draft PRs stacked on this design.
Maintainer scope approval and design approval remain merge prerequisites.
Draft implementations do not establish host support or satisfy live verification.

## Scope

Goals:

- Install skills, personas, standards, and required guides as one package.
- Preserve brainstorm, draft, review, human approval gates, and file artifacts.
- Start fresh reviewers with enforceable read-only access where required.
- Record installation, workflow, and isolation outcomes separately.
- Reuse existing scenarios and integration fixtures. Follow shared-test extraction in #112 without waiting for a new framework.

Non-goals:

- A generic harness registry, transport, compatibility service, or orchestration framework.
- Forking canonical skill or persona text for each host.
- Claiming support for Copilot in VS Code, Cursor cloud agents, or other surfaces
  based on a successful CLI or local IDE run.
- Paid tests in ordinary CI, provider-policy workarounds, or marketplace publication.
- Implementing Hermes, OpenClaw, or Delta here. #116 and #119 own that work.
- Factory Droid or Pi support in this iteration.

## Existing components and ownership

The shared behavior remains in skills/, agents/, resources/, and the host guides.
See [harnesses](../harnesses.md) and [testing](../../TESTING.md).

Each host contributor maintains the adapter, installation guide, offline checks, and live test records. A maintainer approves the scope. The maintainer also decides whether the test records justify a support claim. The human user approves designs and other required workflow steps.

Adapters may define how the host finds the plugin and its resources.
They may also define delegation instructions and tool restrictions. They must read shared persona
text rather than maintaining a second copy of its review rules.

## Architecture and data flow

1. The host installs an EGM candidate at a fixed version into its native package location.
2. The orchestrator loads the shared skill and resolves resources from that package.
3. Each reviewer starts with a fresh conversation. Its task contains the persona
   location, target artifact, required standards, and necessary source paths.
4. The reviewer reads those resources and returns findings through the host's
   result mechanism. It does not receive the parent's conversation,
   rationale, memory, or unrelated reviewer findings. Pass prior reports only
   when explicitly required by the canonical stage and listed as inputs.
   Stage 8, for example, requires Stage 5's `zoom_out_report.md`.
5. The orchestrator waits for all expected completions, identifies failures,
   writes the reports, and stops at the existing human approval gates.

Use direct dispatch when nested delegation is unavailable. A missing reviewer
must not be represented as a passing review. Report the incomplete stage and ask
the user how to proceed. Defer selective retries until a host requires them.

Reviewers have read-only access. Drafting and report-writing roles retain only
the workspace access needed for their outputs. Do not globally weaken host
permissions to make installation or delegation succeed.

A fresh conversation alone does not prove reviewer isolation. Host-injected
instructions, memory, MCP access, and shared workspace files must be assessed
separately. Context isolation is not filesystem or process isolation.
Assess whether a reviewer can access unrelated reports through the shared
filesystem. An instruction to avoid them does not establish enforced isolation.
Record unknown native isolation as unverified, never as a passing result.

### Human approval gates

Preserve the gates defined in the canonical skills:

- [Brainstorm](../../skills/egm-brainstorm/SKILL.md): confirm readiness before Goldfish dispatch, then approve the brief before handoff.
- [Draft](../../skills/egm-draft/SKILL.md): confirm the intake and obtain approval to draft. Approve each section. Confirm the destination when none was supplied.
- [Review](../../skills/egm-review/SKILL.md): select the preset when none was supplied. Preserve its required stage checkpoints and pause/resume choices.
- [Resolve](../../skills/egm-resolve/SKILL.md): present proposed fixes and contested findings before applying edits approved by the user.

Use plain chat when the host has no structured question tool. Wait for the
human response wherever the selected workflow requires one. A noninteractive
fixture's advance approval does not verify an interactive pause.

## Host adapter plans

| Host | Proposed mechanism | Required evidence |
| --- | --- | --- |
| Cursor local Agent | Native plugin package and custom subagents using the host's read-only setting. Reuse shared persona files through thin adapter prompts. | Verify installed resource paths, enforcement of read-only permissions, host completion records, and what context the child receives. |
| OpenCode CLI | OpenCode 1.18.29 V1 configuration with native commands, skill aliases, and restrictive JSON agent definitions. Install the complete EGM tree before exposing entry skills. | Verify `task` dispatch, `permission` enforcement, isolated child sessions, and package-relative reads. |
| GitHub Copilot CLI | Native plugin installation and custom agent profiles with an explicit tool allowlist. Leave repository-instruction inclusion disabled for reviewers. | Verify the installed package layout, child context, shared persona reads, tool denial, and reliable result collection. |

Confirm native plugin manifests and paths against the selected host version.
Do not assume Claude-compatible syntax guarantees equivalent behavior.

The Cursor candidate targets CLI `2026.10.01-e373342` for offline discovery.
Its `.cursor-plugin/plugin.json` selects `skills/`, `.cursor-plugin/agents/`,
and `.cursor-plugin/rules/`. Each reviewer declares `readonly: true` and
`permissionMode: readonly`. The pinned CLI loader requires the latter to
register read-only permissions. Offline discovery found seven skills, seven
reviewers, and one active routing rule. Native enforcement remains unverified.

The OpenCode implementation targets version 1.18.29 and the V1 interface.
It generates a separate `opencode.json` with `agent`, `command`, and
`skills.paths` entries. Reviewers use `mode: subagent` and `permission` rules
that permit local `read`, `glob`, and `grep` operations. MCP resource reads
must be denied explicitly because V1 maps those tools to `read` permissions.
The primary agent uses
`task` with a registered `subagent_type` and omits `task_id` for fresh reviews.
The native CLI accepted this configuration and discovered the seven installed
skills offline. Runtime enforcement and context isolation remain unverified.
Do not combine this mapping with V2 `subagent` or `permissions` interfaces.

The Copilot CLI candidate targets version 1.0.82 and the root Agent Plugins 1.0
`plugin.json`. Profiles live in `com.github.copilot/agents/*.agent.md`.
Native IDs are `egm:egm` for the entry agent and `egm:<persona-name>` for reviewers.
Skills remain in `skills/*/SKILL.md`. The native session inventories found all
eight profiles and seven enabled skills without a model request. Reviewers use
`tools: [read, search]`, `include-custom-instructions: false`, and
`user-invocable: false`. Live enforcement and isolation remain unverified.

Retain the current artifact-directory contract in the host guides. Report where
files were written. Do not introduce a new default output directory here.

## Validation and release gates

### Grok Bot compatibility

Assess [Grok Bot](https://cursor.com/docs/grok-bot) separately under #145.
Its persistent memory and shared cloud computer differ from Cursor local Agent.
The [Grok Bot guide](https://cursor.com/docs/grok-bot/work) describes skills and
bot handoffs. It does not establish compatibility with the Cursor adapter.

Check package import, required resource reads, fresh reviewer context, read-only
enforcement, completion records, and human approval pauses. Check whether reviewer
memory and shared files expose prior findings. Keep support unverified until these
checks pass. A passing Cursor local Agent run cannot establish Grok Bot support.
Propose any required implementation separately after this assessment.

### Shared checks

Reuse the prompts and assertions in the existing skill suites:
[brainstorm scenarios](../../skills/egm-brainstorm/test_scenarios.yaml),
[draft scenarios](../../skills/egm-draft/test_scenarios.yaml), and
[review scenarios](../../skills/egm-review/test_scenarios.yaml).
Use the marker probe and line-count workflow fixture in
[`tests/integration/test_codex.py`](../../tests/integration/test_codex.py),
plus the project-instruction and parent-marker probe in
[`tests/integration/test_claude.py`](../../tests/integration/test_claude.py),
as behavioral references. Their native trace readers are host-specific.
Adapt evidence collection to each new host; do not reuse incompatible parsers.
The common runner and results schema remain follow-up work in
[#112](https://github.com/google/elephant-goldfish-model/issues/112).

Offline checks must cover:

- Manifest parsing and identity/version consistency with the existing package.
- All referenced persona, standard, and guide paths in the installed layout.
- Adapter tool restrictions and the absence of copies of shared behavior.
- When a native evidence parser is introduced, fixtures with missing starts,
  missing completions, malformed records, and Unicode line separators. Establish
  the schema from real host records first; reuse applicable parsers and fixtures.

Live checks run only when the user explicitly requests them. Use a clean host profile and
a candidate at a fixed version. Run brainstorm, draft, and review, including a real human
approval pause. Preserve the raw evidence privately when it contains account data.

For each run, record candidate SHA, artifact checksum or installed-file identity,
host version and surface, model identifier, and date.
Record installation, workflow, and isolation outcomes separately. Record reviewer starts and completions
from host records rather than relying only on the parent's summary.

Isolation checks must include a random marker available only in the parent
conversation. Verify the child's required reads and inspect host-injected context
where available. Failure to repeat a marker alone does not
prove isolation. Probe read-only enforcement using a disposable fixture and
confirm that the reviewer cannot modify it.

If host records are inaccessible, retain an explicit unverified isolation
result. A passing install must never upgrade an unknown workflow or isolation
result. Scope all conclusions to the tested host version, model, and surface.

Add a host to the support table only after all three categories pass.
Missing delegation must stop the review with a clear unsupported message.
No inline simulation of independent reviewers is permitted.

## Alternatives considered

| Alternative | Decision and rationale |
| --- | --- |
| Skills-only installation through a universal installer | Insufficient by itself: EGM requires personas and standards outside each skill directory. It may be used only if complete package access is proven. |
| Copy the entire runtime once per host | Reject: duplicated content drifts. Keep the source content shared and adapters small. |
| Reuse the parent's conversation for reviewers | Reject: it defeats Goldfish isolation. |
| Build a universal adapter framework first | Reject: three concrete integrations do not justify a new framework. Extract common logic only after duplication appears. |
| Add every harness listed by popular repositories | Reject: adoption elsewhere does not prove EGM's installation or isolation requirements. |
| Support only the current hosts | Lowest maintenance cost, but leaves the demand represented by #145–#147 unmet. Maintainers may choose this until validation capacity is available. |

## Risks and mitigations

- Host API drift: record exact versions in test records and update the adapter with regression checks.
- Excessive model cost: run small fixtures manually and record usage when available.
- Maintenance growth: keep each adapter independent and avoid unused capabilities.

## Rollout and rollback

Prepare each host in a separate draft implementation PR based on this design
branch. The adapters have independent package layouts and verification results.
Merge the design first, then retarget and validate each implementation against
main. Maintainer approval remains required before an implementation merges.
Each implementation references its issue. Use a closing reference only when
merging that implementation completes every acceptance criterion.

Include installation documentation and offline checks with each adapter.
Keep live installation, workflow, and isolation results explicitly unverified
until the required host runs pass. Update the support table with that evidence.
Preserve existing host behavior and tests.
A broken integration can be reverted independently. Downgrade its support statement
and retain the failure record. Do not remove unrelated user configuration.

Release work proceeds separately. Inclusion of a new adapter in
a release requires regenerated packages and validation of the exact candidate.

## Open decisions and review status

- Maintainers must approve or revise the three inquiries.
- Confirm maintainers can support the validation and ongoing host-version testing.
- Complete review of the selected OpenCode V1 mapping and the other host mappings.
- The full EGM review pipeline and live host tests have not been run for this proposal.
  This document is not implementation-ready until those decisions and review findings
  are resolved.

## Research references

Reviewed 2026-10-24. These are capability references, not EGM test evidence.

- [Cursor subagents](https://cursor.com/docs/subagents)
- [OpenCode agents](https://opencode.ai/docs/agents/)
- [OpenCode V2 agents](https://dev.opencode.ai/v2/docs/agents/)
- [Copilot CLI custom agents](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli)
- [Superpowers integrations](https://github.com/obra/superpowers)
- [Vercel Skills installation ecosystem](https://github.com/vercel-labs/skills)
- [GBrain integrations](https://github.com/garrytan/gbrain)
