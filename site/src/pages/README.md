# Pages

## Overview
Site route pages for the EGM documentation website.

## Interface
- [site/src/pages/index.astro] Serves the EGM homepage with JSON-LD website metadata and the shared layout, navigation, homepage, and footer components.
- [site/src/pages/[...slug].md.ts:getStaticPaths] Generates documentation page parameters from the `docs` content collection by using each entry `id` as the slug.
- [site/src/pages/[...slug].md.ts:GET] Returns the Markdown export with an H1 title, description, and transformed body using `text/markdown; charset=utf-8`.

## Invariants
- [site/src/pages/[...slug].md.ts:GET] Rewrites repository-relative links with `transformRepositoryMarkdown` before serializing the page body.
- [site/src/pages/[...slug].md.ts:GET] Emits a Markdown document that starts with the entry title and includes the description when present.
- [site/src/pages/[...slug].md.ts:getStaticPaths] Uses the content entry `id` unchanged as the route slug.

## Side Effects
- None verified.

## Verification
- Run: `npm run check` from `site/`.
