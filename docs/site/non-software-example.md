---
title: Non-software review example
description: A worked /egm-review-loop walkthrough using a campus study space plan.
---

This walkthrough shows how to review a non-software document from start to finish using [Custom review](/skills/egm-review-loop) (`/egm-review-loop`). It uses a short operational plan for a shared student study space and requires no software background.

## 1. Starting plan with seeded defects

Save the initial draft as `study-space-plan.md` (source: [study-space-plan.md](../examples/study-space-plan.md)). This draft intentionally includes four defects: a skipped heading level, promotional and uncalibrated claims, an unspecified booking and tie-breaking process, and undefined roles and artifacts.

```markdown
# Shared Study Space Plan

This plan covers the opening schedule and daily responsibilities for Room 204, a shared student study space seating up to 24 people. This seamless schedule eliminates all booking conflicts and guarantees a quiet, productive environment for everyone.

### Opening Schedule

* **Weekdays**: Open 08:00 to 22:00.
* **Weekends**: Open 10:00 to 18:00.
* **Bookings**: Study groups of 3 to 6 students can reserve the side table for two-hour blocks. Overlapping booking requests are resolved fairly.

### Responsibilities

* **Opening duty**: The morning volunteer unlocks the door 10 minutes before opening, turns on the lights, and puts out the desk binder.
* **During open hours**: Students sign in at the front desk when they arrive. Quiet conversation is allowed at the side table only.
* **Closing duty**: The evening volunteer checks the room at closing time, records any maintenance notes in the desk binder, and locks the door. If an issue cannot wait until the next day, notify the floor coordinator.
```

## 2. Review command and settings

Run `/egm-review-loop` and ask for reviewers that fit a general operational plan:

```text
/egm-review-loop
Review study-space-plan.md.
Help me choose reviewers and standards
for the opening schedule and responsibilities.
```

For this run, the review used three built-in Goldfish reviewers with no software-specific standard file:

| Setting | Value |
| :------ | :---- |
| Target file | `study-space-plan.md` |
| Scope | Full file (lines 1–15) |
| Reviewers | `comprehension`, `structural`, `style` |
| Standards | Built-in persona audit (no custom standard file) |
| Supporting context | None |

## 3. Excerpts from a recorded review

> **Illustrative example**: The excerpts below come from one recorded run in **Antigravity CLI (`agy`) version 1.5.19** on **2026-11-28**. Because fresh-context reviewers sample independently on each run, exact wording and finding counts vary between runs.

### Comprehension reviewer (`comprehension`)

> **What this proposes**: This document proposes an opening schedule and daily operating responsibilities for Room 204, a 24-person shared student study space. It sets weekday (08:00–22:00) and weekend (10:00–18:00) hours, allows groups of 3 to 6 students to reserve a side table in two-hour blocks, and assigns opening, in-hours sign-in/noise, and closing tasks to morning and evening volunteers.
>
> * **Major — `Bookings` (line 9)**: Both the booking mechanism and conflict resolution are unspecified. A naive reader does not know how or where to submit a reservation, how far in advance bookings open, or what "resolved fairly" means operationally.
> * **Major — `Opening duty` & `Closing duty` (lines 13, 15)**: Assumed workflow prerequisites and undefined artifacts. The plan does not explain how volunteers are handed keys to unlock/lock Room 204, nor does it define what the "desk binder" contains or where it is stored when the room is closed.
> * **Major — `Closing duty` (line 15)**: Undefined role and missing escalation procedure. "Floor coordinator" is not defined or linked to contact information, and there are no criteria for what constitutes an issue that "cannot wait until the next day."
> * **Nit — Overview & `During open hours` (lines 3, 14)**: Line 3 guarantees a quiet environment without stating how noise rules are enforced. "Front desk" (line 14) is ambiguous as to whether it is inside Room 204 or at building reception, and Room 204's location is unstated.

### Structural reviewer (`structural`)

> * **Major — `### Opening Schedule` (line 5) and `### Responsibilities` (line 11)**: Heading hierarchy skips level 2 (`H2`), jumping directly from `# Shared Study Space Plan` (`H1`, line 1) to `###` (`H3`). Main sections under an `H1` must use `##` (`H2`) to maintain sequential heading nesting.

### Style reviewer (`style`)

> * **Major — Intro paragraph (line 3)**: Hyperbole, marketing fluff, and uncalibrated absolute claims ("seamless", "eliminates all booking conflicts", "guarantees a quiet, productive environment for everyone"). Action: `DROP` the promotional sentence or `CALIBRATE` to state only the factual mechanism.
> * **Major — `### Opening Schedule` (line 9)**: "Overlapping booking requests are resolved fairly" is subjective with no verifiable rule. Action: `CALIBRATE` by specifying the concrete resolution rule.

## 4. Corrected plan and defect mapping

After reviewing the findings and deciding which changes to accept, apply the updates to produce the revised plan (source: [study-space-plan-revised.md](../examples/study-space-plan-revised.md)):

```markdown
# Shared Study Space Plan

This plan covers the opening schedule, booking rules, and daily responsibilities for Room 204 (second floor, Library Annex), a shared student study space seating up to 24 people.

## Opening Schedule

* **Weekdays**: Open 08:00 to 22:00.
* **Weekends**: Open 10:00 to 18:00.
* **Bookings**: Study groups of 3 to 6 students can reserve the side table for two-hour blocks up to 7 days in advance using the booking sheet in the desk binder inside Room 204. Requests are granted first-come, first-served by sign-up timestamp, and each group may hold at most one block per day.

## Responsibilities

* **Opening duty**: The scheduled morning volunteer collects the Room 204 key from the ground-floor reception lockbox, unlocks the door 10 minutes before opening, turns on the lights, and places the desk binder (containing the sign-in sheet, booking sheet, and maintenance log) on the entry desk inside Room 204.
* **During open hours**: Students sign in at the entry desk inside Room 204 when they arrive. Quiet conversation is allowed at the side table only; if noise disrupts other users, the on-duty volunteer asks the group to lower their voices or move to a ground-floor lounge.
* **Closing duty**: The scheduled evening volunteer checks the room at closing time, records any maintenance notes in the desk binder, locks the binder in the entry-desk drawer, locks the door, and returns the key to the ground-floor reception lockbox. If an urgent issue cannot wait until the next day (such as a broken door lock, water leak, or safety hazard), the volunteer contacts the floor coordinator using the phone number on the inside cover of the desk binder.
```

### How each finding was resolved

| Finding | Seeded defect | Correction in revised plan |
| :------ | :------------ | :------------------------- |
| `structural` (lines 5, 11) | Skipped `H2` heading level (`#` to `###`) | Changed `### Opening Schedule` and `### Responsibilities` to `##` (`H2`). |
| `style` (line 3) | Promotional phrasing and uncalibrated guarantees | Removed the "seamless" sentence and kept only the factual room scope and location. |
| `comprehension` & `style` (line 9) | Unspecified booking process and vague "resolved fairly" rule | Added the sign-up method (desk binder), 7-day window, first-come, first-served rule, and one-block daily limit. |
| `comprehension` (lines 13, 15) | Missing key handoff and undefined "desk binder" contents/storage | Specified the ground-floor reception lockbox for the key and listed the binder's contents and overnight drawer storage. |
| `comprehension` (line 15) | Undefined "floor coordinator" and escalation criteria | Defined urgent issue examples and pointed volunteers to the coordinator's phone number inside the binder cover. |
| `comprehension` (lines 3, 14) | Ambiguous "front desk" and unstated noise enforcement | Clarified "entry desk inside Room 204", added the building/floor location, and stated how volunteers handle noise disruptions. |
