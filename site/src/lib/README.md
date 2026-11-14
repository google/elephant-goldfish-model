# Lib

## Overview
Shared library modules for the EGM documentation website: GitHub star counting and repository-relative Markdown link resolution.

## Interface
- [site/src/lib/github-stars.ts:githubStars] Fetches the GitHub star count for the canonical repository with a five-second timeout and an optional `GITHUB_TOKEN`.
- [site/src/lib/repository-markdown.mjs:repositoryLink] Resolves repository-relative Markdown links to absolute GitHub URLs, including raw image and tree directory variants.
- [site/src/lib/repository-markdown.mjs:transformRepositoryMarkdown] Rewrites repository-relative links for Astro content and removes the first H1 from `SKILL.md` files.
- [site/src/lib/repository-markdown.mjs:remarkRepositoryLinks] Returns the remark plugin that applies repository link rewriting to Markdown trees.

## Invariants
- [site/src/lib/github-stars.ts:githubStars] Returns `null` when GitHub is unavailable or the count is invalid.
- [site/src/lib/repository-markdown.mjs:repositoryLink] Throws when a relative reference escapes the repository root or resolves outside the canonical GitHub repository.
- [site/src/lib/repository-markdown.mjs:repositoryLink] Leaves external URLs, root-relative paths, fragments, and bracketed template paths unchanged.
- [site/src/lib/repository-markdown.mjs:repositoryLink] Preserves query strings and fragments and switches directory links from `/blob/` to `/tree/`.
- [site/src/lib/repository-markdown.mjs:transformRepositoryMarkdown] Removes only the first level-one heading from `SKILL.md` files.

## Side Effects
- [site/src/lib/github-stars.ts:githubStars] Performs one outbound request per build.

## Verification
- Run: `npm run check` from `site/`.
