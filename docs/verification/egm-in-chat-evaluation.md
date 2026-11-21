# EGM in Chat: recorded prototype evaluation

This preserves the report from [design commit b9a2c26](https://github.com/google/elephant-goldfish-model/blob/b9a2c26efbb4a7032b08e72a2ad1ef071b80beaa/docs/designs/egm_chat.md#evaluation-evidence). It has not been rerun or independently verified here. Prototype instruction labels are separate from plugin release versions.

The original raw cases, harness, and judge outputs are not linked in that report. The proposed [Stage 2 test plan](https://github.com/google/elephant-goldfish-model/blob/fadd7f4c162d302a61bcaf638aec99d7709e35ff/openai/skills/egm-in-chat/TEST.md) and [scenario file](https://github.com/google/elephant-goldfish-model/blob/fadd7f4c162d302a61bcaf638aec99d7709e35ff/openai/skills/egm-in-chat/test_scenarios.yaml) describe candidate checks; they are not the original evaluation corpus or harness. Before #464 merges, supply those sources or commit and run a replacement evaluation of the revised rules.

These results are for prototype instruction set v0.3.0, evaluated before this proposal.

## Method

- Models ran through the OpenAI Agents SDK in a mode where the model must open the skill file, as in the ChatGPT app.
- 77 cases: 27 hand-written (19 for tuning, 8 held out), 30 blind-spot cases, and 20 trips from the TREK planning benchmark (CC BY 4.0, released August 2026, after the models' training data).
- Each version was compared with no skill on the same model and cases.
- Judges were checked against labels before use. The blocker judge reached TPR 0.90 and TNR 1.00 against three-model proxy labels. The invented-fact judge reached TPR 0.73 and TNR 0.92 against human labels from RAGTruth and SummEdits.
- Twelve rounds tested 33 skill versions.

## Held-out results

gpt-5.5, 8 held-out cases and 10 TREK trips, 2 runs each:

| Measure | v0.3.0 | No skill |
|---|---|---|
| Right decision, held-out cases | 100% | 75% |
| Right decision, TREK trips | 100% | 45% |
| Right decision, flawed plans | 100% | 100% |
| Sound plans with no unsupported blocker | 100% | 0-33% |
| Unsupported blockers per reply (TREK) | 0.05 | 1.95 |
| Real problems found | 100% | 100% |
| Words per reply | 476 | 358 |

Claude Haiku 5.5, 8 held-out cases, 3 runs each:

| Measure | v0.3.0 | No skill |
|---|---|---|
| Right decision | 96% | 58% |
| Right decision, flawed plans | 100% | 92% |
| Sound plans with no unsupported blocker | 89% (99% judge-corrected) | 0% |
| Unsupported blockers per reply | 0.25 | 2.5 |
| Real problems found | 100% | 100% |
| Words per reply | 411 | 478 |

The first prototype instruction set (v0.1.0) scored below no skill: 50% right decisions on Haiku 5.5.

## Findings

- On strong models, the skill mainly fixes over-blocking. Without it, models hold most sound plans for reasons the plan does not support.
- The skill does not find more real problems. Strong models already find 97 to 100% unaided.
- No single-reply instruction raised recall on a small model (gemini-3.5-flash-lite). Two independent fresh reviews raised it only from 77% to 82%, because both tend to miss the same flaws. Extra catches need separate fresh-context reviewers, which is full EGM.
- On gemini-3.5-flash-lite, the skill lets some real problems through: right decisions on flawed plans were 77 to 95%, against 100% with no skill. The skill should recommend a strong model and full EGM Review for decisions users depend on.
- Every activated reply disclosed same-context review. None claimed independent review.

## ChatGPT web pilot

A three-case manual pilot ran on 2026-11-10 in ChatGPT Chat and Work on the web, with prototype instruction set v0.1.0 installed as a private plugin.
Replies were masked, shuffled, and scored blind.
The skill tied the plain model on five of six pairs and lost one.
No reply invented facts or claimed independent review.
ChatGPT Work listed all packaged skills; the UI did not show whether the skill file was read.
The current candidate must pass the pilot criteria in the [design](../designs/egm_chat.md#evaluation-evidence) before #464 merges.

## Limits

- Blocker-judge labels come from three models, not people.
- The held-out set is small (8 cases), and the gpt-5.5 check uses 2 runs per case.
- The boundary between a fix and a blocker is a judgment call.
- ChatGPT web runs were not repeated.
