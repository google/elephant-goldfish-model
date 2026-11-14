# Layouts

## Overview
Shared Astro layout for the EGM documentation website, composing gBreeze stylesheets, Starlight theme primitives, and site components.

## Interface
- [site/src/layouts/Base.astro] Composes fonts, gBreeze stylesheets, site styles, canonical and social metadata, favicons, theme colors, `ThemeProvider`, `Analytics`, and the page slot.

## Invariants
- [site/src/layouts/Base.astro] Loads the gBreeze token stylesheet before component stylesheets and site styles.
- [site/src/layouts/Base.astro] Emits canonical, Open Graph, and Twitter metadata from the page title, description, and canonical URL.
- [site/src/layouts/Base.astro] Renders both self-hosted font variants through Astro's `Font` component.

## Side Effects
- [site/src/layouts/Base.astro] Renders `Analytics.astro`, which can load the Cookie Notification Bar on canonical `egm.dev` and Google Analytics only after affirmative consent.
- No direct storage writes or network requests are performed by the layout itself.

## Verification
- Run: `npm run check` from `site/`.
