# Phase 5 — Pre-commit hook + PR checklist (local only)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Run the node-only JS **unit tests** (`node --test`) and **syntax check** in
pre-commit, and document them in the PR checklist — both local. **GitHub
Actions are left untouched** (no JS/esbuild/playwright there).

## Files

- Edit: `.pre-commit-config.yaml`
- Edit: `dev/workflows/pull-request.md`

## Steps

- [x] **5.1 — Add a `js-test` hook (`.pre-commit-config.yaml`)**
  - In the `local` repo, next to `ty` / `viewer-bundle`, add:
    ```yaml
    - id: js-test
      name: run frontend JS unit tests
      entry: node --test 'js/dev/tests/*.test.mjs'
      language: system
      pass_filenames: false
      files: ^(py/pytanga/viz/templates/.*\.js|js/dev/.*\.(mjs|js))$
    ```
  - (On Windows the `bash` shell may be unavailable; if so, split into two hooks
    — `js-unit` (`node --test js/dev/tests/*.test.mjs`) and `js-syntax`
    (`node js/dev/tests/check-syntax.mjs`) — both `language: system`,
    `pass_filenames: false`.)
  - `node` must be on the developer's PATH (documented in `js/dev/README.md`).

- [x] **5.2 — Update `dev/workflows/pull-request.md`**
  - Add to the "Run the full validation gate" step:
    `node --test js/dev/tests/*.test.mjs` and
    `node js/dev/tests/check-syntax.mjs` (and note the manual Playwright smoke
    `node js/dev/tests/reconcile-smoke.mjs` for layout/frontend changes).
  - Update the "Toolchain-dependent tests" note: `npm install` in `js/dev/`
    (instead of `dev/`).

- [x] **5.3 — Confirm GitHub Actions are unchanged**
  - Do **not** add a JS/esbuild/playwright job to `.github/workflows/*.yml`.
  - `ci.yml` continues to run pytest + `build-viewer-js.py --check` + ruff + ty
    only (all Python, no node).

## Validation

```
uv run pre-commit run js-test --all-files          # node clone only
git diff --stat .github/workflows                  # must be empty
```

## Notes

- The `viewer-bundle` pre-commit hook (`uv run python tools/build-viewer-js.py`)
  is Python-only and already correct; do not change it.
- pre-commit is a developer-machine gate, not CI — the "no JS in GitHub Actions"
  constraint applies only to `.github/workflows/`.

