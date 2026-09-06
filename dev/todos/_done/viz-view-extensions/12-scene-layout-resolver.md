# Phase 12 — Per-scene default layout (`visualizer.py`)

## Goal

Make "single scene" resolvable as a one-pane layout: any scene name maps to a
serialized `view_layout` whose root is `StackView("vertical", [SceneView(name)])`,
merged with the global overlay (base scene `""` only) and per-scene overlays.
This is the model phases 13–15 build on to unify the two view modes.

## Files

- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/tests/viz/test_layout_api.py`

## Steps

- [x] **12.1 — `_scene_layout_for(scene_name)`**
  - Add a resolver returning the serialized single-scene layout for *scene_name*.
  - For the base scene `""`, reuse the existing default layout (`_layouts[""]` /
    `_layouts_serialized[""]`, auto-created by `_sync_overlays`).
  - For a named scene, build `StackView("vertical", [SceneView(name)])`, inject
    `_scene_overlays[name]`, and serialize **without** the global overlay.

- [x] **12.2 — Keep it in sync in `_sync_overlays`**
  - Extend `_sync_overlays` to also rebuild the named-scene single-scene layouts
    (e.g. `self._scene_layouts_serialized: dict[str, dict]`), not just the
    registered layouts and the base default layout.

- [x] **12.3 — Tests**
  - `test_layout_api.py`: `_scene_layout_for("")` is a `view_layout` whose root is a
    `stack` wrapping a `scene_view` for `""`; `_scene_layout_for("detail")` wraps a
    `scene_view` for `"detail"`; per-scene overlays appear under that pane's
    `children`; the global overlay is present only for the base scene.

## Validation

`uv run pytest py/tests/viz/test_layout_api.py -q`
