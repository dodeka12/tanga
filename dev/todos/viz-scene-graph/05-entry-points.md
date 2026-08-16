# Phase 5 — Entry points (`Visualizer` / `VizSceneHandle`)

**Status:** Planned

## Goal

Expose the new API at the top level while staying backward compatible:
`add()` still returns a `str` id; `new()` returns a `VizObjectRef`;
`add_group()` returns a `VizObjectRef` for a `VizGroup`. Add `parent_id`
support to the add path so groups and scene-graph parenting work.

## Files

- Modify: `py/pytanga/viz/visualizer.py`
- Modify: `py/pytanga/viz/_scene_handle.py`
- Modify: `py/pytanga/viz/__init__.py`
- (possibly) `py/pytanga/viz/_types.py` (add `VizGroup` to accepted input)

## Steps

### `Visualizer`

- [ ] Add `new(...)` mirroring `add(...)`; returns `VizObjectRef`.
- [ ] Add `add_group(name=None)` returning `VizObjectRef` wrapping a
      `VizGroup`.
- [ ] Thread `parent_id: str | None = None` through `add` / `_add_to_scene`.
- [ ] Special-case `VizGroup` in `_add_to_scene` (no `_resolve` call; store as a
      group node).
- [ ] Ensure `add(...)` behavior and return type (`str`) are unchanged.
- [ ] Delegate `new`/`add_group` to the main-scene handle pattern
      (`VizSceneHandle(self, "")`).

### `VizSceneHandle`

- [ ] Add `new(...)` returning `VizObjectRef(self, node)`.
- [ ] Add `add_group(name=None)`.
- [ ] Re-expose the existing per-scene `add` with `parent_id` support
      (delegating to `Visualizer._add_to_scene`).
- [ ] Add `update_style(...)` for parity with `Visualizer` (used by
      `VizObjectRef.style` setter).

### `_types.py`

- [ ] Add `VizGroup` to the accepted `VizInputType`/`SceneEntity` union (or
      handle it purely within `_add_to_scene`).

### `__init__.py`

- [ ] Export `VizGroup` and `VizObjectRef`; add to `__all__`.
- [ ] Avoid a circular import by importing `VizObjectRef` lazily or from a
      module that doesn't import `visualizer` at module load time.

## Unit tests

File: `py/tests/viz/test_entry_points.py`.

- [ ] `test_add_returns_str` — `viz.add(Point(...))` returns a `str`.
- [ ] `test_new_returns_ref` — `viz.new(Point(...))` returns a `VizObjectRef`.
- [ ] `test_add_group_returns_ref` — `viz.add_group("g")` returns a
      `VizObjectRef`.
- [ ] `test_group_new_attaches_child` — `grp.new(Point(...))` parents the child
      under `grp`.
- [ ] `test_parent_id_add` — `viz.add(Point(...), parent_id=grp.id)` nests
      correctly.
- [ ] `test_scene_handle_new` — `viz.scene("s").new(Point(...))` targets the
      named scene.
- [ ] `test_scene_handle_add_group` — group is created in the named scene.
- [ ] `test_add_backward_compat` — existing add/label flows unchanged.

## Verification

- [ ] `uv run pytest py/tests/viz/test_entry_points.py` passes.
- [ ] `viz.add(Point(...))` returns a `str`.
- [ ] `viz.new(Point(...))` returns a `VizObjectRef`.
- [ ] `grp = viz.add_group("g")` then `grp.new(Point(...))` attaches to `grp`.
- [ ] `scn = viz.scene("s"); scn.new(Point(...))` targets the correct scene.
- [ ] `add`/`new` accept `parent_id` and nest correctly.
- [ ] Existing multi-scene and label tests still pass.
