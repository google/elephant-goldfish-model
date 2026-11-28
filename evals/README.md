# EGM Reproducible Evaluations

This directory defines the offline-capable evaluation fixtures, external dataset
manifest, and public showcase for EGM reviews.

## Replay Checks vs. Live Runs

* **Replay checks** (`python scripts/eval_runner.py replay`) verify the fixture
  schemas, external dataset manifest, output parser, and scorer in offline fork
  CI without dataset downloads or model credentials. They test the **scorer and
  parser**, not live model behavior.
* **Live runs** (`python scripts/eval_runner.py compare ...`) measure actual
  review behavior against pinned cases and a plain-review baseline using the
  same model and budget. Live scores are **advisory**.

## Directory Contents

* [`fixtures/cases.yaml`](fixtures/cases.yaml): Original review fixtures
  (`public-api-preserved`, `new-dependency-added`,
  `missing-evidence-owner-question`) plus a `showcase: true` entry excluded from
  the scored set.
* [`fixtures/replay/review_outputs.yaml`](fixtures/replay/review_outputs.yaml):
  Synthetic review outputs used to verify the review scorer and parser offline.
* [`fixtures/replay/factuality_outputs.yaml`](fixtures/replay/factuality_outputs.yaml):
  Synthetic factuality judge outputs used to verify per-dataset clean/flawed
  recall reporting offline.
* [`manifests/external_cases.yaml`](manifests/external_cases.yaml): Pinned
  revisions, checksums, case IDs, split rules, and attribution for RAGTruth,
  SummEdits, held-out EGM plans, and TREK trips. Corpora and raw traces stay out
  of Git and are fetched on demand.
* [`showcase/public_review_example.md`](showcase/public_review_example.md):
  Public before-and-after review example (excluded from the scored set).

## Running Checks

```bash
# Offline fork CI checks (no credentials or network required)
python -m pytest tests/unit
python scripts/eval_runner.py replay

# Validate the external dataset manifest without downloading corpora
python scripts/eval_runner.py manifest

# Score a fresh maintainer comparison (advisory live scores)
python scripts/eval_runner.py compare \
  --cases evals/fixtures/cases.yaml \
  --outputs path/to/egm_outputs.yaml \
  --baseline-outputs path/to/plain_review_outputs.yaml
```

Keep harness-specific results separate (for example, `native_claude_code`
workflow runs vs. `managed_agents` persona runs) and record harness isolation
as a separate verification result.
