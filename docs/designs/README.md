# EGM Design Specifications

This directory contains the canonical technical design specifications defining
the Elephant-Goldfish Model (EGM) framework, skills, reviewer personas, and
operational guardrails.

| Document | Author | Primary Component |
| :------- | :----- | :---------------- |
| [skill_icons.md](skill_icons.md)<br>Canonical skill artwork shared by plugins, the README, and the website. | [@n3wth](https://github.com/n3wth) | Skill presentation |
| [runtime_packaging.md](runtime_packaging.md)<br>Draft runtime package boundaries, permissions, and validation. | [@n3wth](https://github.com/n3wth) | Runtime packaging implementation (#136) |
| [releases.md](releases.md)<br>Draft versioned archives, checksums, and manual release procedure. | [@n3wth](https://github.com/n3wth) | Release implementation (#137) |
| [architecture.md](architecture.md)<br>System architecture of the EGM framework covering component models, end-to-end dataflow, and agent lifecycle. | [@quinnjim](https://github.com/quinnjim), [@eewing314](https://github.com/eewing314) | [EGM Framework Architecture](../../README.md) |
| [brainstorm.md](brainstorm.md)<br>Fast zero-doc ideation tool using a 6-lens Goldfish swarm to audit and stress-test early concepts before drafting. | [@briansuchy](https://github.com/briansuchy) | [`egm-brainstorm`](../../skills/egm-brainstorm/SKILL.md) |
| [draft.md](draft.md)<br>Iterative section-by-section specification drafting protocol and semantic boundary definitions. | [@quinnjim](https://github.com/quinnjim), [@eewing314](https://github.com/eewing314) | [`egm-draft`](../../skills/egm-draft/SKILL.md) |
| [drift_report.md](drift_report.md)<br>Automated scanner to detect and report divergence between checked-in design specifications and live codebase implementations. | [@quinnjim](https://github.com/quinnjim) | [`egm-drift-report`](../../skills/egm-drift-report/SKILL.md) |
| [bootstrap.md](bootstrap.md)<br>Bottom-up recursive bootstrapping and sentinel-block upserting of documentation across package and repository trees. | [@briansuchy](https://github.com/briansuchy) | [`egm-bootstrap`](../../skills/egm-bootstrap/SKILL.md) |
| [review.md](review.md)<br>Multi-stage verification protocol and automated resolution engine using isolated Goldfish reviewer personas. | [@tearseb](https://github.com/tearseb), [@briansuchy](https://github.com/briansuchy) | [`egm-review`](../../skills/egm-review/SKILL.md) |
| [synthesizer.md](synthesizer.md)<br>Intermediate orchestration subagent to coordinate swarm fan-out, deduplicate critiques, and normalize link citations. | [@briansuchy](https://github.com/briansuchy) | [`synthesizer`](../../agents/synthesizer.md) |
| [additional-harnesses.md](additional-harnesses.md)<br>Proposed support for Cursor, OpenCode, and Copilot CLI. Maintainer scope approval is pending. | [@n3wth](https://github.com/n3wth) | [Harness integrations](../harnesses.md) |
| [multi_harness_support.md](multi_harness_support.md)<br>Proposed integration requirements and verification gates for Hermes Agent, OpenClaw, and Delta; native support remains unverified. | [@Seburan](https://github.com/Seburan), [@yathamsriram243-blip](https://github.com/yathamsriram243-blip) | [Harness Architecture](../harnesses.md) |
