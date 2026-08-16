# Phase 8 — Standalone & figure HTML export verification

**Status:** Planned

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

- [ ] Emit `parent_id` + `transform` in exported entity entries.
- [ ] In `js_entity_creation`, parent meshes under their parent before adding to
      scene (mirror the live `viewer.js` logic).
- [ ] Add a `VizGroup` renderer path for the static export path
      (`THREE.Group`).
- [ ] Confirm `Scene.full_state()` output drives both `display_static` and
      `FigureConfig`/figure export unchanged.
- [ ] Confirm a group + children is serialized in DFS pre-order so parents are
      present before children (no deferred-parent resolution needed).
- [ ] Preserve mesh cleanup (no orphaned groups) on static re-render.

## Unit tests

- [ ] `py/tests/viz/test_export_static.py`:
  - [ ] `test_static_full_state_has_parent_and_transform` — exported entities
        include `parent_id` / `transform`.
  - [ ] `test_static_group_kind` — groups serialized with `kind == "VizGroup"`.
  - [ ] `test_static_render_html` — standalone HTML generation succeeds with a
        group + child.
  - [ ] `test_figure_html_generation` — figure export path succeeds and contains
        the group JS.
  - [ ] `test_parent_before_child` — DFS pre-order in the generated entity list.

## Verification

- [ ] `uv run pytest py/tests/viz/test_export_static.py` passes.
- [ ] `viz.display_static()` produces a viewer that looks identical to the live
      viewer for a group + children scene.
- [ ] Figure HTML export renders the hierarchy and transforms correctly.
- [ ] Existing `test_export_smoke.py` / `test_export_renderers.py` still pass.