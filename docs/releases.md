# Versioned releases

The canonical version is `plugin.json`'s `version`. Claude and Codex manifests
must match it. Keep one EGM version across these hosts; marketplace catalogs
without a version field do not need one. Other host adapters need explicit
packaging and verification before being added to release support.

While EGM is pre-1.0, use patch bumps for compatible fixes and minor bumps for
features or incompatible workflow changes. Explain breaking changes in release
notes. Version 1.0 requires a stable contract for skill names, parameters, output
paths, and report formats. Do not change published artifacts under the same tag.

## Prepare a candidate

1. Update the root, Claude, and Codex manifest versions in a reviewed PR.
2. Regenerate `distributions/claude` using the runtime builder and run
   `pytest tests/unit`. Include any migration notes in the PR.
3. After merge, a maintainer creates and pushes an annotated `vMAJOR.MINOR.PATCH`
   tag on the selected main commit. Never move an existing release tag.
4. Run **Prepare draft release** from `main`, supplying that existing tag.
   The tagged commit must include the release scripts and pass unit tests.
5. Review the draft's two runtime ZIPs, `SHA256SUMS`, and source commit. Replace
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

The local command checks manifest versions and builds artifacts; it does not
verify Git tag ancestry or run tests. Those checks belong to the workflow.
Exact installed-bundle verification remains tracked in
[#60](https://github.com/google/elephant-goldfish-model/issues/60).
