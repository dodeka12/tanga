# Workflow: Pull Request

How to open a pull request for a feature/fix branch.

## Overview

1. Run the full test suite, linter, and type checker — all must pass.
2. Create a local backup branch (never published).
3. Squash all commits on the branch into one.
4. Rename the changelog to the squashed commit's hash + update `docs/changelog/index.md`.
5. Write the PR summary to a temp file.
6. Push the branch and create the PR with the `gh` CLI.

## Prerequisites

- The branch is fully committed locally.
- A branch changelog exists at `docs/changelog/YYYY/MM/DD_<branch-name>.md`
  (see `dev/workflows/changelog.md`).

## Steps

### 1. Run the full validation gate

Run the full test suite, the linter, the type checker, and the JS checks, and
require all of them to succeed before doing anything else:

```powershell
uv run pytest -rs
uv run ruff check .
uv run ty check
node --test 'js/dev/tests/*.test.mjs'
node js/dev/tests/check-syntax.mjs
```

- If any check fails, fix it and re-run. Do **not** open the PR with failing
  tests, lint errors, or type errors.
- `uv run ruff check .` carries the ANN (type-hint coverage) rules; `uv run ty
  check` is the correctness gate (unresolved/unsound types, bad calls, bad
  attributes). Both run over the whole repository, including `py/examples`.
- The two `node` commands are the **local** JS gate (Node.js is required — see
  `js/dev/README.md`). They run only on a developer machine, never in GitHub
  Actions. For frontend/layout changes also run the manual browser smoke:
  `node js/dev/tests/reconcile-smoke.mjs` (see `js/dev/README.md`).
- `-rs` prints the reason for every skipped test. **Do not silently ignore
  skipped tests** — confirm each skip is expected. The only expected skips are
  the offline-export tests in `py/tests/viz/test_export_delivery.py` (see the
  note below); investigate anything else before opening the PR.

### Toolchain-dependent tests (offline export)

`py/tests/viz/test_export_delivery.py` gates two tests behind a
`requires_toolchain` marker (`test_snapshot_offline_inlines_everything` and
`test_end_to_end_writes_all_three_modes`). They exercise `delivery="offline"`,
which bundles assets with esbuild, so they **skip** when Node.js/esbuild are not
installed.

- CI intentionally skips these tests (no Node.js/esbuild/Playwright toolchain is
  installed in CI).
- To run them locally, install the dev JS toolchain once (`npm install` in
  `js/dev/`, or `npm install esbuild` to install just esbuild), then re-run the
  suite — the two skips disappear.

### 2. Create a backup branch

Before rewriting history, snapshot the current branch so nothing is lost if the
squash goes wrong:

```powershell
git branch backup/<branch-name>            # e.g. backup/fix-join-meet
```

- Name it `backup/<branch name>`.
- **Do NOT publish it** — leave it local (no `git push`).
- Backup branches are cleaned up manually; this workflow never deletes them.

### 3. Squash the branch to one commit

Collapse every commit on the branch (since it diverged from its base) into a
single commit, keeping the working tree as the final state:

```powershell
git reset --soft (git merge-base HEAD main)   # move HEAD back to the base
git commit -m "<conventional commit message summarising the branch>"
```

- `main` is the default base; substitute the actual base branch if the branch
  was cut from something else.
- The short hash of this squashed commit is what the changelog is named after in
  the next step.

### 4. Rename the changelog (branch name → squashed commit hash)

The branch was just squashed, so `git rev-parse --short HEAD` now returns the
**squashed** commit's hash.  Get it plus today's date (the PR submission date,
which determines the year/month folder and the day in the filename):

```powershell
git rev-parse --short HEAD                 # e.g. 8f05f30 (squashed commit)
Get-Date -Format "yyyy MM dd"              # e.g. 2026 09 19
```

Move the changelog into `docs/changelog/YYYY/MM/` (creating the folder if it
does not exist) and rename it to `DD_<hash>.md`, replacing the branch name with
the squashed commit's hash and the date with the PR submission date. For
example, a branch changelog created as `docs/changelog/2026/08/19_fix-join-meet.md`
and submitted on `2026-09-19` becomes `docs/changelog/2026/09/19_8f05f30.md`.

Also update the `→ [Details](...)` link in `docs/changelog/index.md` to the new
path (e.g. `2026/09/19_8f05f30.md`) and the entry's `— <YYYY-MM-DD>` date
heading to the PR submission date, then **commit the rename as a separate
commit** (do not `--amend` — the changelog is named after the squashed commit,
which is fine even though it is not the branch's final HEAD).

Before committing, re-run `uv run python tools/last-release.py` and make sure
the changelog title (`# Changes since version ...`) and the
`docs/changelog/index.md` heading match its current output — including the
parenthesised release candidate (e.g. `1.16.0 (1.17.0-rc3)`). If another PR
merged while this branch was open, the release candidate may have advanced;
update both the title and the index heading to match.

### 5. Write the PR body to a temp file

Write a short summary of the changes to a temporary file. Using a file keeps
the `gh` invocation stable (no argument-length or quoting problems):

```powershell
$body = Join-Path $env:TEMP ("pr_body_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".md")
@'
## Summary

- Short summary of the changes.
@' | Set-Content -Path $body -Encoding utf8
```

### 6. Push the branch and create the PR

```powershell
git push -u origin <branch-name>
gh pr create --title "<short summary>" --body-file $body
Remove-Item $body
```

- Push only the feature branch; the `backup/<branch-name>` branch stays local
  and is never published.
- `--body-file` reads the PR text from the temp file, which is the most stable
  way to pass multi-line text to `gh`.
