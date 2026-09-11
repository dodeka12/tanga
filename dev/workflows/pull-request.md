# Workflow: Pull Request

How to open a pull request for a feature/fix branch.

## Overview

1. Run the full test suite — it must pass.
2. Rename the branch changelog to its final hash-based name.
3. Write the PR summary to a temp file.
4. Push the branch and create the PR with the `gh` CLI.

## Prerequisites

- The branch is fully committed locally.
- A branch changelog exists at `docs/changelog/YYYY/MM/DD_<branch-name>.md`
  (see `dev/workflows/changelog.md`).

## Steps

### 1. Run the full test suite

Run the full pytest suite and require it to succeed before doing anything else:

```powershell
uv run pytest -rs
```

- If any test fails, fix it and re-run. Do **not** open the PR with failing
  tests.
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
  `dev/`, or `npm install esbuild` to install just esbuild), then re-run the
  suite — the two skips disappear.

### 2. Rename the changelog (branch name → last commit hash)

Get the short hash of the branch's current last commit and today's date (the PR
submission date, which determines the year/month folder and the day in the
filename):

```powershell
git rev-parse --short HEAD                 # e.g. 8f05f30
Get-Date -Format "yyyy MM dd"              # e.g. 2026 09 19
```

Move the changelog into `docs/changelog/YYYY/MM/` (creating the folder if it
does not exist) and rename it to `DD_<hash>.md`, replacing the branch name with
the hash and the date with the PR submission date. For example, a branch
changelog created as `docs/changelog/2026/08/19_fix-join-meet.md` and submitted
on `2026-09-19` becomes `docs/changelog/2026/09/19_8f05f30.md`.

Also update the `→ [Details](...)` link in `docs/changelog/index.md` to the new
path (e.g. `2026/09/19_8f05f30.md`) and the entry's `— <YYYY-MM-DD>` date
heading to the PR submission date, then commit the rename.

Before committing, re-run `uv run python tools/last-release.py` and make sure
the changelog title (`# Changes since version ...`) and the
`docs/changelog/index.md` heading match its current output — including the
parenthesised release candidate (e.g. `1.16.0 (1.17.0-rc3)`). If another PR
merged while this branch was open, the release candidate may have advanced;
update both the title and the index heading to match.

### 3. Write the PR body to a temp file

Write a short summary of the changes to a temporary file. Using a file keeps
the `gh` invocation stable (no argument-length or quoting problems):

```powershell
$body = Join-Path $env:TEMP ("pr_body_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".md")
@'
## Summary

- Short summary of the changes.
@' | Set-Content -Path $body -Encoding utf8
```

### 4. Push the branch and create the PR

```powershell
git push -u origin <branch-name>
gh pr create --title "<short summary>" --body-file $body
Remove-Item $body
```

`--body-file` reads the PR text from the temp file, which is the most stable
way to pass multi-line text to `gh`.
