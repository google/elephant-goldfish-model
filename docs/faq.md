# FAQ

#### Q: Are there alternatives?

**A**: Yes. Many.

EGM is one of the ways teams are making LLMs work better. It is not *the* way.
There are others with different trade-offs. Regardless of the tool you choose,
please remember: *You own the outcomes.*

#### Q: What concrete artifacts does the EGM process produce?

**A**: EGM produces three core deliverables:

*   **Design Document**: A peer-reviewed technical specification that captures
    intent, system invariants, and strategic direction.
*   **Implementation checklist**: Identifies the files to create or modify,
    the planned changes, and how to verify them.
*   **Enriched Context Loops**: Colocated Markdown documentation (such as README
    hierarchies) that provides high-quality context for future development
    loops.

#### Q: Will SWEs become obsolete under EGM?

**A**: In our opinion? No. However, code generation will be increasingly
delegated to automated agents, shifting human engineering focus toward governing
intent and reviewing architectural decisions captured in design documents.

#### Q: Will the increased volume of design documentation create a human review bottleneck?

**A**: It can. Reviewing designs adds work, and excessive documentation can
become a bottleneck. The aim is to catch important problems before implementation;
whether that saves time depends on the change and the quality of the review.

We recommend putting an emphasis on prioritization, at least for now. Use EGM
for "What's important now?", instead of everything, to avoid overloading your
reviewing and release pipelines.

#### Q: Does this workflow degrade developer velocity?

**A**: It depends. Design and review take time and may not pay off for a small,
well-understood change. For uncertain or consequential changes, they may reduce
rework by exposing missing decisions earlier.

Compare total time, useful findings, and rework on your own tasks. Completing
the EGM workflow alone does not demonstrate a productivity improvement.

#### Q: What does a review cost, and how long does it take?

**A**: It depends on how many reviewers run, how many stages run, and how long
the design is. Each reviewer is a fresh subagent that reads the design from the
start, and most also read a document standard.

*   **Reviewers and stages**: A full `/egm-review` runs 10 reviewer subagents
    in five stages, one stage after another. Reviewers in the same stage can run
    in parallel. Hosts that nest reviewers under `egm-synthesizer` also start a
    synthesizer for Stages 5, 7, 8, and 9. The `Feature spec only` preset runs
    Stages 5 to 8 (7 reviewers), and `Implementation plan only` runs Stage 9
    (3 reviewers). `egm-review-loop` repeats the review for up to 5 rounds.
*   **Document size**: Every reviewer reads the design, so a longer design
    costs more in each one.

One measured run: on 2026-10-22, Antigravity CLI 1.4.5 ran brainstorm, draft,
and review on a small test design, a tool that counts nonblank lines, with
approvals given in advance and the review in uninterrupted mode. The session
used the CLI's default model. The whole run took 1,398.7 seconds and reported
309,915 tokens. The five review stages took 17 minutes 56 seconds, from the
first Stage 5 reviewer start to the last Stage 9 reviewer finish. Its review
stages ran 9 reviewers; Stage 5 has since added `egm-inventive-catalyst`. See the
[run report](https://github.com/google/elephant-goldfish-model/pull/103#issuecomment-6350669488).
This is one run, not an average.

These measurements do not exist: the model name and the size of the test
design in that run, whether its token count includes the reviewers' own
sessions, a recorded token count for any other run, and a cost in money.

On a subscription plan, a review can reach the plan's usage limit before it
finishes. On 2026-10-22, a Claude Cowork review (Opus 5.5 Medium) stopped
during Stage 8 for this reason; see the
[harness test record](https://github.com/google/elephant-goldfish-model/blob/main/TESTING.md#harness-test-record).

For a small, well-understood change, skip the review and use your normal
workflow. Save the review for uncertain or consequential designs, as the
answer above explains.

#### Q: Is expecting design documentation to be complete enough for a zero-context agent realistic?

**A**: Sometimes, but not always. EGM's approach captures strategy and an
execution plan, with Goldfish agents improving the quality, but LLMs are still
non-deterministic.

You need to use your judgment the same way you would for coaching a new software
engineer. If it is making a minor mistake, adjust it. If it is wildly off base,
maybe you need to go back to the drawing board and correct your design. This is
part of the process and gets easier the more you use it.

#### Q: Should I open big pull requests?

**A**: No. Generally, the answer for this (and many other questions) is "The
answer is the same as when you built things without AI."
