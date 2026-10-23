<p align="center">
  <a href="https://egm.dev"><img src="docs/assets/readme-header.svg" width="480" height="116" alt="Elephant-Goldfish Model"></a>
</p>

<p align="center">Design with an elephant. Review with a goldfish.</p>

<p align="center">
  <a href="#install">Install</a> &ensp;·&ensp;
  <a href="#try-your-first-design">Quickstart</a> &ensp;·&ensp;
  <a href="docs/getting_started.md">Documentation</a> &ensp;·&ensp;
  <a href="https://egm.dev">Website</a>
</p>

<br>

Thousands of Google engineers use EGM, an open-source plugin, to draft specs with deep-context agents and stress-test them with zero-context subagents before writing code.

The **Elephant** holds your project context and drafts the specification. **Goldfish** reviewers examine the draft and referenced source material without the earlier conversation, helping expose unstated assumptions and blind spots. **You** make the architectural trade-offs and approve the specification before implementation.

Use it when a feature needs design decisions before implementation. For a small, clear bug fix, use your normal coding workflow.

## Install

Choose your coding agent. Install the complete plugin so its skills can read the reviewer prompts and document standards.

### Antigravity

```sh
agy plugin install https://github.com/google/elephant-goldfish-model
```

### Claude Code

```sh
claude plugin marketplace add google/elephant-goldfish-model
claude plugin install egm@egm
```

### Codex

```sh
codex plugin marketplace add google/elephant-goldfish-model
codex plugin add egm@egm
```

Start a new session after installation. For **Claude Cowork** and **ChatGPT Work**, see the [setup and support guide](docs/harnesses.md).

## Try your first design

Open your project in your coding agent and choose a feature that needs design decisions. This example adds webhook delivery: what should happen when a delivery fails, or the same event arrives twice?

Use the commands below in Antigravity. In Claude Code, use the `/egm:` prefix, for example `/egm:egm-brainstorm`. In Codex, select the corresponding EGM skill from the skill picker. Brainstorming and review require a session that can create fresh subagents.

**1. Explore the idea**

```text
/egm-brainstorm Add webhook delivery to this project.
```

Discuss requirements and trade-offs with the agent. Fresh reviewers challenge the proposal, and the agent saves the agreed direction in `concepts_brief.md`.

**2. Draft the specification**

```text
/egm-draft
```

The agent turns the brief into `design_draft.md`, pausing after each section for your feedback in chat.

**3. Review the draft**

Use the draft path returned by the agent, for example:

```text
/egm-review design_draft.md
```

Fresh reviewers check the design, its clarity, its fit with the code, and its implementation plan. Choose which findings to address. When you approve the design, ask your coding agent to implement it.

See the [workflow guide](docs/getting_started.md) for the full process, including saving approved specifications under `docs/designs/`.

## How it works

<table>
  <thead><tr><th align="left">Role</th><th align="left">Context</th><th align="left">Responsibility</th></tr></thead>
  <tbody>
    <tr valign="top"><td><strong>Elephant</strong></td><td>Your project, requirements, and earlier decisions</td><td>Explore the problem and draft the specification.</td></tr>
    <tr valign="top"><td><strong>Goldfish</strong></td><td>The document and its referenced source material, without the earlier conversation</td><td>Find missing assumptions, unclear requirements, and implementation risks.</td></tr>
    <tr valign="top"><td><strong>You</strong></td><td>The goals and constraints that matter</td><td>Resolve trade-offs, approve the design, and decide what to build.</td></tr>
  </tbody>
</table>

Goldfish reviews require fresh subagent contexts. If your agent cannot create them, EGM stops the review. A review does not replace tests or human judgment. See [supported environments and verification limits](docs/harnesses.md#support-status--contributing-other-harnesses).

## Choose a skill

You can use each skill when you need it. You do not have to follow the full sequence.

| Skill | Use it to… |
| :--- | :--- |
| [`egm-brainstorm`](skills/egm_brainstorm/SKILL.md) | Test an idea and write a concept brief. |
| [`egm-draft`](skills/egm_draft/SKILL.md) | Turn a brief or existing notes into a design document. |
| [`egm-review`](skills/egm_review/SKILL.md) | Review a design with fresh agents across five stages. |
| [`egm-resolve`](skills/egm_resolve/SKILL.md) | Work through review findings and agree on changes. |
| [`egm-drift-report`](skills/egm_drift_report/SKILL.md) | Compare checked-in documents with the current source code. |
| [`egm-bootstrap`](skills/egm_bootstrap/SKILL.md) | Create or update documentation for an existing codebase. |
| [`egm-review-loop`](skills/egm_review_loop/SKILL.md) | Run a configured group of reviewers for a specific review task. |

## Learn more

- [Getting started](docs/getting_started.md): the workflow and project layout.
- [Setup and support](docs/harnesses.md): installation, agent capabilities, and known limits.
- [Architecture](docs/designs/architecture.md): how the skills and reviewers fit together.
- [Testing](TESTING.md): checks, execution records, and verification limits.
- [Dave Rensin’s original essay](https://medium.com/@drensin/elephants-goldfish-and-the-new-golden-age-of-software-engineering-c33641a48874): the ideas behind EGM.

## Contribute

Read the [contribution guidelines](CONTRIBUTING.md) before opening a pull request. Use [issues](https://github.com/google/elephant-goldfish-model/issues) for bugs and [discussions](https://github.com/google/elephant-goldfish-model/discussions) for questions and ideas.

## License

[Apache 2.0](LICENSE). This is not an officially supported Google product.
