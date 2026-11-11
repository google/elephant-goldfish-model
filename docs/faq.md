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

**A**: Each reviewer is a fresh subagent that reads the design, and most also
read a document standard. The cost grows with these factors:

*   **Reviewers and stages**: A review runs five stages, one after another.
    Reviewers in the same stage can run in parallel. For a design with an
    implementation plan, the `Consolidated report with all review rubrics`
    preset (uninterrupted mode) runs each stage once: 10 reviewer subagents. A
    design with no implementation plan gets Stages 5 to 8 only: 7 reviewers.
    The other presets pause after each stage and run Stages 7 and 9, when they
    include them, through `egm-review-loop`. Each round of that loop starts the
    stage's 3 reviewers again; it asks you before each new round, finishes after
    two clean rounds in a row, and asks again at 5 rounds, where you can choose
    to continue. Stages 5, 6, and 8 can run once more after the design changes,
    and Stages 7 and 9 can run their whole loop once more. An interactive review
    can therefore start many more than 10 reviewers, and the number depends on
    your choices.
*   **Extra subagents**: When a run nests reviewers under `egm-synthesizer`
    (Claude Cowork cannot), each stage or loop round that uses it adds a
    synthesizer, and the synthesizer may start two copies of each reviewer. A
    reviewer that fails is started once more. The counts above are minimums.
*   **Design and context size**: Every reviewer reads the design, so a longer
    design costs more in each one. Reviewers also read the files you pass as
    `GoldfishContext` and the files the design links to inside the working
    directory, and some reviewers search the code.
*   **Your own session**: The main session runs `egm-resolve` after each loop
    round and writes every report. An interactive review also waits for your
    answer at each checkpoint.

One measured run: on 2026-10-22, Antigravity CLI 1.4.5 ran brainstorm, draft,
and review on a test design for a tool that counts nonblank lines. Approvals
were given in advance, and the review ran in uninterrupted mode, one pass per
stage, with reviewers dispatched directly. The session used the CLI's default
model. The whole run, brainstorm and draft included, took 1,398.7 seconds and
reported 309,915 tokens. The five review stages took 17 minutes 56 seconds,
from the first Stage 5 reviewer start to the last Stage 9 reviewer finish. Its
review stages ran 9 reviewers; Stage 5 has since added
`egm-inventive-catalyst`. See the
[run report](https://github.com/google/elephant-goldfish-model/pull/103#issuecomment-6350669488).
This is one run, not an average.

The run report does not record the model name, the size of the test design, or
whether its token count includes the reviewers' own sessions, and it gives no
token count for the review alone. No other recorded run gives a token count,
no run measures an interactive review or `egm-review-loop`, and no record gives
a cost in money.

On a plan with a usage limit, such as a subscription plan, a review can reach
the limit before it finishes. On 2026-10-22, a Claude Cowork run of brainstorm,
draft, and review (Opus 5.5 Medium) reached its usage limit during review
Stage 8; see the
[harness test record](https://github.com/google/elephant-goldfish-model/blob/main/TESTING.md#harness-test-record).

For a small, well-understood change, skip the review and use your normal
workflow. Save the review for uncertain or consequential designs, as the
[answer on developer velocity](#q-does-this-workflow-degrade-developer-velocity)
explains.

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
