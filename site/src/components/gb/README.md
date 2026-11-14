# gBreeze Components

## Overview
gBreeze (`@material/web` labs) application control components in their native-element form for the EGM documentation website.

## Interface
- [site/src/components/gb/Button.astro] Renders the gBreeze button with color, size, href, target, popover, ARIA, data, and label props, using an `<a>` when `href` is set.
- [site/src/components/gb/IconButton.astro] Renders the gBreeze icon button with label, color, size, href, target, popover, ARIA, and data props.
- [site/src/components/gb/Symbol.astro] Renders a Material Symbols glyph by name from the local SVG collection.

## Invariants
- [site/src/components/gb/Button.astro] Emits the gBreeze class names (`btn`, `ripple`, `focus-ring-outer`, `btn-<color>`, `btn-<size>`) in native-element form.
- [site/src/components/gb/IconButton.astro] Emits the gBreeze class names (`icon-btn`, `ripple`, `focus-ring-outer`, `icon-btn-<color>`, `icon-btn-<size>`) in native-element form.
- [site/src/components/gb/Symbol.astro] Throws when the requested glyph is not present in `src/assets/symbols/`.
- [site/src/components/gb/Symbol.astro] Strips the source SVG wrapper, rewrites fills to `currentColor`, and preserves the source `viewBox`.

## Side Effects
- None verified.

## Verification
- Run: `npm run check` from `site/`.
