# EGM Design Specifications

This directory contains the canonical technical design specifications defining
the Elephant-Goldfish Model (EGM) framework, skills, reviewer personas, and
operational guardrails.

| Document | Author | Primary Component |
| :------- | :----- | :---------------- |
| [openspec.md](openspec.md)<br>Draft standalone bidirectional OpenSpec (`spec-driven` v1 schema) interoperability orchestrator (`validate_openspec.py` stdlib validator, bounded baseline import, `egm-codebase-details` export fidelity check, and minimal core-skill intake pointers). | [@briansuchy](https://github.com/briansuchy) | `egm-openspec`, [`egm-brainstorm`](../../skills/egm-brainstorm/SKILL.md), [`egm-draft`](../../skills/egm-draft/SKILL.md), [`egm-review`](../../skills/egm-review/SKILL.md) (#383) |
| [site_documentation.md](site_documentation.md)<br>Proposed multi-page guide, skill reference, and shared site interface. | [@n3wth](https://github.com/n3wth) | Website and documentation |
| [triz_integration.md](triz_integration.md)<br>Draft Soviet TRIZ method integration introducing the Inventive Catalyst persona to eliminate false architectural compromises in `/egm-brainstorm` and Step 5 of `/egm-review`. | [@briansuchy](https://github.com/briansuchy) | [`egm-brainstorm`](../../skills/egm-brainstorm/SKILL.md), [`egm-review`](../../skills/egm-review/SKILL.md) (#37) |
| [ask.md](ask.md)<br>Draft read-only command that answers questions about EGM and suggests the next skill from workspace artifacts. | [@smituparmar01](https://github.com/smituparmar01) | `egm-ask` (#175) |
| [skill_icons.md](skill_icons.md)<br>Canonical skill artwork shared by plugins, the README, and the website. | [@n3wth](https://github.com/n3wth) | Skill presentation |
| [runtime_packaging.md](runtime_packaging.md)<br>Implemented runtime package boundaries, permissions, and validation. | [@n3wth](https://github.com/n3wth) | Runtime packaging implementation (#136) |
| [releases.md](releases.md)<br>Implemented versioned archives, checksums, and manual release procedure. | [@n3wth](https://github.com/n3wth) | Release implementation (#137) |
| [claude_release_branch_distribution.md](claude_release_branch_distribution.md)<br>Draft publication of the attested Claude runtime to a generated branch for directory submission. | [@n3wth](https://github.com/n3wth) | Claude directory publication (#121) |
| [architecture.md](architecture.md)<br>System architecture of the EGM framework covering component models, end-to-end dataflow, and agent lifecycle. | [@quinnjim](https://github.com/quinnjim), [@eewing314](https://github.com/eewing314) | [EGM Framework Architecture](../../README.md) |
| [brainstorm.md](brainstorm.md)<br>Fast zero-doc ideation tool using a 7-lens Goldfish swarm to audit and stress-test early concepts before drafting. | [@briansuchy](https://github.com/briansuchy) | [`egm-brainstorm`](../../skills/egm-brainstorm/SKILL.md) |
| [draft.md](draft.md)<br>Iterative section-by-section specification drafting protocol and semantic boundary definitions. | [@quinnjim](https://github.com/quinnjim), [@eewing314](https://github.com/eewing314) | [`egm-draft`](../../skills/egm-draft/SKILL.md) |
| [drift_report.md](drift_report.md)<br>Automated scanner to detect and report divergence between checked-in design specifications and live codebase implementations. | [@quinnjim](https://github.com/quinnjim) | [`egm-drift-report`](../../skills/egm-drift-report/SKILL.md) |
| [bootstrap.md](bootstrap.md)<br>Bottom-up recursive bootstrapping and sentinel-block upserting of documentation across package and repository trees. | [@briansuchy](https://github.com/briansuchy) | [`egm-bootstrap`](../../skills/egm-bootstrap/SKILL.md) |
| [review.md](review.md)<br>Multi-stage verification protocol and automated resolution engine using isolated Goldfish reviewer personas. | [@tearseb](https://github.com/tearseb), [@briansuchy](https://github.com/briansuchy) | [`egm-review`](../../skills/egm-review/SKILL.md) |
| [synthesizer.md](synthesizer.md)<br>Intermediate orchestration subagent to coordinate swarm fan-out, deduplicate critiques, and normalize link citations. | [@briansuchy](https://github.com/briansuchy) | [`synthesizer`](../../agents/synthesizer.md) |
| [additional-harnesses.md](additional-harnesses.md)<br>Proposed support for Cursor, OpenCode, and Copilot CLI. Maintainer scope approval is pending. | [@n3wth](https://github.com/n3wth) | [Harness integrations](../harnesses.md) |
| [windsurf_support.md](windsurf_support.md)<br>Proposed experimental Windsurf Cascade workspace routing and Goldfish isolation boundary. | [@n3wth](https://github.com/n3wth) | [Harness integrations](../harnesses.md) (#376) |
| [multi_harness_support.md](multi_harness_support.md)<br>Proposed integration requirements and verification gates for Hermes Agent, OpenClaw, and Delta; native support remains unverified. | [@Seburan](https://github.com/Seburan), [@yathamsriram243-blip](https://github.com/yathamsriram243-blip) | [Harness Architecture](../harnesses.md) |
| [plugin_listing_presentation.md](plugin_listing_presentation.md)<br>Proposed listing text, starter prompts, and packaged skill assets without workflow-body changes. | [@n3wth](https://github.com/n3wth) | Plugin presentation (#122) |
