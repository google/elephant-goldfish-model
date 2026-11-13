# UMich EECS 481 Student Contributions

This directory hosts benchmark contributions and workflow helpers from University of Michigan EECS 481 (Software Engineering) students using the Elephant-Goldfish Model (EGM).

## Contribution Tracks

Students can contribute to the repository through three tracks based on EECS 481 coursework:

1. **Option 1: HW2 Legacy Coverage Expansion (`libpng`, 10 to 50 tests)**: Add a reproducible test expansion submission under `hw2-test-expansion/submissions/` showing how structured Elephant planning improved statement or branch coverage from the 10-test baseline (20% coverage) toward a 50-test suite on `libpng`, including edge cases that one-shot generation missed.
2. **Option 2: HW3 20-PR Goldfish Evaluation Benchmark**: Add a structured pull request assessment under `hw3-pr-assessment/submissions/` evaluating the 20 AI-written pull requests from Homework 3 (including known ground-truth defective pull requests), or propose a targeted refinement to a Goldfish reviewer prompt that catches a defect the baseline reviewer missed.
3. **Option 3: Workflow Helper Checks**: Add a small, deterministic validation script or unit test under `tests/unit/` that automates a check or removes manual copy-pasting from the EGM workflow.

## Directory Layout

```text
contributions/eecs481/
├── README.md
├── schemas/
│   ├── hw2_test_expansion.json
│   └── hw3_pr_assessment.json
├── hw2-test-expansion/
│   └── submissions/
│       └── test_sample_libpng_expansion.json
└── hw3-pr-assessment/
    └── submissions/
        └── test_sample_pr_review.json
```

## Submission Format and Local Validation

Each HW2 or HW3 benchmark entry lives in its own JSON file inside the corresponding `submissions/` directory and must conform to the JSON schemas in `schemas/hw2_test_expansion.json` or `schemas/hw3_pr_assessment.json`.

Run the offline unit test suite before pushing your branch:

```bash
pytest tests/unit/test_eecs481_submissions.py
pytest tests/unit
```

## Pull Request and Google CLA Steps

1. Fork `google/elephant-goldfish-model` on GitHub and create a feature branch for your submission.
2. Sign the [Google Individual Contributor License Agreement (CLA)](https://cla.developers.google.com/) using the email address attached to your Git commits.
3. Add your JSON submission file (or helper test) and run `pytest tests/unit` locally.
4. Open a pull request against `main` using [`.github/PULL_REQUEST_TEMPLATE.md`](../../.github/PULL_REQUEST_TEMPLATE.md), select `Track: Bug Fix / Minor Patch` for single benchmark submissions, and check the Human Accountability Affirmation box after reviewing every line of your diff.

## Class Visits, Office Hours, and Mentorship Raffle

- **Guest Lecture (Tuesday, November 17, 2026, 1:30 PM EST)**: Dave Rensin visits EECS 481 for a live walkthrough and Q&A.
- **Guest Talk and Live Office Hours (Tuesday, December 1, 2026, 1:30 PM to 2:00 PM EST)**: Oliver Newth joins EECS 481 to walk through real-world specification traces, Goldfish fresh-context reviews, and live pull request Q&A.
- **Contributor Mentorship Raffle**: Every EECS 481 student who opens a valid pull request that passes CI enters a random drawing for 1-on-1 Google software engineering career and internship chats (three 30-minute sessions or six 15-minute sessions).
