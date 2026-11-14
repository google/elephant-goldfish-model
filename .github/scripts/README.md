# Scripts

## Overview
Automated Stage-1 PR triage and two-pass Goldfish review planner. Runs read-only inside the `review` job (trusted default-branch checkout) using the Python standard library only, and emits `review-plan.json` for the isolated `post` job. The module also defines its default repository, branch, primary and fallback models, API bases, comment limits, and review labels.

## Interface
- [.github/scripts/review_pr.py:RepoReviewConfig] Holds ignore patterns, the review-comment limit, and the draft-PR setting.
- [.github/scripts/review_pr.py:GateDecision] Holds the sweep-gate decision, reason, and review depth.
- [.github/scripts/review_pr.py:load_repo_config] Loads `.gemini/config.yaml` with safe defaults and a standard-library fallback.
- [.github/scripts/review_pr.py:is_ignored_path] Matches changed paths against the configured ignore patterns.
- [.github/scripts/review_pr.py:classify_review_depth] Classifies a PR as `lite`, `focused`, or `full` from changed paths and non-test line count.
- [.github/scripts/review_pr.py:validate_pr_template] Checks PR body conformance with the contribution template.
- [.github/scripts/review_pr.py:load_claude_bundle_globs] Extracts the Claude bundle globs from `scripts/pack_plugin.py`.
- [.github/scripts/review_pr.py:is_claude_bundled_source_path] Reports whether a repository path is packaged into `distributions/claude/`.
- [.github/scripts/review_pr.py:check_claude_bundle_parity] Verifies `distributions/claude/` parity against changed source files using Git blob SHAs.
- [.github/scripts/review_pr.py:collect_repo_inventory] Collects the canonical repository file inventory for prompt grounding.
- [.github/scripts/review_pr.py:filter_false_positive_findings] Removes findings that cite paths absent from the repository.
- [.github/scripts/review_pr.py:evaluate_sweep_gate] Evaluates anti-noise guardrails before calling Gemini.
- [.github/scripts/review_pr.py:parse_valid_right_lines] Maps each changed file to the diff right-side lines that accept comments.
- [.github/scripts/review_pr.py:build_diff_context] Builds bounded diff text prioritized by source-file importance.
- [.github/scripts/review_pr.py:sanitize_comment_body] Neutralizes bare mentions and unsafe text in review comments.
- [.github/scripts/review_pr.py:normalize_findings] Normalizes model findings into the review payload schema.
- [.github/scripts/review_pr.py:should_post_findings] Decides whether the remaining findings clear the posting threshold.
- [.github/scripts/review_pr.py:format_inline_comment_body] Formats a finding as a line-anchored inline comment.
- [.github/scripts/review_pr.py:build_review_payload] Builds a GitHub pulls/reviews payload anchored strictly to diff lines.
- [.github/scripts/review_pr.py:needs_maintainer_assignment] Decides whether the maintainers team needs an explicit review request.
- [.github/scripts/review_pr.py:build_clean_handoff_plan] Builds the clean-handoff plan and maintainer routing payload.
- [.github/scripts/review_pr.py:build_pass1_prompt] Builds the Pass 1 prompt for high-severity candidate defects.
- [.github/scripts/review_pr.py:build_pass2_disproof_prompt] Builds the Pass 2 prompt that tries to disprove Pass 1 findings.
- [.github/scripts/review_pr.py:build_model_chain] Builds an ordered, deduplicated Gemini model chain.
- [.github/scripts/review_pr.py:call_gemini_json] Calls Gemini and parses a JSON response.
- [.github/scripts/review_pr.py:call_gemini_with_fallback] Tries the model chain and falls back on eligible HTTP failures.
- [.github/scripts/review_pr.py:resolve_pr_number] Resolves the open PR from an explicit number, head SHA, or default branch.
- [.github/scripts/review_pr.py:parse_fallback_models] Parses the comma-separated Gemini fallback-model chain.
- [.github/scripts/review_pr.py:plan_pr_review] Computes the end-to-end two-pass review plan without GitHub mutations.
- [.github/scripts/review_pr.py:main] Runs the CLI, writes the plan, and emits GitHub Action outputs.
- [.github/scripts/review_pr.py:main] Accepts repository, branch, PR or head SHA, model and fallback-model, styleguide, config, repo-root, output, and force-manual options.

## Invariants
- [.github/scripts/review_pr.py:plan_pr_review] Computes the review plan without GitHub mutations.
- [.github/scripts/review_pr.py:load_repo_config] Falls back to safe defaults when the config file is absent, unreadable, or PyYAML is unavailable.
- [.github/scripts/review_pr.py:classify_review_depth] Treats changes under `skills/`, `agents/`, `site/`, or `docs/designs/`, or in a root manifest, as `full`, and changes under `.github/`, `scripts/`, `adapters/`, or `tests/` as `focused`.
- [.github/scripts/review_pr.py:build_pass1_prompt] Wraps untrusted PR metadata, diffs, and prior bot notes inside a per-call nonce boundary.
- [.github/scripts/review_pr.py:build_pass2_disproof_prompt] Requires canonically cited findings and rejects invented file paths.
- [.github/scripts/review_pr.py:call_gemini_with_fallback] Retries only fallback-eligible pool errors and advances through the ordered model chain.

## Side Effects
- [.github/scripts/review_pr.py:main] Writes `review-plan.json` and appends `has_action`, `action`, `reason`, and `depth` to `GITHUB_OUTPUT`.
- [.github/scripts/review_pr.py:plan_pr_review] Reads GitHub pull, review, and repository data without writing to GitHub.

## Verification
- Run: `python3 -m pytest tests/unit/test_pr_triage_review.py`
