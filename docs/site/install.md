---
title: Install EGM
description: Choose your AI application and install the plugin.
---

## ChatGPT and Codex desktop

Open the [EGM plugin page](https://chatgpt.com/plugins/plugins_6aeb90f47ec88191a3c107e01d3eb357) in ChatGPT or Codex desktop. Select **Install**. This listing is desktop only.

## Claude Cowork

Open the plugin panel and add this marketplace:

```text
google/elephant-goldfish-model
```

## Command line

Run the commands for your application.

### Claude Code

```sh
claude plugin marketplace add google/elephant-goldfish-model
claude plugin install egm@egm
```

### Codex CLI

```sh
codex plugin marketplace add google/elephant-goldfish-model
codex plugin add egm@egm
```

### Antigravity

```sh
agy plugin install https://github.com/google/elephant-goldfish-model
```

## Before your first review

Install the whole plugin, not just the skills. Reviews need separate AI reviewers with fresh conversation contexts.

Cloud review support has limits. See [application support](https://github.com/google/elephant-goldfish-model/blob/main/docs/harnesses.md#support-status--contributing-other-harnesses) for details.

## Next step

Follow [Getting started](/getting-started) to develop an idea or review a document.

Need help? Check the [installation guide](https://github.com/google/elephant-goldfish-model/blob/main/docs/harnesses.md#install) or [report an issue](https://github.com/google/elephant-goldfish-model/issues).
