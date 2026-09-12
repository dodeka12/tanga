# Phase 2 — Constructor re-run reset

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md`) for the
> subsystem(s) this work touches, so the new code aligns with the documented
> architecture.  If this work introduces or changes architecture, update the
> developer docs.

## Goal

Re-running `Visualizer(...)` on the cached instance clears the default scene and
re-adds axes/grid per the current call's flags, instead of doing nothing.

## Files

- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/tests/viz/test_visualizer_singleton.py`

## Steps

- [x] **2.1 — Re-run branch updates axes/grid flags and resets the main scene**
  - Replace the Phase-1 early `return` in `__init__` with:
    ```python
    if getattr(self, "_initialized", False):
        self._add_default_axes = add_default_axes
        self._add_default_grid = add_default_grid
        self._reset_scene("")
        return
    ```
  - `_reset_scene("")` already clears the main scene, discards the
    `_default_objects_added` marker, and re-adds axes/grid via
    `_add_default_scene_objects("")` (which reads the now-updated flags).

- [x] **2.2 — Test re-run reset**
  - Monkeypatch `_is_jupyter` to `True`.  Construct with
    `add_default_axes=False, add_default_grid=False`; add an entity to the main
    scene; construct again; assert the entity is gone.
  - Assert the axes/grid presence after a re-run matches the **second** call's
    flags (e.g. re-run with `add_default_axes=True` re-adds `Axes3D`/`Grid`;
    re-run with `False` leaves them absent).

## Validation

`uv run pytest py/tests/viz/test_visualizer_singleton.py -q`

## Notes

- Constructor reset is in-memory only; it does not `flush()` or `show()` — the
  user's subsequent `viz.add()` / `viz.show()` renders the fresh state.
- Other constructor config (`camera`, `title`, `space_dim`, `background_color`,
  `annotation`, `reuse_existing`, `enable_server_stop_key`) stays
  first-call-wins (see README decisions).
