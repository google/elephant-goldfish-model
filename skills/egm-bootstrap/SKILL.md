---
name: egm-bootstrap
license: Apache-2.0
disable-model-invocation: true
description: Bootstrap directory README.md files across a repository subtree.
---

# EGM Peanuts and Hay Bootstrap (`egm-bootstrap`)

When running in Codex or ChatGPT Work, first read [Codex integration](../../docs/codex.md).
In Claude Code or Cowork, read `${CLAUDE_PLUGIN_ROOT}/docs/claude.md` first.

Automates creating, updating, and verifying Elephant-and-Goldfish Model (EGM) `README.md` contracts (`Interface`, `Invariants`, `Side Effects`) across a directory tree: **Peanuts** (leaf package contracts) and **Hay** (parent blueprint indexes).

## Inputs

*   **`path`**: Target root directory to bootstrap (Required).
*   **`is_worker`**: Internal; `true` when running as a Sub-Orchestrator (default: `false`).
*   **`sub_tree_root`**: Internal; subtree partition root path.
*   **`target_filename`**: Contract filename to generate or update (default: `"README.md"`, or e.g. `"EGM.md"` when preserving human-written READMEs).

## Execution Constraints (CRITICAL)

1.  Read and apply [execution instructions](../../resources/execution_instructions.md) (in Claude Code: `${CLAUDE_PLUGIN_ROOT}/resources/execution_instructions.md`; if `<SKILL>` omits a file path, check `~/.gemini/config/plugins/egm/resources/execution_instructions.md`; if file tools are unavailable, proceed inline). If your harness cannot nest subagents, use direct dispatch; if it has no subagent tool, run the scout steps inline.
2.  **Temporary File Isolation**: Each worker keeps its status, checkpoint, and log files in its own directory outside the workspace (host scratch or `mktemp -d`), never a fixed, shared path. If neither exists, skip them.
3.  **Formatting & Parallelism**: Format generated Markdown cleanly (headers, tables, fenced blocks; optional repo formatter like `npx prettier --write` if configured). Spawn sub-orchestrator workers in parallel.
4.  **Mandatory Safety Gate (> 15 Subdirectories)**: If BFS discovery finds more than 15 subdirectories, pause immediately and request user confirmation before continuing or spawning workers.

---

## Workflow

### Step 0: Ecosystem & Verification Discovery

Inspect the repo root manifest to record `VerificationCommand`:
*   Node/TS (`package.json`): `npm test` (or `pnpm test` / `yarn test`)
*   Rust (`Cargo.toml`): `cargo test` | Go (`go.mod`): `go test ./...` | Python (`pyproject.toml`/`pytest.ini`/`setup.py`): `pytest`
*   .NET / C# (`*.sln`/`*.slnx`/`*.csproj`): `dotnet test`
*   Make (`Makefile`): `make test` | Bazel (`BUILD`/`BUILD.bazel`): `bazel test //...` | None: `<test-command>`

### Step 1: Startup Branching

If `is_worker` is `true`, jump to **Step 4** for `sub_tree_root`. Otherwise run **Step 2**.

### Step 2: Incremental Scoping & Safety Gate (Root Orchestrator)

1.  **BFS Discovery**: Map `path` level-by-level via a queue (never recursive `find` or `ls -R`). Keep intermediate folders and build manifests (`package.json`, `Cargo.toml`, `go.mod`, `pyproject.toml`, `*.sln`, `*.csproj`, `Makefile`, `BUILD`). Ignore symlinks, `.git`, `.antigravity`, `node_modules`, `venv`, `dist`, `build`, `third_party`, and patterns in `.gitignore` / `.egmignore`.
2.  **Safety Gate (> 15)**: When running directory count exceeds **15**, stop and ask via single-select gate (`is_multi_select: false`):
    *   `question`: `"The target directory tree contains more than 15 subdirectories. This is a large execution scope. Do you want to proceed with full-tree bootstrapping?"`
    *   `options`: `["Yes, proceed with full tree bootstrapping", "No, abort execution"]`
    Wait for the user; abort immediately if declined.
