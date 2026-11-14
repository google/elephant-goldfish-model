# Docs

## Overview
Documentation-site layout components that wrap Starlight primitives for headers, sidebars, pages, actions, pagination, search, and theming.

## Interface
- [site/src/components/docs/Head.astro] Documentation page head wrapper adding analytics, fonts, a Markdown alternate link, and an `llms.txt` described-by link.
- [site/src/components/docs/Header.astro] Documentation header composing site navigation and compact search.
- [site/src/components/docs/MobileMenuToggle.astro] Mobile documentation menu toggle for the Starlight sidebar.
- [site/src/components/docs/PageActions.astro] Copy-page actions with `bar`, `rail`, and `standalone` placements, a live status message, and a Markdown fallback link.
- [site/src/components/docs/PageFrame.astro] Documentation page frame composing header, sidebar, main content, footer, and mobile-menu handling.
- [site/src/components/docs/PageSidebar.astro] Page table of contents and the copy-page rail.
- [site/src/components/docs/PageTitle.astro] Documentation title with an optional skill icon, description, command, and standalone actions.
- [site/src/components/docs/Pagination.astro] Previous and next page links.
- [site/src/components/docs/Search.astro] Search trigger that forwards to the Starlight search dialog and restores focus when it closes.
- [site/src/components/docs/Sidebar.astro] Documentation sidebar sections and mobile footer.
- [site/src/components/docs/ThemeSelect.astro] Light, dark, and system theme picker backed by `egm-theme-picker`, `localStorage`, and system theme changes.

## Invariants
- [site/src/components/docs/Head.astro] Adds the Markdown alternate link only when the route entry identifier is not `404`.
- [site/src/components/docs/PageActions.astro] Requires `placement` and renders actions only for entries other than `404`.
- [site/src/components/docs/PageTitle.astro] Derives skill icons only from `skills/<name>` entries and maps hyphens to underscores.
- [site/src/components/docs/Sidebar.astro] Renders link entries and section groups from `Astro.locals.starlightRoute.sidebar`.
- [site/src/components/docs/ThemeSelect.astro] Falls back to the `auto` theme when `localStorage` is unavailable and listens for system theme changes.
- [site/src/components/docs/MobileMenuToggle.astro] Displays only below the `50rem` breakpoint.

## Side Effects
- [site/src/components/docs/PageActions.astro] Fetches the Markdown export, writes clipboard contents, updates a live status message, and reveals the fallback link when copying fails.
- [site/src/components/docs/ThemeSelect.astro] Writes the selected theme to `localStorage` under `starlight-theme`, storing an empty string for `auto`.
- [site/src/components/docs/PageFrame.astro] Toggles the footer's `inert` attribute while the mobile sidebar popover is open.
- [site/src/components/docs/Search.astro] Installs DOM listeners that forward the custom search trigger to the Starlight dialog and restore trigger focus on close.

## Verification
- Run: `npm run check` from `site/`.
