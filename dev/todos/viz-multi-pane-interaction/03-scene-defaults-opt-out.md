# Phase 3 — Per-scene default axes/grid opt-out

## Goal

Let a named scene be created without the generic default `Axes2D`/`Grid` so a
`CoordinateSystem` pane draws only its own, correctly-scaled grid/axes.

## Files

- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/tests/viz/test_scene_session.py`

## Steps

- [x] **3.1 — Add `add_axes`/`add_grid` to `Visualizer.scene()`**
  - Extend the signature to
    `def scene(self, name, *, enable_server_stop_key=False, add_axes: bool = True, add_grid: bool = True)`.
  - In the `if name not in self._scenes:` branch, replace
    `self._add_default_scene_objects(name)` with
    `self._add_default_scene_objects(name, add_axes=add_axes, add_grid=add_grid)`.
- [x] **3.2 — Document the semantics in the docstring**
  - Note the flags apply only at scene creation, and that the main scene `""`
    is created in `__init__` (use the `add_default_axes`/`add_default_grid`
    constructor flags for it).
- [x] **3.3 — Add a regression test**
  - Assert `Visualizer(add_default_axes=True, add_default_grid=True).scene("plot", add_axes=False, add_grid=False)`
    contains no default `Axes2D`/`Grid` objects while `scene("other")` (defaults)
    does, and that a later `_add_default_scene_objects("plot")` still adds
    nothing (idempotency guard intact).

## Validation

`uv run pytest py/tests/viz/test_scene_session.py -q && uv run ruff check py/pytanga/viz/visualizer.py`

## Notes

- `_add_default_scene_objects` already accepts `add_axes`/`add_grid` and already
  records the scene in `_default_objects_added` even when nothing is added
  (`visualizer.py:915,967`) — no change needed there.
- Defaults `True` keep the current constructor-flag behaviour, so this is
  backward compatible.
