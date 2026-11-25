# OpenCode V2 adapter

Status: Proposed. Author: @manish96170. Date: 2026-11-18.

Related issue: #470. This proposal is separate from the OpenCode V1 work in
#146. It does not change or replace the V1 adapter.

## Problem and scope

The current OpenCode adapter targets OpenCode CLI 1.18.29. Its generated
configuration uses V1-only `agent`, `command`, `permission`, and `task`
interfaces. OpenCode V2 uses `agents`, `commands`, ordered `permissions`, and
the `subagent` action. A V1 candidate is therefore not a safe installation
path for a current OpenCode user.

Add a separate experimental OpenCode V2 adapter. It must install the complete
EGM resource tree, create V2-native reviewer profiles, and preserve the
Goldfish boundary without claiming guarantees that the host cannot establish.

Goals:

- Keep canonical skills, reviewer personas, and standards in one shared source
  tree. The adapter must not copy or fork their behavior into V2-specific text.
- Install a complete, hash-recorded candidate at a fixed user-selected path.
- Generate an `opencode.json` that OpenCode V2 accepts without using deprecated
  V1 fields.
- Run reviewer personas as named V2 subagents with read-only tool permissions.
- Preserve direct fresh-session dispatch and the existing human approval gates.
- Add offline validation and a credential-free scripted native probe for the
  selected OpenCode V2 version.
- Record installation, workflow, and isolation evidence independently.

Non-goals:

- Replacing, changing, or removing the OpenCode V1 adapter.
- Adding a hosted service, telemetry client, MCP server, automatic approval
  hook, model credential, or new network dependency.
- Advertising OpenCode V2 as supported before all required workflow and
  isolation evidence exists.
- Proving that a new child session is a complete isolation boundary.
- Running paid live-model validation in ordinary CI.

## Candidate layout and installer contract

Add a V2-specific installer under `adapters/opencode-v2/`. It accepts only a
new absolute destination outside the source tree and rejects paths containing
template, glob, or `.env.` components. It copies these canonical files into
`<destination>/bundle/`:

- `skills/`, `agents/`, `resources/`, and required `docs/` files;
- `plugin.json`, `LICENSE`, `README.md`, and the required V2 host guide.

The installer writes an `installation.json` containing the plugin name,
version, selected OpenCode V2 version, explicit experimental status, and a
SHA-256 digest for every bundled file. It must refuse an existing path rather
than overwriting a prior candidate.

The installer creates an alias for every canonical `skills/*/SKILL.md` entry.
The aliases point to the copied skill directories, not to the source checkout.
This lets the installed candidate resolve its canonical relative references.
It exposes the skills only through explicit entry points because their
`disable-model-invocation` gates remain in force.

The V2 candidate must remain separate from the user's global OpenCode config.
Users launch it with an explicit configuration environment override and select
the generated `egm` primary agent. Installation does not make a model request.

## V2 agent contract

The generated configuration uses only V2 `agents`, `commands`, `skills`, and
ordered `permissions` fields. It defines the `egm` primary orchestrator and
one `mode: subagent` profile for each canonical reviewer persona. Persona text
stays in `bundle/agents/<persona>.md`; each profile tells the child to read its
canonical persona before reviewing the supplied target.

The `egm` agent must allow dispatch only to the bundled reviewer IDs. It must
instruct the host to create a new `subagent` session for each independent
review, never resume a prior reviewer, wait for completion, and pass only the
task, target, selected source paths, standards, and explicitly required prior
reports. It must not pass parent conversation history, rationale, memory, or
unrelated reviewer findings.

The orchestrator writes reports and honors every canonical approval gate. It
must report missing dispatches, completions, or required reads as incomplete;
it must not simulate a Goldfish review in the parent session.

### Reviewer permissions

Each V2 reviewer uses a deny-first, ordered permission list. After a broad
deny, it allows only local `read` and `glob` operations needed for the review,
with these later exceptions and denials:

- deny `read` for `.env` and `.env.*`; allow `.env.example`;
- deny `grep`, `edit`, `shell`, `webfetch`, `websearch`, `skill`, `subagent`,
  and all MCP tools and MCP resource-list/read operations;
- deny external directories except the candidate bundle that contains the
  canonical personas, standards, and host guide.

The external-directory exception does not grant access to arbitrary paths.
Review documents and code must be inside the active project location. A target
outside that location requires a separate, explicit user decision rather than
a wider reviewer policy.

