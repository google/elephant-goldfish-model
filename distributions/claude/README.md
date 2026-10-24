# Elephant-Goldfish Model (EGM)

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Website](https://img.shields.io/badge/Website-egm.dev-black.svg)](https://egm.dev)

Elephant-Goldfish Model (EGM) is an open-source plugin for Spec-Driven Development with AI coding agents. Deep-context Elephant sessions draft specifications, and isolated zero-context Goldfish subagents stress-test them before you write code.

## Install

| Harness | Install |
| :--- | :--- |
| **Any AI agent** | Ask your agent: `Install https://github.com/google/elephant-goldfish-model` |
| **Antigravity** | `agy plugin install https://github.com/google/elephant-goldfish-model` (or `/plugin` in IDE) |
| **Claude Code** | `claude plugin marketplace add google/elephant-goldfish-model && claude plugin install egm@egm` |
| **Codex** | `codex plugin marketplace add google/elephant-goldfish-model && codex plugin add egm@egm` |
| **Claude Cowork / ChatGPT** | See [Harnesses](docs/harnesses.md) for desktop and workspace setup |

## Quickstart

1. **Ideate & Stress-Test**: Run `/egm-brainstorm` to explore problem boundaries and test early concepts with a Goldfish swarm.
2. **Draft**: Run `/egm-draft` to convert the concept brief into a living design document under `docs/designs/<feature>.md`.
3. **Review & Resolve**: Run `/egm-review docs/designs/<feature>.md` to run the multi-stage Goldfish reviewer swarm.
4. **Submit & Implement**: Submit the verified design doc via pull request and implement code against the approved specification.

In Claude Code, commands use the `/egm:` prefix (for example `/egm:egm-brainstorm`).

For detailed setup guides and walkthroughs, see [Getting Started](docs/getting_started.md), [Harnesses](docs/harnesses.md), and [Framework Architecture](docs/designs/architecture.md).

## Skills

| Skill | Command | Description |
| :---- | :------ | :---------- |
| **Brainstorm** | `/egm-brainstorm` | Zero-doc ideation tool using a multi-lens Goldfish shootdown swarm to stress-test early concepts. |
| **Draft** | `/egm-draft` | Iterative, section-by-section markdown design specification compiler. |
| **Review** | `/egm-review` | Multi-stage verification pipeline orchestrator (Zoom Out -> Comprehension -> Critic -> Readiness). |
| **Review Loop** | `/egm-review-loop` | Concurrent review subagent dispatch engine supporting direct and hierarchical dispatch. |
| **Review Resolve** | `/egm-resolve` | Interactive triage and automated patch application engine for review findings. |
| **Drift Report** | `/egm-drift-report` | Sequential AST scanner detecting divergence between checked-in specs and live code. |
| **Bootstrap** | `/egm-bootstrap` | Recursive bottom-up codebase documentation generator and sentinel-block upserting engine. |

## Philosophy

EGM uses two animal metaphors to structure AI agents across the software development lifecycle:

* 🐘 **The Elephant (Remembers Everything)**: Deep-context agents load system history, architecture diagrams, component boundaries, and user journeys. The Elephant runs structured brainstorming, probes operational limits, and drafts comprehensive specifications.
* 🐠 **The Goldfish (Zero-Context Memory)**: Stateless, isolated subagents read only the draft spec and live source code, without conversational bias. The Goldfish swarm stress-tests designs from conflicting perspectives. Personas in `agents/` include Design Critic, Naive Reader, Tech Lead, Codebase Auditor, Structural Validator, Style Editor, and Zoom Out Architect.
* 🧑‍💻 **The Human (Owns the Outcomes)**: AI is an exploration partner and automated auditor, while human engineers own architectural decisions, trade-offs, and final outcomes.

For the foundational essay introducing this methodology, see Dave Rensin's article: [Elephants, Goldfish, and the New Golden Age of Software Engineering](https://medium.com/@drensin/elephants-goldfish-and-the-new-golden-age-of-software-engineering-c33641a48874).

## Contributing

We welcome community contributions! Please review [Harnesses](docs/harnesses.md) and our [Contribution Guidelines](CONTRIBUTING.md) before submitting pull requests.

## License

Apache 2.0 License applies to this project - see the [LICENSE](LICENSE) file for details.

This is not an officially supported Google product.
