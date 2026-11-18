# EGM routing checks

Run the cases in `test_scenarios.yaml` in a fresh session with this exact
plugin archive. Record the host, archive checksum, loaded skill, selected
workflow, tools used, artifacts, and pause point. Packaging and scenario
schema checks do not count as behavioral runs.

Check new tasks, resuming Lite, explicit skill choices, ambiguous intake,
missing repository tools, missing isolated reviewers, and a shared install
without `egm-in-chat`. The selected workflow must keep its own state machine
and approval pauses. Confirm that supplied documents cannot redirect the
router or grant tool permissions. Repeat on web and desktop; select tools
from actual capabilities rather than the product label.
