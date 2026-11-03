# Multi-Harness Support: Hermes Agent, OpenClaw, and Delta

* **Authors:** Sriram ([@Seburan](https://github.com/Seburan)), Sriram Yatham ([@yathamsriram243-blip](https://github.com/yathamsriram243-blip))
* **Status:** Stage 1 design proposal; native contracts and live runs unverified
* **Updated:** 2026-10-30
* **Refs:** [#116](https://github.com/google/elephant-goldfish-model/issues/116)

## 1. Problem and Goals

EGM shares its skills, personas, and document standards across harnesses.
Adding another host must preserve that shared text and the fresh-context
boundary between drafting and Goldfish review.

This proposal defines requirements for Hermes Agent, OpenClaw, and Delta.
It does not establish working support for any of them.

Goals:

* Reuse the canonical `skills/`, `agents/`, and `resources/` content.
* Select a documented installation format for each specific host release.
* Verify native delegation without parent conversation inheritance.
* Enforce reviewer read-only access through host controls.
* Require installation and workflow evidence before claiming support.

Non-goals:

* Forking skill text or adding a runtime translation service.
* Adding chat bridges, registries, or device synchronization.
* Shipping speculative manifests or untested installation commands in Stage 1.
* Claiming support from offline metadata tests alone.

## 2. Heilmeier Assessment

| Question | Assessment |
| --- | --- |
| What are we trying to do? | Run EGM on three additional hosts while preserving shared prompts and independent review. |
| How is it done today? | The [harness guide](../harnesses.md) documents existing integrations. These three integrations have no verified native run attached to this proposal. |
| What is new? | Reuse a compatible bundle where possible. Add a thin host adapter only when a pinned host requires it. |
| Who benefits? | Target-host users and maintainers who would otherwise maintain separate prompt copies. |
| What are the risks? | Unsupported discovery paths, inherited project context, writable reviewers, and premature support claims. |
| What will it cost? | Contributor time and model usage for live probes. Runtime and token costs have not been measured. |
| How long will it take? | Each host proceeds independently after its contracts are verified. No delivery date is committed. |
| What are the exams? | Stage 1 defines acceptance gates. Stage 2 supplies schema, installation, isolation, permissions, and workflow evidence for each host. |

## 3. Host Contracts and Open Questions

The following are research inputs, not tested EGM integrations.
Record the host release and matching documentation or source revision before
turning an input into an implementation contract.

| Host | Documented input | Contract still to verify |
| --- | --- | --- |
| Hermes Agent | Current [delegation documentation](https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation) exposes `delegate_task(goal, context)`. Children have fresh conversations but inherit tool access and may receive workspace project context. | Package discovery, exact installed release, persona loading, project-context suppression, and enforced read-only permissions. Do not assume `hermes.spawn` or a per-call Claude-style tool filter. |
| OpenClaw | The [manifest documentation](https://docs.openclaw.ai/plugins/manifest) distinguishes native `openclaw.plugin.json` plugins from compatible bundles. | Probe the existing EGM bundle first. Otherwise document the native schema and package root. Verify `openclaw plugins install`, loaded plugin identity, and the exact `sessions_spawn` schema against the pinned release. A renamed JSON file does not prove compatibility. |
| Delta | [#116](https://github.com/google/elephant-goldfish-model/issues/116) names Delta as a target. | Confirm the product, upstream repository, release, installation format, and delegation API. No `delta.spawn`, isolation flag, manifest path, or minimum version is specified here. |

No host-specific manifest path or minimum engine version is selected until
the corresponding source and native installation probe establish it.
Named persona discovery and nested delegation are also unverified.

## 4. Architecture and Review Boundaries

The existing root `plugin.json` remains the canonical metadata source.
Use an existing compatible package when it preserves all runtime resources.
If an adapter is required, keep host-specific fields in that adapter.
Copy shared metadata from the canonical manifest and test exact parity for
the fields supported by that host's schema.

Each reviewer receives its persona, target document, and required resources.
Do not forward the parent conversation. Inspect both the submitted child
prompt and host-injected context. A fresh conversation alone does not prove
that project instructions or memory were excluded.

Reviewers must be unable to modify files or execute mutation-capable tools.
Use host-enforced permissions rather than prompt instructions as proof.
Claude's `Read`, `Grep`, and `Glob` are one host-specific example. Other hosts
must map the same no-mutation requirement to their own verified controls.
Do not assume those literal tool names or a universal `tools` argument.

If a host cannot meet the isolation or permission requirements, its Goldfish
review integration remains unsupported. Stop the review rather than running
it in the parent context or with broader permissions.

## 5. Alternatives

| Option | Decision |
| --- | --- |
| Existing compatible bundle | Preferred when a native installation probe proves discovery and resource access. Avoids duplicate metadata. |
| Thin native adapter | Use only when a verified host contract requires it. Keep prompt content canonical. |
| Speculative per-host manifests | Reject. Valid JSON or YAML and metadata parity do not prove host acceptance. |
| Runtime translator or copied skill forks | Exclude because they add maintenance and prompt drift. |

## 6. Delivery Plan

### Stage 1: Design

This PR contains this proposal and its design-index entry only.
It changes no runtime manifests, installation guide, support records, or tests.
Maintainer design approval does not certify native host support.
Keep #116 open for implementation and evidence.

### Stage 2: Implement and Verify One Host

Before implementation, obtain the contribution-track approval required by
[AGENTS.md](../../AGENTS.md). Submit a follow-up against this merged design.

1. Identify the host product, exact release, upstream source, and schema.
2. Probe the existing EGM package before adding an adapter.
3. Implement the smallest required adapter and native delegation mapping.
4. Add offline checks for actual schema, metadata, and resource-path contracts.
5. Run native installation, isolation, permission, and workflow probes.
6. Update [the harness guide](../harnesses.md) and [test record](../../TESTING.md)
   with evidence and explicit limits. Promote only the tested host.

Do not publish guessed installation commands or mark a host supported while
required evidence is missing. Unverified results must remain explicit.

## 7. Validation and Acceptance

Stage 1 runs `pytest tests/unit` and `git diff --check`.
The link test checks relative target existence and same-document anchors
outside hidden directories and other excluded paths. It does not validate
cross-document fragments, external URLs, or native plugin discovery.

Stage 2 must preserve strict JSON parsing for JSON manifests. Use YAML parsing
only for formats that require YAML. Test each selected schema rather than
treating matching metadata as schema validation.

Attach the following evidence for each host:

* Exact host version and source, EGM commit, OS, and model configuration.
* Clean installation commands and output showing which EGM package loaded.
* Discovery and successful reads of skills, personas, and document standards.
* Native child prompts and traces showing parent conversation and unrelated
  project context were excluded. Use a parent-only canary probe.
* Effective child permissions and a negative probe showing mutation attempts
  are blocked. A prompt asking for read-only behavior is insufficient.
* End-to-end `/egm-brainstorm`, `/egm-draft`, and `/egm-review` outputs.
  Verify reviewer completion, required reads, and stage order from traces.
* Limits, failures, and measured usage. Redact credentials before publication.

Offline checks cannot substitute for native probes.
If a required probe fails, leave support unverified and record the failure.

## 8. Regression and Rollback

Pin evidence to the tested release and EGM commit. A later host release does
not inherit a verified result automatically. If discovery, isolation, or
permissions regress, record the affected version, withdraw its support claim,
and fix or revert that host's adapter. Preserve other working integrations
and the shared prompt text.
