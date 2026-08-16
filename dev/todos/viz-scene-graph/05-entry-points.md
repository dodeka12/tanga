# Phase 5 — Entry points (`Visualizer` / `VizSceneHandle`)

**Status:** Planned (revised after design discussion)

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

- [ ] Add `new(...)` mirroring `add(...)`; returns `VizObjectRef`.
- [ ] Add `add_group(name=None)` returning `VizObjectRef` wrapping a
      `VizGroup` node.
- [ ] Thread `parent_id: str | None = None` through `add` / `_add_to_scene`;
      thread `attach_to: str | None = None` for overlay creation.
- [ ] Special-case `VizGroup` in `_add_to_scene` (no `_resolve`; store as a
      group node).
- [ ] Thread the resolved `styles_map` into node creation (`Scene` holds the
      default styles, so resolve at creation).
- [ ] Add `add_label`/`new_label`-style helpers returning refs (label nodes are
      `VizOverlayObject`s with `attach_to`).
- [ ] Keep `add(...)` behavior and `str` return type unchanged.
- [ ] Add `update_control(ctrl_id, ...)` re-pushing via `controls_define`.

### `VizSceneHandle`

- [ ] Add `new(...)` returning `VizObjectRef(self, node)`.
- [ ] Add `add_group(name=None)`.
- [ ] Re-expose per-scene `add` with `parent_id`/`attach_to` support.
- [ ] Add `update_style(...)` parity.
- [ ] Add `new_label(...)`/label-ref accessors for labels attached to a node.

### `_types.py`

- [ ] Add `VizGroup` to accepted input (or handle purely in `_add_to_scene`).

### `__init__.py`

- [ ] Export `VizGroup`, `VizObjectRef`, `VizSceneObject`, `VizOverlayObject`.
- [ ] Import `VizObjectRef` lazily to avoid a circular import.

## Control update details

- [ ] `update_control(ctrl_id, **fields)` mutates the stored `Control` and
      re-pushes `controls_define` (separate channel). A `Slider` range update
      is `update_control("s", min=0, max=10)`.
- [ ] Controls remain `Control` dataclasses (not viz nodes) on the separate
      channel, but may carry `parent_id`/`attach_to` for scene-node following.

## Unit tests

File: `py/tests/viz/test_entry_points.py`.

- [ ] `test_add_returns_str` — `viz.add(Point(...))` returns a `str`.
- [ ] `test_new_returns_ref` — `viz.new(Point(...))` returns a `VizObjectRef`.
- [ ] `test_add_group_returns_ref` — `viz.add_group("g")` returns a
      `VizObjectRef`.
- [ ] `test_group_new_attaches_child` — `grp.new(Point(...))` parents the child
      under `grp`.
- [ ] `test_parent_id_add` — `viz.add(Point(...), parent_id=grp.id)` nests.
- [ ] `test_attach_to_label` — a label created with `attach_to` references the
      scene node.
- [ ] `test_update_control` — `viz.update_control("s", max=10)` updates the
      stored slider and re-pushes.
- [ ] `test_scene_handle_new` — `viz.scene("s").new(Point(...))` targets the
      named scene.
- [ ] `test_scene_handle_add_group` — group is created in the named scene.
- [ ] `test_add_backward_compat` — existing add/label flows unchanged.

## Verification

- [ ] `uv run pytest py/tests/viz/test_entry_points.py` passes.
- [ ] `viz.add(Point(...))` returns a `str`.
- [ ] `viz.new(Point(...))` returns a `VizObjectRef`.
- [ ] `grp = viz.add_group("g")` then `grp.new(Point(...))` attaches to `grp`.
- [ ] A label created with `attach_to=node_id` is discovered and follows.
- [ ] `viz.update_control("s", max=10)` mutates + re-pushes the control.
- [ ] Existing multi-scene and label tests still pass.