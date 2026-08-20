# Phase 8 — Standalone & figure HTML export verification

**Status:** Done

## Goal

Ensure the standalone (`display_static`) and figure HTML export paths still
work end-to-end after the scene-graph refactor, and that groups/transforms are
preserved in the exported HTML.

## Files

- Modify: `py/pytanga/viz/export/_figure_html.py`
- Modify: `py/pytanga/viz/export/_bootstrap/_entities.py`
- Modify: `py/pytanga/viz/export/_bootstrap/_scene.py`
- (as needed) `py/pytanga/viz/export/_html.py`

## Steps

- [x] Emit `parent_id` + `transform` in exported entity entries.
- [x] In `js_entity_creation`, parent meshes under their parent before adding to
      scene (mirror the live `viewer.js` logic).
- [x] Add a `VizGroup` renderer path for the static export path
      (`THREE.Group`).
- [x] Confirm `Scene.full_state()` output drives both `display_static` and
      `FigureConfig`/figure export unchanged.
- [x] Confirm a group + children is serialized in DFS pre-order so parents are
      present before children (no deferred-parent resolution needed).
- [x] Preserve mesh cleanup (no orphaned groups) on static re-render.

## Unit tests

- [x] `py/tests/viz/test_export_static.py`:
  - [x] `test_static_full_state_has_parent_and_transform` — exported entities
        include `parent_id` / `transform`.
  - [x] `test_static_group_kind` — groups serialized with `kind == "VizGroup"`.
  - [x] `test_static_render_html` — standalone HTML generation succeeds with a
        group + child.
  - [x] `test_figure_html_generation` — figure export path succeeds and contains
        the group JS.
  - [x] `test_parent_before_child` — DFS pre-order in the generated entity list.

## Verification

- [x] `uv run pytest py/tests/viz/test_export_static.py` passes.
- [x] `viz.display_static()` produces a viewer that looks identical to the live
      viewer for a group + children scene.
- [x] Figure HTML export renders the hierarchy and transforms correctly.
- [x] Existing `test_export_smoke.py` / `test_export_renderers.py` still pass.