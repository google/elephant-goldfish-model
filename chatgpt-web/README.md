# EGM for ChatGPT web package

This folder holds a separate plugin for web chat hosts that have no local
executor, such as ChatGPT on the web. It contains one skill, `egm-in-chat`.
See the [design](../docs/designs/egm_chat.md).

The folder is outside `skills/` on purpose. The published EGM plugin and every
coding harness read `skills/`, so this skill does not appear in them.

The skill helps shape an idea, draft a plan, or review a document from the chat
and the files a user attaches. Its critique is same-context. It does not run
independent Goldfish reviewers, and it needs no shell or repository.

Build the package:

```sh
python scripts/pack_plugin.py --target chatgpt-web --output dist
```

Install `dist/egm-chatgpt-web.zip` as a private plugin in the web host.
