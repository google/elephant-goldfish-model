# Public Before-and-After Review Example

This showcase demonstrates one complete EGM review finding and its resulting
change. It is **excluded from the scored evaluation set** (`showcase: true` in
[`cases.yaml`](../fixtures/cases.yaml)).

## Original Revision

Consider a plan to refactor `scripts/pack_plugin.py` that originally omitted
offline verification details:

```markdown
## Detailed Implementation Plan
1. Extract `_normalize_archive_path` in `scripts/pack_plugin.py`.
2. Ship the updated build script.
```

## EGM Review Finding

* **Stage**: Stage 9 (Implementation Readiness)
* **Decision**: `hold`
* **Finding (`missing-verification-step`)**: The plan modifies archive path
  normalization in `scripts/pack_plugin.py` without specifying how
  deterministic ZIP output and path-traversal guards in
  `tests/unit/test_packaging.py` will be re-verified.

## Resulting Change

```markdown
## Detailed Implementation Plan
1. Extract `_normalize_archive_path` in `scripts/pack_plugin.py` while keeping
   `build(root, target, output)` and all public CLI flags unchanged.
2. Run `python -m pytest tests/unit/test_packaging.py` to verify deterministic
   ZIP output and unsafe-path rejection.
```

## Plain-Review Comparison Note

When comparing EGM against a plain review, run both with the **same model and
token/turn budget** using `scripts/eval_runner.py compare --outputs ...
--baseline-outputs ...`. Live comparison scores are advisory and kept separate
from offline replay checks.

## Replay Command

Verify the offline parser and scorer (including showcase exclusion) without
model credentials:

```bash
python scripts/eval_runner.py replay
```

Ready to try a first review on your own design? Start with the
[EGM Quickstart](../../docs/getting_started.md).
