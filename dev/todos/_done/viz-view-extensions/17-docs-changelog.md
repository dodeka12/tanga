# Phase 17 — Docs, changelog, export gate, full validation

## Goal

Document the unified view mode and the new view controls; update the changelog;
confirm the standalone HTML export is unaffected; run the full suite.

## Files

- Edit: `docs/dev/architecture/viz-controls-and-interactions.md` (or new sibling)
- Edit: `docs/py/viz/interaction/control-views.md` (+ menu/dialog pages)
- Edit: `docs/py/viz/visualizer/split-views.md`, `docs/py/viz/app/layouts.md`
- Edit: `docs/changelog/<branch>.md`

## Steps

- [x] **17.1 — Architecture doc**
  - Extend `docs/dev/architecture/viz-controls-and-interactions.md` (or add
    `viz-views-menus-dialogs.md` beside it) covering: the unified `View` model,
    the single `(id, event)` communication channel, per-pane vs global overlay
    containers, `EControlVariant`, and the `GroupView`-only group model.
  - Add a note that single-scene mode is served as a one-`SceneView` layout and the
    frontend always renders through the layout tree.

- [x] **17.2 — API docs**
  - Document `GroupView` (icon/icon_only, borderless fold), `MenuView`, `Dialog`,
    `EControlVariant`, `add_menu`, `show_dialog`/`remove_dialog`/`clear_dialogs`,
    and the `add_control_group` → `GroupView` unification in the relevant
    `docs/py/viz/**` pages; link the new examples.

- [x] **17.3 — View-mode docs**
  - Update `split-views.md` / `layouts.md` to state that a single scene is served as
    a one-`SceneView` layout and that overlays (menus, dialogs, control groups)
    render identically in single-scene and layout modes.

- [x] **17.4 — Changelog**
  - Append a "View-mode unification" bullet (and any breaking-change note for the
    group unification) to the branch changelog per `dev/workflows/changelog.md`.

- [x] **17.5 — Export regression gate**
  - Run `uv run pytest py/tests/viz/test_export_static.py
    py/tests/viz/test_export_camera.py py/tests/viz/test_export_renderers.py -q`
    and confirm the standalone HTML export is unaffected (single-scene, no
    controls/layouts).

- [x] **17.6 — Full validation**
  - `uv run pytest -q`, `uv run ruff check py/pytanga/viz/`, `node --check` on all
    touched JS, `uv run python tools/generate-example-docs.py --check`, and
    `uv run mkdocs build --strict`.

## Validation

`uv run pytest -q && uv run ruff check py/pytanga/viz/ && node --check py/pytanga/viz/templates/viewer.js && uv run python tools/generate-example-docs.py --check && uv run mkdocs build --strict`