3.  **Bottom-Up Post-Pruning**:
    *   *Recognized Source / Schema Extensions*: Systems (`.c`, `.cc`, `.cpp`, `.cxx`, `.h`, `.hh`, `.hpp`, `.rs`, `.go`, `.zig`, `.lean`, `.f`, `.f90`, `.f95`, `.f03`, `.f08`, `.hs`), Managed (`.java`, `.kt`, `.scala`, `.cs`, `.razor`, `.cshtml`, `.fs`, `.vb`), Scripting (`.py`, `.rb`, `.php`, `.lua`, `.sh`, `.bash`, `.ps1`, `.psm1`, `.psd1`, `.r`, `.R`, `.ex`, `.exs`), Web/Mobile (`.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`, `.cjs`, `.swift`, `.m`, `.dart`), Schemas/IDLs (`.sql`, `.proto`, `.graphql`, `.gql`, `.thrift`, `.prisma`), Infra (`.tf`, `.hcl`, `.cue`). Exclude manifests, lockfiles, fixtures, docs, and `.csv`/`.tsv`/`.parquet`.
    *   *Exclude Test-Only Dirs*: Skip `tests`, `testing`, `testdata`, or dirs holding only `*_test.*`, `*Test.*`, `test_*.*`, `*.spec.*`.
    *   *Non-Code Filtering*: Drop directories with neither direct code nor code-containing subdirectories; keep empty intermediate folders only when descendants hold code.
4.  Compute pruned directory count and max depth, then run **Step 3**.

### Step 3: Execution Strategy Selection (Root Orchestrator)

1.  **Direct (`<= 5` pruned dirs)**: Run **Step 4** inline on `path`, then **Step 5**.
2.  **Parallel Swarm (`> 5` pruned dirs)**: Verify >15 approval first if applicable. Partition via **Adaptive Depth Partitioning**:
    *   Start at `depth = 1`. Collect nodes at `depth`. If 3-5 nodes, use them as partition roots.
    *   If `< 3`, increment `depth` (max 3) and re-check. If `> 5`, take the 3-4 largest branches separately and combine smaller ones into one fallback subtree.
    *   If `depth == 3` and still `< 3`, pick immediate children of root (or run sequentially).
    *   Spawn parallel workers using `egm-bootstrap-orchestrator` (`agents/bootstrap_orchestrator.md`, or a general-purpose subagent):
        `Prompt`: `"Run egm-bootstrap with path=[path], is_worker=true, sub_tree_root=[partition_root], target_filename=[target_filename]."`
    *   Wait for all worker JSON `subtree_index` payloads, then proceed to **Step 5**.

### Step 4: Sub-Orchestrator Worker Flow

1.  **Scout Setup (`goldfish-explorer`)**: Register (where runtime subagent definition is supported) or prompt a read-only scout (`enable_write_tools: false`, `enable_subagent_tools: false`) with:
    > You are a read-only codebase explorer. Analyze source files in the target directory and return a JSON object matching `{"interface": string[], "invariants": string[], "side_effects": string[]}`. Do not write files. Never infer RPC methods, routes, status enums, or invariants from file or directory names alone; cite exact `[file:symbol_or_flag]` for every entry, and output `["None"]` if no explicit invariants or side effects exist in code.
