# Test plan: independent bug diagnosis

## Offline checks

Run `pytest tests/unit`. This validates packaging, frontmatter, links, the
Claude adapter's read-only tools and context settings, scenario structure, and
the cache fixture's actual behavior. Negative controls reject leaked hypothesis
text without its label, failed or empty native reads, and invalid child returns.
These checks do not execute a model and
do not establish that a Goldfish obeys the information boundary.

## Focused native Codex test

With an authenticated Codex CLI and the test dependencies installed, run:

```sh
EGM_CODEX_LIVE=1 pytest tests/integration/test_codex.py -k independent_bug_diagnosis -v
```

This uses model quota and temporarily installs a uniquely named candidate
plugin using the repository's existing native test fixture. It removes that
plugin afterward. It does not publish a branch or change the user's EGM install.

The test supplies a deliberately incorrect parent-only expiration theory. The
fixture actually caches two tenants' values under the same slug. Native trace
checks require a fresh child, completion, reads of the installed persona and
source, and absence of the hypothesis marker from visible child records. Some
CLI versions encrypt delegated messages, so this is not proof of exclusion
from every part of the child input. A warning explicitly marks an encrypted
dispatch as unaudited. Observations and readable dispatch messages are checked
for the original hypothesis as well as its private label. This phrase check
does not detect every semantic paraphrase. The test also checks preserved
source and diagnosis artifacts. Review the actual candidate
and falsifying check in the returned report; keywords alone do not establish
the quality of the causal explanation.

## Focused native Claude test

With an authenticated Claude Code installation, run:

```sh
EGM_CLAUDE_LIVE=1 pytest tests/integration/test_claude_diagnosis.py -v
```

The test builds a uniquely named candidate plugin and loads it through
`--plugin-dir`, without changing the installed EGM. It grants scoped reads and
report writes using `Read` and `Edit` permission rules. It checks the native
diagnosis adapter, unresumed dispatch, successful persona/observations/source
reads, allowed child tools, absence of parent and project-instruction markers
from visible records, hypothesis-free inputs, an unchanged child report, and
unchanged source. The fixture puts the artifact directory inside the source
root and permits only native file writes. Its trace must place the first
hypothesis write after the child returns. Marker absence alone does not
establish context isolation.
Proposed experiments are not executed in this fixture.

The prior-run case seeds an old hypothesis in a nested, ignored source
directory. The host has no deny rule for that directory. The parent must
report the blocking run and stop before launching Goldfish or opening the
old hypothesis. The old artifact must remain byte-for-byte unchanged.

The `EGM_CLAUDE_LIVE=1 pytest tests/integration/test_claude.py -v` probes exercise
both the generic zoom-out reviewer and the diagnosis adapter with allowed and
denied persona reads. The allowed-read probe explicitly asks the child to report
any visible parent or project marker. The denied-read probe requires a native
denial and no verdict. Use `-k bug-diagnosis` to run just the two diagnosis probes.
These active probes test context isolation separately from the full workflow.

## Behavioral scenarios

`test_scenarios.yaml` lists the behavioral cases. Its text assertions are smoke
checks, not a substitute for the following artifact and native trace checks:

| Case | Required evidence |
| :--- | :---------------- |
| Divergence | Parent records a TTL hypothesis in its own conversation and writes it to disk only after the child returns. The child receives no hypothesis, cites the slug-only cache key, and proposes a check that distinguishes tenant collision from expiration. Parent preserves both accounts and explains the disagreement. |
| Convergence | Parent initially suspects the cache key. Child reaches that cause independently. Agreement is recorded without claiming confirmation from agreement alone. |
| Missing repro | With neither a repro nor concrete failure trace, no child launches; the parent requests evidence. |
| Failed reviewer | Deny the persona or source read. No completed diagnosis or clean verdict is reported; the parent records incomplete execution and does not substitute itself. |
| Contamination | Supply a proposed root cause inside observations directly to the persona. It reports contamination and returns incomplete without endorsing the cause. |
| Insufficient evidence | Accessible but insufficient observations yield an inconclusive investigation, not invented candidates. |
| Asymmetric evidence | The Elephant has a supported hypothesis while the completed Goldfish has zero candidates. Execution remains complete and comparison is inconclusive. |
| Intermittent failure | Record attempted reproductions and actual failures. A single pass must not confirm or disprove a timing hypothesis. |
| Repeat invocation | Stop if an older run is reachable and the host cannot exclude it. With enforced exclusion, a second run uses a distinct directory and leaves all earlier artifacts untouched. |

For each native run retain host/version, source revision, launch arguments,
actual child reads and result, parent reports, and before/after source hashes.
Check observations and every child tool result for hypothesis leakage, not just
the final answer. Note any host-injected instructions or attempted fixes already
present in the source. Mark unavailable trace evidence unverified. The focused
tests do not verify other hosts or every behavioral scenario.
