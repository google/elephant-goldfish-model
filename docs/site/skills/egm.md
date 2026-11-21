---
title: /egm
description: Start or resume EGM from your task and project context, with guidance that fits your experience.
---

## Start here

Start with `/egm` and describe what you want to do. You do not need to choose
a specialist skill. In a host with a skill picker, select **/egm**. Some hosts
namespace the command as `/egm:egm`.

Describe the task or provide the document, brief, or diff. EGM selects an
existing workflow and starts its next valid phase. It resumes active work
instead of restarting it and keeps each workflow's approval pauses.

EGM uses the conversation, relevant project files, and supplied artifacts to
choose the next step. New users get a brief explanation. Experienced users get
a short route notice. Active work resumes without repeated onboarding. Ask for
more or less detail at any time; approval and review requirements stay the same.

Small engineering changes use Lite. Larger ideas start with Brainstorm;
aligned briefs go to Draft. Existing designs, review findings, codebase
documentation, and drift checks go to their matching skills. When the optional
`egm-in-chat` skill is installed, document-only work can use it with clearly
labelled same-context critique.

EGM checks the tools actually available for the current phase. It names
missing capabilities and never simulates independent reviewers. You can
still choose any specialist skill directly.

## Examples

```text
/egm Here is our design and the review findings. Help me work through them.
/egm draft Use the agreed concepts brief.
/egm review docs/designs/webhooks.md
```

Action arguments also include `brainstorm`, `resolve`, `review-loop`, `lite`,
`bootstrap`, and `drift-report`; `in-chat` requires the optional chat skill.
An active workflow keeps control of its phase triggers: `review` during Lite
resumes Lite's review phase. Name a specialist explicitly to override routing.
Existing `/egm-*` commands remain available as compatibility entry points.

## Full instructions

Read the [EGM routing instructions](../../../skills/egm/SKILL.md).
