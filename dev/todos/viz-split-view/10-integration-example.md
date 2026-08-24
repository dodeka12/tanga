# Phase 10 — Example + integration checks

## Goal

A user-facing example and an integration pass proving nested splits, fixed vs
movable splitters, control-group panes, and the dummy-fill rule together.

## Steps

- [x] **10.1 — `py/examples/viz/demo_split_view.py`**
  - Nested horizontal/vertical split; `SceneView` ×3 + one `ControlGroupView`
    (fixed 280 px sidebar); sliders + a control group on the "side" scene.

- [x] **10.2 — Integration checklist (manual, in browser)**
  - Drag both splitter orientations; fixed sidebar pins its splitter; control
    pane growth resizes neighbors; leftover space shows a spacer.
  - Deferred: requires a browser (no headless browser in the repo).

- [x] **10.3 — Validate**
  - `uv run ruff check py/examples/viz/demo_split_view.py` (clean) + layout
    serialization smoke (`iter_scene_names` → `['side','main','detail']`).

## Validation

`uv run ruff check py/examples/viz/demo_split_view.py` + a serialization smoke run.