2.  **Post-Order Traversal (Deepest Leaves First)** across `D`:
    *   **Correction Policy**: If `target_filename` already exists in `D`, read it (never blindly overwrite), scan code via `goldfish-explorer`, extract legacy public symbols/invariants/side effects JSON, merge with code-verified scout output, and edit `target_filename` preserving valid developer notes.
    *   **Scout Reading & Chunking**: No per-directory or per-file byte cap. List top-level definitions with your search tool first, then read every non-test file in full in chunks of ~**1,500 lines** cut at top-level definitions (never mid-body; small files share a chunk), giving each parallel chunk scout the file's imports and top-level definitions to judge visibility, and merge chunk scout JSON outputs. Verify build-manifest deps and `import` / `#include` before attributing RPCs, schemas, or message types locally. Read order: (1) contracts, schemas, build manifests (`.h`, `.hh`, `.hpp`, `.proto`, `.graphql`, `.gql`, `.thrift`, `.prisma`, `.sql` DDL, interfaces; extract exact DDL tables and exported targets); (2) entry points (`main.*`, `index.*`, `lib.*`, `mod.*`, `__init__.py`, dir-named files) then source/query files alphabetically; (3) templates/configs <= 200 lines each (800 in config-only dirs), excluding `.css`/`.scss`; (4) ignore test files (`*_test.*`, `*Test.*`, `test_*.*`, `*.spec.*`) everywhere. On scout timeout/failure, log a warning and use `["(Details pending/documentation failed)"]`.
    *   **Parent Propagation**: Pass merged child `interface` summaries into parent `P`'s scout prompt.
    *   **Verification Commands**: Use `VerificationCommand` or nearest ancestor manifest (.NET: `dotnet test` on the nearest `*.csproj`). For Bazel, always emit valid targets (`//[package_path]/...` or `//[package_path]:all`; NEVER `//[package_path]...`, `//[package_path]:...`, or bare `...`); use `bazel run` for runners.
    *   **Template & Link Policy**: Read [README templates](references/templates.md) before writing. Use **Component Package (Peanuts)** when `D` has direct code (plus child contract links if any) and **Intermediate Blueprint** when `D` has only child contracts. Use relative links (`./child/${target_filename}`, `../sibling/${target_filename}`) **only** for dirs existing in pruned `subtree_index` with real files (link `./child/SKILL.md` for skill dirs or omit uncreated links), and repo/URL links for external cross-package refs. Format cleanly.
3.  **Report or Continue**: Compile `subtree_index` (`path`, `summary`, `interface`, `invariants`, `side_effects`). If `is_worker` is `true`, read [Worker Return Interface Schema](references/worker-return.schema.json), return the matching JSON payload, and stop. Otherwise proceed to **Step 5**.

### Step 5: Root Compilation & Termination (Root Orchestrator)

1.  **Collect Worker Payloads**: Merge `subtree_index` JSON results. On worker timeout/failure, insert `[Subtree Root] (Documentation failed / Subagent execution timeout)` in the root index and continue.
2.  **Intermediate Directories**: Document intermediate folders between `path` and partition roots bottom-up using **Intermediate Blueprint** template and valid relative links.
3.  **Root Contract (`path`)**: Always classify `path` as **Repository Root (Blueprint / Hay)**. Preserve existing top title/metadata/overview via Correction Policy if `target_filename` exists. If `path` has direct source files, scout them into `## Local Interface & Invariants`. Ensure root diagrams reflect only verified sync/async boundaries, operations, and stores from `subtree_index`, then write `target_filename`.
4.  **Final Correctness Verification (CRITICAL)**: Re-read **every** created or modified contract file in `subtree_index` (including all child packages) and verify:
    *   `Interface`, `Invariants`, and `Side Effects` sections cite verified `[file:symbol_or_flag]` entries (or `None`) without unverified claims.
    *   Valid Markdown headers, tables, fences, and Bazel/test targets (`/...` or `:all`, never `:...`).
    *   Every relative link (`./subdir/${target_filename}`, `./subdir/SKILL.md`) points to an existing file on disk.
5.  **Optional Drift Review**: Present a single-select gate (`is_multi_select: false`):
    *   `question`: `"Do you want to run the EGM Drift Report on the generated contract updates to check for consistency with the codebase?"`
    *   `options`: `["(Recommended) Yes, run drift report on modified contracts", "No, skip drift review"]`
    If selected, run [egm-drift-report](../egm-drift-report/SKILL.md) over modified contracts, verifying every documented method, route, enum, database table, and invariant against local source files and recording discrepancies in the drift report for human triage.
6.  Terminate cleanly.
