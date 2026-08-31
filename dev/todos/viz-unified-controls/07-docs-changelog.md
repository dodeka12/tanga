# Phase 7 — Docs + changelog

## Goal

Document the unified model and record the change in the branch changelog.

## Files

- Edit: `docs/py/viz/…` (control-views / interaction reference pages)
- Edit: `docs/changelog/2026-08-31_fix-file-chooser-bug.md`
- Edit: `docs/changelog/index.md` (at PR time)

## Steps

- [ ] **7.1 — Docs**
  - Update the control-views / interaction reference pages to describe the
    unified id namespace, event envelope, and registry (runtime helpers).
  - Follow `dev/workflows/example-docs.md` if any example changes.

- [ ] **7.2 — Changelog**
  - Add **Refactor** / **Bug Fixes** bullets per `dev/workflows/changelog.md`
    (title `# Changes since version 1.12.0` — confirm with
    `uv run python tools/last-release.py`).
  - Two Bug Fixes: `FileChooserView` select write-back; `controls_define` no
    longer wipes the layout control registry.

- [ ] **7.3 — Full validation**
  - `uv run pytest py/tests/viz/ -q`
  - `node --test dev/src/js-tests/`
  - `uv run mkdocs build --strict`

## Validation

`uv run pytest py/tests/viz/ -q && node --test dev/src/js-tests/ && uv run mkdocs build --strict`
