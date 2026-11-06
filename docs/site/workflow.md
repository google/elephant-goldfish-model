---
title: Drafting and review
description: How context, independent review, and human decisions fit together.
---

This page describes the built-in software design workflow. For other documents, use [Custom review](/skills/egm-review-loop) with reviewers and standards that fit the task.

## Develop the idea with context

The Elephant is the drafting assistant. Give it the project background, constraints, existing documents, and unresolved questions.

Use [Brainstorm](/skills/egm-brainstorm) to explore the problem and [Draft](/skills/egm-draft) to develop the document.

## Review without the earlier conversation

Reviews use several AI agents and additional model tokens. Choose a review depth that fits the decision.

The Goldfish reviewers start fresh. They receive the draft and permitted supporting material, including relevant source code for software work. They do not inherit the conversation that led to the design.

Use [Review](/skills/egm-review) to look for omissions, unclear assumptions, and decisions the document has not explained. “Fresh” refers to the reviewers’ conversation context. It does not mean they must work without evidence.

## Resolve the findings

Read the findings, check them against the project, and decide what to change. Use [Resolve findings](/skills/egm-resolve) to work through that discussion.

You approve the plan before acting on it.

## Start where you need to

You can review a document you already have. You do not need to run every command in order.

For software work, [Document a codebase](/skills/egm-bootstrap) can describe an existing project. [Check for drift](/skills/egm-drift-report) can compare documents with code after implementation.
