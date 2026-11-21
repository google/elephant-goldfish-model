# Language packs for `egm-bootstrap`

Status: Proposed. Refs #<issue>.
Author: @mitnick2012. Date: 2026-11-12.

## Purpose and scope

`egm-bootstrap` is language-agnostic, but it mixes language rules into its
universal workflow. Step 0 lists one test command per ecosystem. Step 2 holds
a 40-line extension list. Step 4 hardcodes entry points such as
`__init__.py` and a .NET-only verification note. Each new language adds text
to `SKILL.md`, whose body is 23,931 bytes against the 24,000-byte limit in
`tests/unit/test_skill_load_limits.py`. A one-line addition for any further
language would exceed that limit.

The rules that decide what a contract says also stay generic. These rules
cover what counts as public, which files are tests or generated code, and
which calls are side effects. A C# `internal` helper, a Go lower-case
function, and a Rust `pub(crate)` item all look public to a generic scout.

This change makes `SKILL.md` delegate to a router file,
`references/language-router.md`, which loads per-language packs from
`references/`. It follows the pattern used by multi-language review skills: a
central skill, a dispatch table, and one rules file per language.

### Goals

- Keep one `egm-bootstrap` skill. Its workflow, safety gate, grounding rules,
  templates, and worker schema stay as they are.
- Move language rules into `references/lang-<name>.md` packs with a fixed
  section layout.
- Load only the packs that match the repository, plus a generic fallback.
- Give scouts language-specific visibility rules so contracts list only real
  public interface.
- Keep routing in `references/language-router.md` so a new language changes
  no `SKILL.md` bytes. The body drops from 23,931 to about 23,120 bytes.

### Non-Goals

- New skills per language. The plugin ships exactly seven skills and every
  harness adapter registers them; per-language skills would multiply that
  surface for no behavioral gain.
- Changes to the README templates, the worker return schema, or the safety
  gate thresholds.
- Language-specific deterministic analyzers or parsers.
- Bazel rules. Bazel is a cross-language build system and stays in
  `SKILL.md`, where `bootstrap_bazel_target_syntax` tests it.

## Design

### Routing

`SKILL.md` Step 0 reads `references/language-router.md`. The router has four
parts:

- **Routing Table**: every manifest and extension that selects a pack. A unit
  test checks that each table manifest also appears in the pack's Detection
  section.
- **Loading**: always read `lang-generic.md`. Read a pack when Step 0 (root)
  or Step 2 (any subtree) finds its manifest or extension, before that
  directory's children are listed. Workers get absolute pack paths in the
  internal `language_packs` input. Bazel trees keep the SKILL.md Bazel
  verification rules.
- **Scope**: a pack's ignore, test, and generated-file rules apply only under
  its manifest directory. File-level rules match by extension, and
  directory-level rules (Read Order, Verification) use the pack matching most
  of the directory's source files. This prevents, for example, the .NET
  `packages/` rule from hiding a JS workspace.
- **Applying Packs in Step 4**: workers skip ignored, generated, and test
  files. Chunk boundaries start at the decorator or attribute above a
  definition. Each scout's spawn prompt gets the matching pack's Public
  Interface, Signals, and in-file test rules.

Packs add detail only. Execution Constraints, the safety gate, grounding, and
link rules in `SKILL.md` always win. File-based routes (Next.js, Nuxt,
SvelteKit) stay grounded: the scout cites the exported handler and the
framework dependency, never a directory name alone.

### Pack layout

Every pack has these sections, in this order:

| Section | Used by |
| :--- | :--- |
| Detection | Step 0 routing and Step 2 manifest preservation |
| Source Extensions | Step 2 pruning |
| Ignored Paths | Step 2 BFS |
| Test Conventions | Step 2 test-directory exclusion and Step 4 read order |
| Public Interface | Scout prompt |
| Definition Patterns | Step 4 chunking at definition boundaries |
| Read Order | Step 4 contracts-first and entry-point ordering |
| Signals | Scout prompt (invariants and side effects) |
| Verification | Step 4 Verification section |

### Initial packs

`generic`, `dotnet`, `python`, `typescript`, `go`, `rust`, `jvm`, `cpp`.
`lang-generic.md` keeps the full extension list from the current Step 2, so
languages without a pack, such as Ruby, PHP, Swift, and Zig, behave as they
do today.

### Packaging

`scripts/pack_plugin.py` ships `skills/*/references/*.md`, which is a flat
pattern. Packs therefore use flat `lang-*.md` names instead of a
`languages/` subdirectory. No packaging change is needed.

## Alternatives considered

- **One skill per language** (`egm-bootstrap-dotnet` and so on). This would
  duplicate the 400-line workflow per language, break the seven-skill
  packaging assertion, and require harness registration for each skill.
- **Keep growing `SKILL.md`**. This approach is blocked by the body limit.
- **Routing table inside `SKILL.md`**. Each language would add a row of about
  70 bytes, and the scoping rules alone need about 800 bytes more than the
  limit allows.
- **A `languages/` subdirectory**. This needs a packaging glob change and
  gains nothing over flat names.

## Verification and rollout

- `tests/unit/test_bootstrap_language_packs.py` checks that `SKILL.md` links
  the router, that the router table and `references/lang-*.md` files match,
  that table manifests appear in each pack's Detection section, that every
  pack has the nine sections in order, and that the generic pack keeps all
  56 legacy extensions.
- `scripts/pack_plugin.py` requires the router and the generic pack in every
  bundle.
- The `bootstrap_language_pack_routing` scenario checks that a repository
  with `*.slnx` at the root and `package.json` in a subtree routes to the
  .NET, TypeScript, and generic packs only.
- Existing scenarios (`bootstrap_small_tree`, `bootstrap_safety_gate`,
  `bootstrap_code_grounding`, `bootstrap_bazel_target_syntax`) must still
  pass.
- Manual check: bootstrap a polyglot repository and confirm that .NET
  contracts skip `bin/` and `obj/`, omit `internal` members, and use
  `dotnet test` on the nearest test project.

### Adding a language

1. Create `skills/egm-bootstrap/references/lang-<name>.md` with the nine
   sections.
2. Add one row to the Routing Table in `references/language-router.md`.
3. Run `pytest tests/unit/test_bootstrap_language_packs.py`.
