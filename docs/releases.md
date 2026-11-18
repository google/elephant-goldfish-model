# Versioned releases

The canonical version is `plugin.json`'s `version`. Every host manifest that
declares an EGM version must match it, including experimental adapters such as
Cursor when present. Marketplace catalogs without a version field do not need
one. Version synchronization does not add a host to release support; other host
adapters still need explicit packaging and verification.

While EGM is pre-1.0, use patch bumps for compatible fixes and minor bumps for
features or incompatible workflow changes. Explain breaking changes in release
notes. Version 1.0 requires a stable contract for skill names, parameters, output
paths, and report formats. Do not change published artifacts under the same tag.

## Prepare a candidate

1. Update `plugin.json` and every host manifest (`.claude-plugin/plugin.json`,
   `.codex-plugin/plugin.json`, `.cursor-plugin/plugin.json`, and
   `.plugin/plugin.json`) to the same version in a reviewed PR.
   `scripts/prepare_release.py` rejects a tag when any of them differs.
2. Run `pytest tests/unit`. Include any migration notes in the PR.
3. After merge, a maintainer creates and pushes an annotated `vMAJOR.MINOR.PATCH`
   tag on the selected main commit. Never move an existing release tag.
4. Run **Prepare draft release** from `main`, supplying that existing tag.
   The tagged commit must include the release scripts and pass unit tests.
5. Review the draft's two runtime ZIPs, `SHA256SUMS`, the provenance bundle
   (`egm-vMAJOR.MINOR.PATCH.intoto.jsonl`), and source commit.
   Verify both ZIP attestations as described below. Replace
   placeholder notes with changes, compatibility/migration details, and exact
   artifact host-verification evidence. Unverified hosts remain unverified.
6. Publish the draft manually only after review. Directory publication is separate.

The workflow does not create tags, overwrite releases, publish automatically,
or run paid live tests. A duplicate release attempt fails instead of replacing
an existing release. Fix a failed build before creating a new candidate version.
For local preparation, use a fresh output directory:

```sh
python scripts/prepare_release.py --tag v0.1.0 --commit "$(git rev-parse HEAD)" --output /tmp/egm-0.1.0-candidate
```

