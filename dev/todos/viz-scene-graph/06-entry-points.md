# Phase 6 — Entry points (`Visualizer` / `VizSceneHandle`)

**Status:** Done

## Goal

Expose the new API at the top level while staying backward compatible:
`add()` still returns a `str` id; `new()` returns a `VizObjectRef`;
`add_group()` returns a `VizObjectRef` for a `VizGroup`; `attach_to` and
`parent_id` hook overlays and scene children into the graph; `update_control`
adds post-creation control mutation.

## Files

- Modify: `py/pytanga/viz/visualizer.py`
- Modify: `py/pytanga/viz/_scene_handle.py`
- Modify: `py/pytanga/viz/__init__.py`
- (possibly) `py/pytanga/viz/_types.py`

## Steps

### `Visualizer`

- [x] Add `new(...)` mirroring `add(...)`; returns `VizObjectRef`.
- [x] Add `add_group(name=None)` returning `VizObjectRef` wrapping a
      `VizGroup` node.
- [x] Thread `parent_id: str | None = None` through `add` / `_add_to_scene`;
      thread `attach_to: str | None = None` for overlay creation.
- [x] Special-case `VizGroup` in `_add_to_scene` (no `_resolve`; store as a
      group node).
- [x] Thread the resolved `styles_map` into node creation (`Scene` holds the
      default styles, so resolve at creation).
- [x] Add `add_label`/`new_label`-style helpers returning refs (label nodes are
      `VizOverlayObject`s with `attach_to`).
- [x] Keep `add(...)` behavior and `str` return type unchanged.
- [x] Add `update_control(ctrl_id, ...)` re-pushing via `controls_define`.

### `VizSceneHandle`

- [x] Add `new(...)` returning `VizObjectRef(self, node)`.
- [x] Add `add_group(name=None)`.
- [x] Re-expose per-scene `add` with `parent_id`/`attach_to` support.
- [x] Add `update_style(...)` parity.
- [x] Add `new_label(...)`/label-ref accessors for labels attached to a node.

### `_types.py`

- [x] Add `VizGroup` to accepted input (or handle purely in `_add_to_scene`).

### `__init__.py`

- [x] Export `VizGroup`, `VizObjectRef`, `VizSceneObject`, `VizOverlayObject`.
- [x] Import `VizObjectRef` lazily to avoid a circular import.

## Control update details

- [x] `update_control(ctrl_id, **fields)` mutates the stored `Control` and
      re-pushes `controls_define` (separate channel). A `Slider` range update
      is `update_control("s", min=0, max=10)`.
- [x] Controls remain `Control` dataclasses (not viz nodes) on the separate
      channel, but may carry `parent_id`/`attach_to` for scene-node following.

## Unit tests

File: `py/tests/viz/test_entry_points.py`.

- [x] `test_add_returns_str` — `viz.add(Point(...))` returns a `str`.
- [x] `test_new_returns_ref` — `viz.new(Point(...))` returns a `VizObjectRef`.
- [x] `test_add_group_returns_ref` — `viz.add_group("g")` returns a
      `VizObjectRef`.
- [x] `test_group_new_attaches_child` — `grp.new(Point(...))` parents the child
      under `grp`.
- [x] `test_parent_id_add` — `viz.add(Point(...), parent_id=grp.id)` nests.
- [x] `test_attach_to_label` — a label created with `attach_to` references the
      scene node.
- [x] `test_update_control` — `viz.update_control("s", max=10)` updates the
      stored slider and re-pushes.
- [x] `test_scene_handle_new` — `viz.scene("s").new(Point(...))` targets the
      named scene.
- [x] `test_scene_handle_add_group` — group is created in the named scene.
- [x] `test_add_backward_compat` — existing add/label flows unchanged.

## Verification

- [x] `uv run pytest py/tests/viz/test_entry_points.py` passes.
- [x] `viz.add(Point(...))` returns a `str`.
- [x] `viz.new(Point(...))` returns a `VizObjectRef`.
- [x] `grp = viz.add_group("g")` then `grp.new(Point(...))` attaches to `grp`.
- [x] A label created with `attach_to=node_id` is discovered and follows.
- [x] `viz.update_control("s", max=10)` mutates + re-pushes the control.
- [x] Existing multi-scene and label tests still pass.