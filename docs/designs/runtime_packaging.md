# Runtime packaging

Status: Draft. Maintainer scope approval and design review are pending.
Author: @n3wth. Date: 2026-10-24.

Related issues: #121 and #122. Proposed implementation: #136.

## Problem and scope

Users need runtime packages with the resources required by each host. A full
repository archive also contains development files and website assets.

Build Claude and OpenAI runtime packages from one source tree. Preserve normal
user-controlled permissions. Do not add new hosts, services, or automatic
permission approval. Package validation does not establish directory approval
or runtime support.

## Package contract

Use `scripts/pack_plugin.py`, proposed in #136, as the single builder.
`--target claude|openai` selects the host. `--output` selects a new destination.
Produce an `egm-TARGET` folder and an `egm-TARGET.zip` archive.

Allowlist manifests, skills, references, personas, native adapters, required
documentation, licenses, and image assets. Include SVG and PNG files under
`docs/assets` for README images. Exclude website content, tests, workflows,
hooks, development marketplace metadata, and unrelated files.

The target inventory is explicit:

- Shared: `plugin.json`, `LICENSE`, `README.md`, `skills/*/SKILL.md`,
  `skills/*/agents/openai.yaml`, skill assets and references, `agents/*.md`,
  `resources/*.md`, and `resources/document_standards/*.md`.
- Shared guides: `docs/index.md`, `docs/getting_started.md`, `docs/harnesses.md`,
  `docs/claude.md`, `docs/codex.md`, `docs/faq.md`, and `docs/privacy.md`.
  Include `docs/releases.md` when release preparation adds that guide.
- Shared images: SVG and PNG files under `assets/` and `docs/assets/`.
- Claude: `.claude-plugin/plugin.json`, `.claude-plugin/icon.png`, and
  `.claude-plugin/agents/*.md`.
- OpenAI: `.codex-plugin/plugin.json`.

The builder's `SHARED`, `HOST`, and `REQUIRED_SHARED` constants implement this
inventory. Required references must exist; optional files must match these paths.

Keep installation guides, host instructions, personas, skills, and review
standards in the runtime. Exclude repository design documents, `TESTING.md`,
`CONTRIBUTING.md`, `AI_POLICY.md`, and the PR template. Link to those development
documents on GitHub from the bundled guides. Reading development documentation
requires network access; executing the bundled skills does not require it.
Check relative Markdown links in both generated runtimes. A development-only
document edit must not require regenerating runtime content.

Reject symlinks, paths outside the source tree, missing required files,
unbundled manifest references, hooks, and unsupported MCP or app dependencies.
Refuse an existing output folder or archive. A failed build can leave partial
output; diagnose the failure and use a new destination for the next attempt.

Sort archive entries and use fixed timestamps and file modes. Verify identical
bytes under the same build environment. Do not claim reproducibility across
untested toolchain versions.

Generate `distributions/claude` from the same builder. Compare every path and
byte against a fresh build in unit tests. Regenerate it when included source
files change. Do not edit generated files independently.

## Permissions and host boundaries

Remove the automatic permission-approval hook. Keep bounded tools on Claude
native adapters. Resource reads use normal host permissions. A denied read
must stop the affected reviewer without a fabricated verdict.

Read-only Claude reviewers allow `Read`, `Grep`, and `Glob`. The synthesizer
also allows `Agent` and `Write` for delegation and reports. Bootstrap allows
`Agent`, `Bash`, `Read`, `Grep`, `Glob`, `Write`, and `Edit` for documentation.
These tool lists do not establish a filesystem or network sandbox.

Test parent-context isolation separately from filesystem access and host-added
instructions or memory. A Claude CLI probe does not establish Cowork behavior.
OpenAI packaging does not establish support for every ChatGPT mode.

## Validation and rollout

- Test required content, image inclusion, exclusions, unsafe paths, missing
  references, overwrite refusal, reproducibility, and generated freshness.
- Verify allowed and denied resource reads against the generated runtime.
- Record the source SHA, installed artifact identity, host/model version,
  and separate installation, workflow, and isolation outcomes.
- Preserve the cloud workflow and isolation gaps in
  [Cowork #105](https://github.com/google/elephant-goldfish-model/issues/105)
  and [ChatGPT Work #106](https://github.com/google/elephant-goldfish-model/issues/106).
- Obtain scope approval and merge this design before merging #136.
- Coordinate tagged artifacts through the [release design](releases.md).

Directory publication in #121 and #122 remains separate. Confirm the owning
account, policy links, publisher authority, and provider findings before
submission. Close those issues only after verifying the published listing.

## Alternatives and open decisions

Separate hand-maintained packages would drift. A full repository ZIP includes
unneeded development content. A shared allowlist keeps package boundaries
explicit and reviewable.

Maintainers must confirm whether #121/#122 provide the packaging approval path
or identify another aligned issue. This draft does not imply that approval or
an EGM design-review run has occurred.