The local command checks manifest versions and builds artifacts. It does not
verify the caller-supplied source SHA, Git tag ancestry, or tests. Those checks
belong to the workflow. Publish only workflow-built candidates after
exact-artifact checks. Local builds remain diagnostic candidates.
Exact installed-bundle verification remains tracked in
[#60](https://github.com/google/elephant-goldfish-model/issues/60).

## Launch v0.2.0 on OpenAI

The v0.2.0 candidate includes engineering `egm-lite` (merged in #438) and adds
document-first `egm-in-chat` to the existing EGM OpenAI plugin.
Keep the `egm` package name and the
[existing public listing](https://chatgpt.com/plugins/plugins_6aeb90f47ec88191a3c107e01d3eb357).
The private preview is a test fixture, not the listing to publish.
Merging the PRs or publishing a GitHub release does not update OpenAI.

### Changes for the release notes

- Use one OpenAI package for ChatGPT web and desktop, with nine skills.
- Add `egm-lite` for small repository-backed engineering tasks and explicit
  checklist, execution, and review phases. Goldfish review still requires
  verified fresh-context subagents.
- Add document brainstorming, drafting, and same-context review through
  `egm-in-chat`, without requiring a shell or repository.
- Check the current chat's tools before full EGM workflows start. Independent
  review still requires verified fresh-context subagents and artifact access;
  repository workflows also require repository access and command execution.
- Keep the Claude archive and repository-based coding-harness installs at
  eight skills, including `egm-lite`. Existing skill names remain unchanged.

### Release and publication checklist

- [ ] Before merging #464, build a local v0.2.0 candidate using
  `scripts/prepare_release.py` and the reviewed commit. Complete the web and
  desktop host checks required by the design and attach the results to the
  PR. Local preparation does not require creating a Git tag.
- [ ] Merge the design (#435), then the implementation (#464), through native
  [stack #472](https://github.com/google/elephant-goldfish-model/stack/472),
  after the required reviews and implementation checks.
- [ ] Confirm all five versioned manifests are `0.2.0`. A maintainer creates
  the annotated `v0.2.0` tag on the merged main commit and runs **Prepare draft
  release** from `main` with that tag, as described above.
- [ ] Download `egm-openai-0.2.0.zip`, `SHA256SUMS`, and the provenance bundle
  from the resulting GitHub draft release. Verify checksums and attestations.
  Use this workflow-built archive for final host verification and OpenAI upload.
- [ ] Install that exact archive in clean ChatGPT web and desktop chats.
  Record its checksum, host version or date, installation, skill discovery,
  document brainstorm/draft/review, and missing-capability behavior. Verify
  full `egm-brainstorm`, `egm-draft`, and `egm-review` on a capable desktop
  host, including native reviewer-isolation evidence. Verify `egm-lite`'s
  engineering workflow on a capable host too. Earlier private-preview
  smoke tests do not complete this check.
- [ ] Replace the GitHub draft's placeholder notes with the changes above,
  compatibility details, and exact-archive test results. Publish the GitHub
  release after maintainer review.
- [ ] In the [OpenAI plugin submission portal](https://platform.openai.com/plugins),
  the authorized publisher opens the existing EGM submission in its owning
  organization and creates a new draft version. Upload
  `egm-openai-0.2.0.zip`; do not create another plugin or use the private
  preview's identity.
- [ ] Verify the saved draft's `egm` identity, version, nine skills (including
  both `egm-lite` and `egm-in-chat`), listing,
  icons, four listing URLs, verified publisher, and saved country settings.
  Resolve validation errors and complete the portal's required attestations.
  This is a skills-only plugin; it adds no MCP connection or credentials.
- [ ] Submit the saved draft for review. Record its version, submission
  reference, and actual review state. Upload success alone is not submission
  or publication.
- [ ] After approval, the authorized publisher publishes that approved
  version. Check the existing public listing and install from it in fresh web
  and desktop chats to verify the released skill inventory and behavior.
  Record publication evidence before calling v0.2.0 launched.

The source version and local archives are release candidates until these
steps are complete. Portal access, saved submission metadata, host tests,
review approval, and publication must be verified at their owning surfaces.
See OpenAI's [submission workflow](https://developers.openai.com/plugins/deploy/submission).

## Verify downloads

Download both ZIPs, `SHA256SUMS`, and the provenance bundle into one directory.
With GitHub CLI installed, run these commands from that directory:

```sh
sha256sum -c SHA256SUMS
for archive in egm-claude-*.zip egm-openai-*.zip; do
  gh attestation verify "$archive" --repo google/elephant-goldfish-model \
    --signer-workflow google/elephant-goldfish-model/.github/workflows/release.yml \
    --source-ref refs/heads/main || exit 1
done
```

The workflow signs both ZIP digests and stores provenance in GitHub before
creating a draft. The same attestation is attached to the release as
`egm-<tag>.intoto.jsonl`. It is not listed in `SHA256SUMS`. To verify a ZIP
against that downloaded bundle, pass it with `--bundle`:

```sh
gh attestation verify egm-claude-0.1.2.zip --repo google/elephant-goldfish-model \
  --bundle egm-v0.1.2.intoto.jsonl
```

Add the same `--signer-workflow` and `--source-ref` flags as above.

Signing failure blocks draft creation. Local preparation does not create
attestations. The build job uses `id-token: write` to request a signing
certificate and `attestations: write` to store the result. It cannot write releases.

The provenance identifies the workflow run from `main`. The tagged source checked
out during that run can be a different commit. Check the release notes for that
source SHA and inspect the workflow run before publication. Attestations do not
establish host support or prove that the code is safe.
