# Phase 4 — `MenuView` model + global overlay slot + `add_menu` API

## Goal

Add the backend `MenuView` layout view, a top-level `overlay` slot to
`serialize_layout`, and the `add_menu(scene_name=None)` convenience API. No
frontend rendering yet (Phase 5).

## Files

- Edit: `py/pytanga/viz/views.py`
- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/pytanga/viz/_scene_handle.py`
- Edit: `py/pytanga/viz/__init__.py`
- New/extend: `py/tests/viz/test_views.py`, `py/tests/viz/test_layout_api.py`

## Steps

- [x] **4.1 — `MenuView` (`views.py`)**
  - Add `MenuView(View)` (`_node_type = "menu"`) with `trigger`, `label`, `mode`
    (`"dropdown"`/`"bar"`), `direction` (default `"vertical"`), `position`,
    `children`. Validate `mode` and `direction`.
  - `_serialize` emits `trigger` (str), `label`, `mode`, `direction`, `position`,
    and `children` (each `child._serialize(id_gen)`).

- [x] **4.2 — `serialize_layout` overlay slot (`views.py`)**
  - Extend `serialize_layout(root, name="", overlay: list[View] | None = None)`:
    when `overlay` is non-empty, emit `"overlay": [v._serialize(id_gen) ...]`;
    otherwise omit the key. Keep `scenes` as `iter_scene_names(root)`.

- [x] **4.3 — `Visualizer.add_menu` + global overlay state (`visualizer.py`)**
  - Add `self._global_overlay: list[View] = []` in `__init__`.
  - `add_menu(mid=None, *, label="", trigger=..., mode="dropdown",
    direction="vertical", position=None, children=None, scene_name=None) -> str`:
    build a `MenuView`, store it (id → view) for global menus, register any
    control-view handlers in its subtree (reuse `_register_control_handlers` /
    `iter_control_views`), and re-serve the layout with the global overlay.
  - Wire `_layout_serialized_for` / `set_layout` to pass
    `overlay=self._global_overlay`; for the no-layout single-scene case, create a
    minimal default layout (`StackView("vertical", [SceneView("main")])`) when a
    global overlay view is added.

- [x] **4.4 — `VizSceneHandle.add_menu` (`_scene_handle.py`)**
  - Forward to `self._viz.add_menu(...)`, scoped to `self._name` when that maps to
    the base scene (global), and raise/ignore for non-base scenes (per the
    non-goal: per-scene-name menus out of scope).

- [x] **4.5 — Exports (`__init__.py`)**
  - Export `MenuView` (and confirm `EControlVariant` already exported from Phase 1).

- [x] **4.6 — Tests**
  - `test_views.py`: `MenuView` serialization (type/fields/children), nested
    `MenuView` child, `mode`/`direction` validation.
  - `test_layout_api.py`: `serialize_layout(..., overlay=[menu])` includes the
    `overlay` key; omitted when empty; `add_menu` returns an id and is reflected
    in `_layout_serialized_for`.

## Validation

`uv run pytest py/tests/viz/test_views.py py/tests/viz/test_layout_api.py -q`
