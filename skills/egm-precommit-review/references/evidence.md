# Pending-change evidence protocol

The parent collects evidence using local Git and file tools. This is a protocol,
not an atomic snapshot implementation. If the host cannot collect and compare
complete evidence, report incomplete instead of improvising a clean verdict.

1. Work from the resolved repository root. Use `GIT_OPTIONAL_LOCKS=0` for Git
   reads. Resolve HEAD and, if provided, BaseRef to commit OIDs using
   `git rev-parse --verify --end-of-options <ref>^{commit}`. Use
   `git merge-base --all <base-oid> <head-oid>` and require exactly one result.
   Pin that merge base for the run. With no BaseRef, branch.patch is empty.
   Create `round-N/scope.md` with a capture-in-progress note before saving
   any patch, file copy or raw Git capture for the round. This file marks
   the directory as generated even if capture is interrupted. If the note
   cannot be saved, report incomplete and stop before writing evidence.
2. Capture `git status --porcelain=v1 -z --untracked-files=all`,
   `git ls-files --stage -z`, and `git ls-files --others --exclude-standard -z`.
   Parse NUL records, including both paths of a rename, without whitespace
   splitting. Nonzero index stages mean conflicts: stop. Include deletions,
   renames, mode changes, intent-to-add entries, and every non-ignored untracked
   file outside the following artifact exclusions. Inspect only direct child
   directories named `egm-precommit-*` under the configured artifact directory.
   Exclude untracked descendants of this run and prior runs identified by their
   generated layout: a `round-N/scope.md` (even if capture is unfinished) or
   both `precommit_report.md` and `ledger.md`. Check path components and file
   types without following symlinks or reading prior report contents. Apply
   exclusions at directory boundaries.
   Keep all tracked changes and every other untracked file, including directories
   that share the prefix but lack the generated layout. Apply no extension filter.
3. Save three distinct diffs with `--binary --full-index --no-ext-diff
   --no-textconv --no-renames` and `--` before paths: branch (pinned merge base
   to HEAD, or empty), staged (`--cached` against HEAD), and unstaged. Do not
   collapse index and worktree differences with `git diff HEAD`: opposing
   changes can cancel. Disable color. Capture stdout directly without terminal
   truncation and record command success separately. Empty successful output
   means no changes in that layer, not missing evidence.
4. For every changed regular text path, and previously affected finding path
   in a verification round even if its diff has disappeared, save copies of the
   existing HEAD, index and working-copy versions, and the pinned base version
   for branch changes. Use numbered filenames in files/, and map each copy to
   its repository path, layer, SHA-256 and original line numbering in scope.md.
   Read Git blobs by OID from NUL-safe tree/index listings, without shell
   interpolation of repository filenames. Preserve source contents exactly.
   Intent-to-add is an empty index entry plus the real working-copy contents.
   For deleted paths, retain available old versions and old-side patch lines.
   Untracked files require their full contents; their names alone are not review.
5. Do not follow symlinks, including ancestor directories. Do not execute
   filters or external diff drivers. Mark binary, non-text, submodule, symlink,
   oversized or unreadable entries as coverage gaps. These prevent clean even
   when text review succeeds. Do not copy secrets identified during collection
   into artifacts or prompts; record the omission as incomplete and tell the
   user. Ignored paths stay excluded; do not recursively scan .git or logs.
6. After saving the round evidence, replace the note in `scope.md` with the
   complete inventory before running checks or dispatching a reviewer. Record
   it as readable text with paths escaped losslessly (for example as JSON
   strings). Include HEAD,
   pinned base, change-layer mapping, excluded run directories and coverage
   gaps. Keep any saved raw NUL-delimited captures in the run directory,
   outside `round-N/`. Do not give them to the reviewer. The reviewer uses
   scope.md for inventory coverage. Omit excluded
   files from the records, patches and snapshots given to the reviewer.
   Include hashes of patches, file copies and each changed working-copy entry's
   current bytes/type, including untracked files. Detect new/deleted paths with
   the inventory. Record index entries as mode/OID/stage, not index-file mtime.
   Recollect these values after capture, before dispatch, and after completion.
   Apply the same artifact exclusion rule on each recollection. An in-scope
   mismatch means stale, not clean. Do not repair or overwrite a stale round.
7. Reviewers may need unchanged surrounding source. They must list extra paths
   actually read. Before declaring clean, verify those context reads still
   match the bytes reviewed, using captured native read output or before/after
   copies and hashes. If this cannot be established, record the context as
   unverified and the review incomplete. Do not claim atomicity: a file can
   change and change back between observations.

Validation evidence uses the same state identity. After completing scope.md,
hash its exact bytes with SHA-256. That file records the HEAD, base, inventory,
and the patch and snapshot hashes. Record this digest and the tested layer in
checks.md alongside each command, source, exit status and result. Keep scope.md
fixed for that round. Compare the captured repository evidence itself when
checking for drift. If it changes after checks, rerun affected checks against
fresh evidence. To test
a distinct staged candidate, materialize its index tree outside the working
copy with ordinary permissions; never modify the real index or hide user files.
If that cannot be done safely, mark staged validation not run. Changes during
testing or review invalidate certification until new evidence and checks exist.