Permission rules are a host-level tool boundary, not a process or filesystem
sandbox. In OpenCode V2, `grep` authorization matches the search expression,
not the search path, so reviewers must not receive it: otherwise it can bypass
the `.env` read restriction. A reviewer can still infer information from files
it is permitted to read.

## Context and data boundaries

OpenCode V2 subagents begin in separate child sessions. The adapter uses that
mechanism to avoid passing the parent conversation into Goldfish reviewers.
It must never claim more than this verified parent-turn boundary.

OpenCode V2 can inject global or project instruction files, and a shared
project filesystem can expose prior reports or unrelated project files. The
adapter cannot disable all such host-level context. The guide and test record
must call these limitations out explicitly. Reviewers must be instructed not
to retrieve unsolicited history, memory, or earlier findings, but instructions
are not proof of enforcement.

EGM itself sends no runtime telemetry. It has no hosted service, database,
analytics client, or required EGM account. Prompts, project files, and model
responses are processed by the selected OpenCode provider under that
provider's terms and retention settings.

## Commands and user interaction

Commands call the canonical skill by absolute installed path under the `egm`
primary agent. Their templates preserve explicit user input without relying on
the V1 command implementation. The V2 guide warns users not to place untrusted
material in slash-command arguments until the selected OpenCode version's
command interpolation behavior is tested and documented. Users can instead
save the material in a project file and request an ordinary-message review.

The guide documents the exact tested OpenCode V2 release and a launch command.
It also explains that selecting another primary agent removes the adapter's
orchestrator dispatch contract.

## Validation and evidence

Add unit coverage for the V2 installer that checks:

- complete resource copying, SHA-256 identity, safe destination validation, and
  overwrite refusal;
- V2 field names and absence of deprecated V1 configuration fields;
- canonical skill alias resolution and command-to-skill identity;
- all reviewer profile IDs, persona references, and deny-first permission
  ordering;
- `.env`, `.env.*`, `.env.example`, MCP, shell, edit, skill, subagent, and
  external-directory policy outcomes.

Add a V2-specific native probe using an OpenCode-provided scripted local model
and a clean profile. The probe must make no live provider request. It records
whether a new child session starts, whether it receives the task but not a
parent-only marker, whether it reads its required persona, and whether a
synthetic `.env` read is denied. It must also inspect the actual child tool
inventory and report any extra tool even when that tool's calls are denied.

The probe result is not a full workflow pass. It does not establish review
quality, approval pauses, inherited-instruction exclusion, general context
isolation, process isolation, filesystem isolation, or host behavior outside
the tested V2 version and platform.

Live validation requires an explicitly authorized, clean-profile run of
brainstorm, draft, and review with real human approval pauses. Record the EGM
source commit, installed file hashes, OpenCode version, platform, model,
reviewer starts and completions, required reads, produced artifacts, and each
denial result. Retain sensitive raw traces privately and publish only a
sanitized summary.

## Rollout and rollback

The implementation is a separate Stage 2 pull request after this design is
approved and merged. It closes #470 only when the agreed acceptance criteria
are met. Until then, the V2 adapter stays experimental and is not added to the
supported-harness table.

The V1 adapter remains unchanged. If the V2 adapter proves unsafe or drifts
from OpenCode, remove only its separate adapter, guide, tests, and workflow;
do not weaken global user permissions or downgrade the user's OpenCode install.

## Alternatives considered

- **Use the V1 adapter with V2.** Rejected because it uses obsolete interfaces
  and lacks a verified V2 permission and dispatch contract.
- **Copy the skills alone into a global skill folder.** Rejected because EGM
  requires adjacent personas, standards, and host guidance, and discovery alone
  does not establish Goldfish review behavior.
- **Use a generic V2 subagent with no persona wrapper.** Rejected because it
  does not enforce reviewer-specific read-only permissions or ensure canonical
  persona loading.
- **Wait for a universal adapter framework.** Rejected because the V2 adapter
  can be small, host-specific, and independently testable.

## Acceptance criteria

1. A V2-native candidate installs without changing user global configuration.
2. Its installed resources match the selected EGM source commit and recorded
   file digests.
3. Every reviewer is a non-primary, read-only V2 subagent and can read only the
   allowed project and bundle resources.
4. Reviewers cannot read synthetic `.env` files or use write, shell, network,
   MCP, skill, or child-delegation tools in the native probe.
5. The orchestrator creates fresh reviewer sessions, propagates only allowed
   inputs, and marks unavailable or incomplete reviewers as incomplete.
6. Offline checks and the version-pinned credential-free probe pass.
7. Documentation states remaining V2 workflow and isolation gaps without a
   support claim.
