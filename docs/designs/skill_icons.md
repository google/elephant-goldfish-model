# Shared skill icons

Status: Implemented. Canonical artwork is shared by plugins, README, and website.
Author: @n3wth. Date: 2026-10-25.

## Purpose and scope

Use the same eight skill marks in plugin pickers, the README, and egm.dev.
The approved artwork uses familiar silhouettes with two color facets. This
change replaces the existing skill artwork; it does not change skill behavior,
reviewer permissions, installation, or the Elephant-Goldfish logo.

## Source and geometry

Each `skills/egm-*/assets/icon.svg` is the canonical asset. Keep the SVGs
self-contained, with a title and a 24 by 24 viewBox. Visible ink stays inside
the 20 px keyline. Optical size and positioning corrections are part of the
artwork; do not normalize individual bounding boxes or stroke widths.

| Skill | Mark | Base / facet |
| --- | --- | --- |
| Bootstrap | Rounded plus: initialize project documentation | `#1b6ef3` / `#7cacf8` |
| Brainstorm | Lightbulb: explore ideas | `#1b6ef3` / `#7cacf8` |
| Draft | Pencil: write the design | `#1b6ef3` / `#7cacf8` |
| Resolve | Check: address review findings | `#1b6ef3` / `#7cacf8` |
| Drift report | Touching, offset halves: document and code diverge | `#e86e00` / `#ff8d41` |
| Review | Magnifier: inspect the document | `#e86e00` / `#ff8d41` |
| Review loop | Circular arrow: repeat review | `#e86e00` / `#ff8d41` |
| Precommit review | Magnifier: inspect pending changes | `#e86e00` / `#ff8d41` |

## Consumers

- Codex metadata continues to point both icon fields at `./assets/icon.svg`.
  Its `brand_color` matches the icon's base color. Host rendering is controlled
  by the host; metadata validation does not verify its picker UI.
- Both runtime bundles include the canonical files through the existing
  [package builder](../../scripts/pack_plugin.py). Regenerate
  `distributions/claude`; do not edit its copies independently. Claude's
  reviewer color keywords and the plugin-level logo stay unchanged.
- The root README references the canonical paths directly. These relative
  paths also resolve inside generated runtime packages.
- The website's `site/src/components/SkillIcon.astro` imports these SVGs at
  build time and marks them decorative beside adjacent labels.

## Verification and rollout

Check metadata colors and SVG structure, runtime byte equality, and README
image inclusion. Website integration receives its own build and visual checks.
All eight marks must remain legible beside their labels.

The shared artwork and runtime-packaging PR #136 are merged. Artwork and
metadata checks do not establish native-host workflow support.
