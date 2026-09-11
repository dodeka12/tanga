# Phase 8 — Docs + changelog

## Goal

Document the rename (breaking) and the new value-update API, and record the
change per `dev/workflows/changelog.md`.

## Steps

- [x] **8.1 — Docs `docs/py/viz/`**
  - `visualizerapp/controls.md`: `default=` → `value=` in examples and
    parameter-table rows (keep the table's "Default" column header).
  - Add an "Updating control values" section (`set_control_value` /
    `set_control_view_value`).
  - `visualizerapp/app.md`, `visualizerapp/layouts.md`,
    `visualizer/split-views.md`, `visualizer/multi-scene.md`: `default=` →
    `value=`.

- [x] **8.2 — Changelog `docs/changelog/2026-08-27_feat-control-api.md`**
  - Title `# Changes since version 1.8.0` (from `tools/last-release.py`).
  - **Breaking Changes**: `default` → `value` rename (dataclasses, `*View`
    controls, `add_*` APIs, `"value"` wire field).
  - **New Features**: `set_control_value` / `set_control_view_value` +
    `control_update` in-place updates.

- [x] **8.3 — Validate**
  - `uv run mkdocs build --strict`.

## Validation

`uv run mkdocs build --strict`

## Notes

- Do **not** predict a release version; use the since-relative title.
- The changelog is renamed to its hash form at PR time
  (`dev/workflows/pull-request.md`).
