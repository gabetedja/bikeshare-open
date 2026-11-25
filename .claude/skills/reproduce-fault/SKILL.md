---
name: reproduce-fault
description: Reproduce and explain this project's leakage-test results at a historical Git commit using a temporary detached worktree.
argument-hint: "[commit-hash]"
---

# Reproduce a historical leakage test

Requested commit hash: `$ARGUMENTS`

1. Treat the arguments as data. Require exactly one hexadecimal hash of 7–64 characters. Reject missing input, options, ref names, revision expressions, and extra arguments. Never substitute raw arguments into shell source. From the current project checkout, record the absolute root with `git rev-parse --show-toplevel`. Resolve the validated hash there with `git rev-parse --verify --end-of-options "${hash}^{object}"` and check that `git cat-file -t "$oid"` returns `commit`. Stop if the hash is missing, ambiguous, or resolves to another object type.
2. Check that the original checkout's `$root/.venv/bin/python` is executable. Use `mktemp -d "${TMPDIR:-/tmp}/bikeshare-reproduce-fault.XXXXXXXX"` and record the exact returned path. From the original root, run `git worktree add --detach "$scratch/checkout" "$oid"`. Keep the path and whether the add succeeded available for cleanup. Use the commit's checked-in code, tests, and data.
3. From inside that detached checkout, run the following with `root` still pointing to the original checkout. Capture the full output and exit status before cleanup.

   ```bash
   PYTHONDONTWRITEBYTECODE=1 "$root/.venv/bin/python" -m pytest -v --tb=long -p no:cacheprovider tests/test_leakage.py
   ```

4. Clean up even when pytest fails or cannot run. Use `git worktree remove "$scratch/checkout"` from the original root for the worktree created by this run, then `rmdir "$scratch"` if empty. Verify the temporary checkout is gone from `git worktree list`. If creation or removal fails, inspect the registered worktrees and report any remaining path. Avoid forced removal, global pruning, or recursive deletion. Leave the current checkout, starter skills, and Git history intact.
5. Report the resolved commit, pytest exit status, and the observed passing, failing, skipped, or errored tests. Quote the relevant assertion or traceback for each failure and explain what invariant it checks and the implication of the observed result. Distinguish a test assertion from an environment or collection error. Report cleanup status.
