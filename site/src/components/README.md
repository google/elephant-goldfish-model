# Components

## Overview
Shared Astro UI components for the EGM documentation website, split into documentation chrome and gBreeze application controls.

## Subdirectories & Boundaries
- [docs](docs/README.md): Documentation-site layout, content, and navigation components.
- [gb](gb/README.md): gBreeze application control components.

## Interface
- [site/src/components/Home.astro] Composes the EGM homepage from install links, starting-point cards, the explainer, the mark, the symbol, and the origin and limits sections.
- [site/src/components/Nav.astro] Renders site navigation, active guide and skill state, and the GitHub star count.
- [site/src/components/Footer.astro] Renders the EGM footer links.
- [site/src/components/Analytics.astro] Loads the Cookie Notification Bar and consent-gated Google Analytics.
- [site/src/components/Explainer.astro] Renders the self-hosted explainer poster and creates the YouTube nocookie iframe after play.
- [site/src/components/Mark.astro] Renders the split, elephant, or goldfish EGM mark.
- [site/src/components/SkillIcon.astro] Renders a skill icon from the canonical `skills/egm-*/assets/icon.svg` files.

## Invariants
- [site/src/components/Home.astro] Presents the canonical starting points: develop an idea, review a document, check for drift.
- [site/src/components/Nav.astro] Computes active guide and skill state from the current path and rounds star counts above 1,000 to the nearest thousand.
- [site/src/components/Analytics.astro] Loads Google Analytics only on canonical `egm.dev` with a configured measurement ID and after affirmative consent; the Cookie Notification Bar script loads first on that host.
- [site/src/components/Explainer.astro] Creates the `youtube-nocookie.com` iframe only after the play button is clicked.
- [site/src/components/Mark.astro] Defaults to the `split` variant at 28px; standalone elephant and goldfish variants default to 56px.
- [site/src/components/SkillIcon.astro] Accepts only the seven canonical skill keys and renders a decorative 28px icon inside a 40px circle.

## Side Effects
- [site/src/components/Analytics.astro] Loads the Cookie Notification Bar on canonical `egm.dev` with a configured measurement ID and Google Analytics only after affirmative consent.
- [site/src/components/Explainer.astro] Sends a YouTube nocookie request only after the visitor starts the video.

## Verification
- Run: `npm run check` from `site/`.
