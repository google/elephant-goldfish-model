---
title: Document a codebase
description: Create or update documentation for existing code.
---

## What it does

The assistant reads a folder of source code and writes a `README.md` in each directory. Each file describes what the code in that directory provides, the rules it keeps, and its side effects. A parent directory summarizes the directories below it.

## When to use it

Use Document a codebase before design work on existing software. The assistant and the reviewers then start from a written description of the code.

## What you get

New or updated `README.md` files. To keep your current files unchanged, ask for a different file name, such as `EGM.md`.

## Example

```text
/egm-bootstrap src/
```

## Full instructions

The assistant follows the [Document a codebase skill instructions](../../../skills/egm-bootstrap/SKILL.md) in the repository.
