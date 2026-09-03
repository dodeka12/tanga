# Workflow: Pull Request

How to open a pull request for a feature/fix branch.

## Overview

1. Run the full test suite — it must pass.
2. Rename the branch changelog to its final hash-based name.
3. Write the PR summary to a temp file.
4. Push the branch and create the PR with the `gh` CLI.

## Prerequisites

- The branch is fully committed locally.
- A branch changelog exists at `docs/changelog/YYYY-MM-DD_<branch-name>.md`
  (see `dev/workflows/changelog.md`).

## Steps

### 1. Run the full test suite

Run the full pytest suite and require it to succeed before doing anything else:

```powershell
uv run pytest
```

If any test fails, fix it and re-run. Do **not** open the PR with failing tests.

### 2. Rename the changelog (branch name → last commit hash)

Get the short hash of the branch's current last commit:

```powershell
git rev-parse --short HEAD   # e.g. 8f05f30
```

Rename the changelog by replacing the branch name with that hash, e.g.
`docs/changelog/2026-08-19_fix-join-meet.md` →
`docs/changelog/2026-08-19_8f05f30.md`.

Also update the `→ [Details](...)` link in `docs/changelog/index.md` to the new
filename, then commit the rename.

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
