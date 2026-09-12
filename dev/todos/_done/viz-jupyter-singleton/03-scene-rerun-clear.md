# Phase 3 — `scene(name)` re-run clear

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md`) for the
> subsystem(s) this work touches, so the new code aligns with the documented
> architecture.  If this work introduces or changes architecture, update the
> developer docs.

## Goal

`scene(name)` creates a named scene on first call and clears it when the same
notebook cell is re-run, while a different cell (or a second call in the same
execution) keeps get-or-create semantics.

## Files

- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/tests/viz/test_visualizer_singleton.py`

## Steps

- [x] **3.1 — Track per-scene cell/execution keys**
  - In `__init__`, add
    `self._scene_keys: dict[str, tuple[str | None, int]] = {}`.

- [x] **3.2 — Clear on same-cell re-run in `scene()`**
  - In `scene()`, compute `cid = current_cell_id()` and
    `token = execution_token()`.
  - In the create branch, store `self._scene_keys[name] = (cid, token)`.
  - In the existing-name branch, clear + re-add defaults only when
    `stored = self._scene_keys.get(name)` satisfies `stored[0] is not None`,
    `stored[0] == cid`, and `stored[1] != token`:
    ```python
    self._layout.scenes[name].clear()
    self._default_objects_added.discard(name)
    self._add_default_scene_objects(name, add_axes=add_axes, add_grid=add_grid)
    self._scene_keys[name] = (cid, token)
    ```
  - `current_cell_id` / `execution_token` are already imported from
    `._notebook_cell`.

- [x] **3.3 — Test re-run clear**
  - Monkeypatch `_is_jupyter` to `True`, and monkeypatch
    `pytanga.viz.visualizer.current_cell_id` / `execution_token` to simulate
    cells.
  - Assert: first call creates + adds; a second call with the same cell/token
    does not clear; a different cell id does not clear; the same cell id with a
    bumped token clears and re-adds defaults per `add_axes`/`add_grid`.

## Validation

`uv run pytest py/tests/viz/test_visualizer_singleton.py -q`

## Notes

- Outside notebooks `current_cell_id()` is `None` and `execution_token()` is
  constant `0`, so the clear never triggers — scripts keep get-or-create.
- `scene("")` returns the main-scene handle without clearing (its key is never
  stored); the main scene is managed by the constructor reset (Phase 2).
- `add_scene()` is intentionally unchanged (strict: raises if the name is taken).
