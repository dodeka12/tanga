# Phase 3 — Docs + changelog

## Goal

Document the reusable editor and record the change.

## Steps

- [x] **3.1 — Docs**
  - Add an "Editor" section to `docs/py/viz/styles/title-annotation.md` (or the
    appropriate viz page): `open_editor(...)`, the `on_close(text, event)`
    contract, and an example that writes the text back via `set_annotation`.

- [x] **3.2 — Changelog**
  - Append a "New Features" bullet to
    `docs/changelog/2026-08-27_feat-more-controls.md` (append — do not create a
    new file).

- [x] **3.3 — Validate**
  - `uv run mkdocs build --strict` passes.

## Validation

`uv run mkdocs build --strict`

## Notes

- Do **not** predict a release version; rename to hash form at PR time.
