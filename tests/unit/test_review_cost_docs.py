# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Keep the review cost FAQ in step with the egm-review stage reviewers."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def flat(path: str) -> str:
  return " ".join((ROOT / path).read_text(encoding="utf-8").split())


def uninterrupted_reviewers() -> dict[str, list[str]]:
  """Return the reviewers each stage of the uninterrupted flow starts."""
  flow = flat("skills/egm-review/SKILL.md")
  if "### Subflow: Uninterrupted Full Flow" not in flow:
    return {}
  flow = flow.split("### Subflow: Uninterrupted Full Flow", 1)[1]
  flow = flow.split("**Cross-Stage Synthesis", 1)[0]
  stages = {}
  for step, body in re.findall(
      r"\*\*Step (\d) \([^)]*\)\*\*:(.*?)(?=\*\*Step \d|$)", flow):
    listed = re.search(r"Reviewers: \[([^\]]+)\]", body)
    if listed:
      stages[step] = [name.strip() for name in listed.group(1).split(",")]
    else:
      stages[step] = re.findall(r"`(egm-[a-z-]+)` subagent directly", body)
  return stages


def test_review_cost_counts_match_egm_review() -> None:
  stages = uninterrupted_reviewers()
  assert sorted(stages) == ["5", "6", "7", "8", "9"], (
      "Could not read the Stage 5-9 reviewers from the Uninterrupted Full "
      f"Flow in skills/egm-review/SKILL.md (found {stages}). If the skill "
      "changed, recheck the counts in docs/faq.md and "
      "docs/getting_started.md, then update this parser.")
  assert all(stages.values()), stages
  full = sum(len(names) for names in stages.values())
  loop_stage = len(stages["7"])
  assert len(stages["9"]) == loop_stage, stages

  faq = flat("docs/faq.md")
  assert f"runs each stage once: {full} reviewer subagents" in faq
  assert f"Stages 5 to 8 only: {full - len(stages['9'])} reviewers" in faq
  assert f"the stage's {loop_stage} reviewers again" in faq
  assert f"many more than {full} reviewers" in faq
  guide = flat("docs/getting_started.md")
  assert f"runs at least {full} reviewer subagents" in guide
