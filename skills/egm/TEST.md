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

Check `/egm draft` and `/egm review` action arguments, including `review`
while Lite is active and an explicit specialist that overrides active state.
Compare newcomer, experienced, unknown-familiarity, and explicit detail-request
cases. Guidance must change while the selected workflow's gates stay intact.
Check that relevant workspace artifacts inform routing without scanning
unrelated files or inventing a saved familiarity profile. Verify the `/egm`
picker label and documented host spelling in each claimed native host.
