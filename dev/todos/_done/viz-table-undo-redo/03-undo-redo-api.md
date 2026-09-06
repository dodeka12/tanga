# Phase 3 — Backend undo/redo API

## Goal

Expose `undo_table` / `redo_table` / `clear_table_history` /
`can_undo_table` / `can_redo_table` on `Visualizer` and `VizSceneHandle`, and
`undo` / `redo` / `can_undo` / `can_redo` conveniences on `TableView`, so
application code can trigger undo/redo (e.g. from its own buttons).

## Files

- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/pytanga/viz/_scene_handle.py`
- Edit: `py/pytanga/viz/views.py`
- Edit: `py/pytanga/viz/__init__.py` (if exporting new symbols — verify what
  `views`/`_scene_handle` already export)
- Edit: `py/tests/viz/test_control_value_api.py` (or `test_table.py`)

## Steps

- [x] **3.1 — Thread `max_history` through constructors**
  - `add_table` / `_add_scene_table` (`visualizer.py`) gain
    `max_history: int = 100`, passed to `Table(...)`.
  - `VizSceneHandle.add_table` (`_scene_handle.py`) forwards `max_history`.
  - `TableView.__init__` (`views.py`) gains `max_history: int = 100`, passed to
    `Table(...)`.

- [x] **3.2 — `Visualizer.undo_table` / `redo_table`**
  - Resolve via `_resolve_control(cid)`; raise `KeyError` when not found (match
    `set_control`); when `control` is a `Table`, call `undo()`/`redo()`; on
    success push `_push_control_update(ref.scene, cid, get_control_value(control))`;
    return the bool.

- [x] **3.3 — `clear_table_history` / `can_undo_table` / `can_redo_table`**
  - Resolve + `clear_history()` / read the properties; raise `KeyError` when not
    found. No push for `clear_table_history` (state is unchanged).

- [x] **3.4 — `VizSceneHandle` mirrors (`_scene_handle.py`)**
  - `undo_table(cid)`, `redo_table(cid)`, `clear_table_history(cid)`,
    `can_undo_table(cid)`, `can_redo_table(cid)` forwarding to
    `self._viz.<method>(cid)`.

- [x] **3.5 — `TableView` conveniences (`views.py`)**
  - `undo() -> bool`, `redo() -> bool` delegating to `self.control`; read-only
    `can_undo` / `can_redo` properties. Document that browser re-sync goes
    through `viz.undo_table(...)`.

- [x] **3.6 — Tests**
  - `undo_table`/`redo_table` mutate the model and push `control_update`
    (monkeypatch `_push_control_update` to capture the pushed `{columns, rows}`).
  - `undo_table` on empty history returns `False` and pushes nothing.
  - `can_undo_table`/`can_redo_table` reflect stack state.
  - `VizSceneHandle.undo_table` routes to the correct scene.
  - `TableView.undo()`/`redo()` operate on `self.control`.
  - `max_history` flows through `add_table` and `TableView` to the `Table`.

## Validation

`uv run pytest py/tests/viz/test_control_value_api.py py/tests/viz/test_table.py py/tests/viz/test_views.py -q`

## Notes

- Reuse `_resolve_control` so the API covers both panel controls and layout
  views; `get_control_value(control)` returns the `{"columns", "rows"}` dict the
  frontend `apply` already consumes.
- `clear_table_history` intentionally does not push (the grid data doesn't
  change), matching "only the table itself is displayed".
