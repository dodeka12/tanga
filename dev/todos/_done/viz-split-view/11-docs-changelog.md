# Phase 11 — Docs + changelog

## Goal

Document the public API and record the change, per `dev/workflows/changelog.md`.

## Steps

- [x] **11.1 — Docs `docs/py/viz/`**
  - New `visualizer/split-views.md`: `View`/`SplitView`/`SceneView`/
    `ControlGroupView`/`SpacerView`/`Size` API, units, fixed vs movable
    splitters, nesting, and the `?view=` URL note.
  - Added `Split Views` to the `mkdocs.yml` nav (under Visualizer).

- [x] **11.2 — `docs/changelog/2026-08-24_feat-multi-view.md`**
  - Title `# Changes since version 1.0.1` (from `tools/last-release.py`);
    New Features (split views + multi-scene subscription) and Refactor
    (`ThreeJsView` extraction) bullets.

- [x] **11.3 — Validate**
  - `uv run mkdocs build --strict` → "Documentation built in 5.77 seconds"
    (two pre-existing anchor INFO warnings in `object-interaction.md`).

## Validation

`uv run mkdocs build --strict` (passes).

## Notes

- Do **not** predict a release version; use the since-relative title.
- The changelog is renamed to its hash form at PR time
  (`dev/workflows/pull-request.md`).
