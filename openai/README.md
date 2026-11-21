# OpenAI-specific skill source

`skills/egm-in-chat/` supplies the document workflow for the existing EGM
OpenAI plugin. It has no separate manifest, identity, or release archive.

Build the same package for ChatGPT web and desktop:

```sh
python3 scripts/pack_plugin.py --target openai --output /tmp/egm-chatgpt
```

The packer puts this skill at `skills/egm-in-chat/` alongside the eight canonical
EGM skills in `egm-openai.zip`, for nine OpenAI skills. The Claude archive and
repository-based coding-harness installs have eight skills.

v0.2.0 includes both `egm-lite` for small repository-backed engineering tasks
and `egm-in-chat` for document work. Engineering Lite checks the tools required
by its active phase; its Goldfish reviews still require isolated subagents.

`egm-in-chat` uses same-context critique. Full workflows check the current
chat's tools before starting; independent review requires verified isolated
subagents. See the [design](../docs/designs/egm_chat.md) and
[testing instructions](../docs/codex.md#test-a-local-package).
