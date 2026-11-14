# Scripts

## Overview
Site verification and image capture scripts for the EGM documentation website.

## Interface
- [site/scripts/capture.mjs:capture] Serves the built site and drives Chrome to regenerate images.
- [site/scripts/og.html] Social-image template rendered to `public/og.png`.
- [site/scripts/check-docs.mjs] Validates built documentation routes, Markdown exports, repository links, `llms.txt`, `llms-full.txt`, `llms-small.txt`, and Pagefind assets.
- [site/scripts/verify-analytics.mjs:visit] Simulates consent states and intercepts Google requests against built HTML.

## Invariants
- [site/scripts/capture.mjs] Requires a completed `dist/` build because it serves the built output instead of rebuilding it.
- [site/scripts/check-docs.mjs] Requires a completed `dist/` build and fails when routes, Markdown exports, assets, redirects, or required search and LLM files are missing.
- [site/scripts/check-docs.mjs] Exercises `githubStars` response cases and `repositoryLink` transformations before checking the built pages.
- [site/scripts/check-docs.mjs] Requires exactly one level-one heading per page and rejects `<nav>` chrome in Markdown exports.
- [site/scripts/verify-analytics.mjs] Requires the path to a build made without an analytics ID plus the enabled build in `dist/`, and accepts only the home or guide route.

## Side Effects
- [site/scripts/capture.mjs:capture] Reads `scripts/og.html` and `dist/`, then writes `public/og.png` and `screenshots/*.png`.
- [site/scripts/check-docs.mjs] Reads `dist/`, `docs/site/`, and `skills/` without writing files.
- [site/scripts/verify-analytics.mjs] Launches Chrome and prints a JSON report covering pending, rejected, granted, revoked, regranted, repeated-callback, script-failure, missing-ID, and noncanonical-host cases; it intercepts vendor requests and sends no telemetry.

## Verification
- Run: `npm run check:docs` from `site/` after `npm run build`.
- Run: `npm run test:browser -- <disabled-build.html>` from `site/` (requires local Chrome; set `CHROME_PATH` when Chrome is not on `PATH`).
- Run: `npm run capture` from `site/` (requires local Chrome; set `CHROME_PATH` when Chrome is not on `PATH`).
