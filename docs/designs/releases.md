# Versioned runtime releases

Status: Draft. Maintainer scope approval and design review are pending.
Author: @n3wth. Date: 2026-10-24.

Related issue: #124. Proposed implementation: #137, dependent on #136.

## Problem and scope

Users need identifiable archives built from a reviewed commit. Prepare a draft
release with source identity and checksums, then verify its exact artifacts
before publication.

Reuse the [runtime packaging design](runtime_packaging.md). Do not create tags
automatically, publish automatically, run paid models in CI, or add host support.

## Version and artifact contract

Use the root plugin version as canonical. Require matching Claude and Codex
manifest versions. Accept `vMAJOR.MINOR.PATCH` tags without leading zeroes.
Never reuse a published version for changed artifacts.

The proposed `scripts/prepare_release.py` accepts `--tag`, `--commit`, and
`--output`. Require a full source SHA and a new output directory. Produce:

- `egm-claude-VERSION.zip`
- `egm-openai-VERSION.zip`
- `SHA256SUMS`
- `RELEASE_NOTES.md`, containing the source SHA, tag, and verification limits

Local invocation validates the supplied values and builds archives. It does
not prove Git ancestry or run tests. The workflow owns those checks.
The local source SHA is a caller declaration, not verified source identity.
Label that limitation in the generated notes. Publication uses workflow-built
candidates after source verification and exact-artifact checks.

## Workflow and permissions

Dispatch the workflow manually from `main` with an existing version tag. Resolve
the tag to a commit and require that commit to be an ancestor of `main`. Check
out that commit, run offline tests, and prepare its archives.

The build job has `contents: read`, `id-token: write`, and `attestations: write`.
After building, use a commit-pinned `actions/attest` to sign provenance for both
runtime ZIPs and store it in GitHub. Disable registry storage records; no registry
or artifact-metadata permission is needed. Attestation failure stops the build.
Local preparation does not create attestations.

The provenance identifies the workflow dispatched from `main`. Its source
identity can differ from the selected tag checked out during the job. Release
notes record the tagged source SHA. Review both identities before publication.
Attestations establish artifact provenance, not host compatibility or code safety.
Verification must identify the signing workflow on `refs/heads/main` and the
downloaded ZIP's digest. Compare the recorded tagged SHA with the tag resolved
by the build job. Workflow identity alone does not verify that tag mapping.

A separate draft job receives
the artifacts, verifies their checksums, rechecks tag identity, and creates a
draft with contents-write permission. Duplicate release creation fails without
replacing existing assets. Neither job creates tags or publishes releases.

## Acceptance and release procedure

1. Obtain scope approval for #124 and merge the reviewed design.
2. Merge #136 after its design approval and renewed implementation review.
3. Retarget #137 to `main`, refresh validation, and merge after approval.
4. Select the reviewed version and commit. Regenerate packaged content and
   validate all included runtime changes before a maintainer creates the tag.
5. Dispatch the workflow. Inspect both archives, checksums, and source identity.
   Verify each ZIP with `gh attestation verify FILE --repo google/elephant-goldfish-model`.
   Require the signing workflow `.github/workflows/release.yml` from `main`.
6. Complete [the exact-bundle verification procedure in #60](https://github.com/google/elephant-goldfish-model/issues/60)
   for each claimed host using these exact artifacts. Record
   installed-file identity, host/model versions, date, and separate installation,
   workflow, and isolation results.
   Completion requires clean installation, intended artifact identity, and
   supported workflow and isolation outcomes. Preserve any partial host result.
7. Review final release notes and publish manually. Directory approval remains
   separate from release publication.

Test version mismatch, malformed tags and source IDs, archive contents,
checksums, overwrite refusal, and generated freshness. Lint the workflow and
validate its first real dispatch before accepting release preparation as done.

Reuse historical host evidence only with an explicit explanation of its
applicability. Do not present old candidate results as fresh artifact passes.
Keep cloud support partial while #105 and #106 retain evidence gaps.

## Failure handling and alternatives

Leave a failed or unverified candidate unpublished. Build retries use a fresh
local output directory. Do not replace a published archive or move its tag;
prepare a corrected version instead.

Hand-built releases can omit validation or source identity. Automatic publication
would remove the final evidence review. A validated draft preserves that review
without duplicating the package builder.

This draft does not establish maintainer approval or claim an EGM design-review
run. The issue remains open until the release workflow is validated.
