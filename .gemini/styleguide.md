# Elephant-Goldfish Model (EGM) Review Style Guide

Review pull requests only for high-severity correctness, packaging, security, or specification defects in changed lines. Never post style nits, summary banners, or speculative suggestions on untouched lines.

## 1. Repository Invariants

* **Skill and Agent Naming**: Every `skills/<dir>/SKILL.md` file must include YAML frontmatter with `name` equal to the directory name (`egm-*`) and a non-empty `description`. Every `agents/<slug>.md` file uses a snake_case filename without an `egm-` prefix (for example, `agents/design_critic.md`, `agents/implementation_readiness.md`, `agents/zoom_out.md`, `agents/comprehension.md`) while its frontmatter `name` uses `egm-*` and includes a non-empty `description`.
* **GitHub Flavored Markdown Tables**: Never use multiline `:` continuation rows in Markdown tables. Every table row must stay on one line so GitHub renders it properly.
* **Relative Link Integrity**: All relative Markdown links and intra-document `#heading` anchors must resolve on disk.
* **GitHub Actions Security (`zizmor`)**: Keep top-level workflow `permissions` minimal (`{}` or `contents: read`). Declare write scopes only on the specific job that needs them, and set `persist-credentials: false` on `actions/checkout`.
* **Silent Failure and Comment Accuracy**: Flag swallowed exceptions, unlogged error fallbacks, and modified comments or docstrings that contradict the implementation.

## 2. Negative-Rule Ledger (Do Not Flag)

Do not flag any of the following intentional repository conventions:

* **Missing `$schema` in Root `plugin.json`**: Root `plugin.json` intentionally omits `$schema` so OhMyPi (`omp`) and OpenCode parsers do not reject the manifest. The Copilot CLI manifest at `.plugin/plugin.json` carries `$schema`.
* **Snake-Case Agent File Paths**: Files under `agents/` and `.claude-plugin/agents/` do not use an `egm-` filename prefix (`agents/design_critic.md`, not `agents/egm-design.md`). Never ask contributors to rename valid snake_case agent paths to `agents/egm-*.md`.
* **Hardcoded SHA Pins in `.github/workflows/`**: Repository security rules require Action SHA pins and `zizmor: ignore[...]` annotations with inline justifications.
* **Scope Advisory Thresholds**: Do not duplicate scope or template checks handled by `.github/workflows/pr-scope-advisory.yml`.

## 3. Comment Formatting Rules

* **Direct Opening**: Start every comment with `[High]: <1-sentence defect summary>. <1-sentence fix>`. Never print meta-labels such as `BLUF:`, `Bottom line:`, `Summary:`, or `Issue:`.
* **Committable Suggestions**: Include a 1-5 line GitHub `suggestion` block only when committing the block fixes the defect completely without follow-up edits.
* **Concise Technical Prose**: Keep sentences at or under 25 words in active voice and present tense. Avoid em dashes, semicolons, filler praise, and counted preambles.
* **Respect Author Pushback**: Do not re-open or argue a thread after a contributor or maintainer replies `intended`, `by design`, or `won't fix`.
