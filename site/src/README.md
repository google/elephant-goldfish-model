# Source

## Overview
Source tree for the EGM documentation website: content configuration, shared libraries, components, layouts, and pages. The tree also contains `assets/` (fonts and symbol SVGs) and `styles/` (site CSS), which are build-time inputs but not code contracts.

## Subdirectories & Boundaries
- [components](components/README.md): Shared Astro UI components.
- [layouts](layouts/README.md): Shared page layout.
- [lib](lib/README.md): Shared library modules.
- [pages](pages/README.md): Site route pages.

## Interface
- [site/src/content.config.ts:collections] Loads the `docs/site/**/*.md` documentation collection.

## Invariants
- [site/src/content.config.ts:collections] Maps entry IDs by stripping the `docs/site/` prefix and the `.md` suffix.

## Side Effects
- None verified.

## Verification
- Run: `npm run check` from `site/`.
