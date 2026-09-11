# Phase 3 — Visualizer API + scene handle + exports

## Goal

Public `add_table` APIs on `Visualizer` and `VizSceneHandle`, handler
registration into the `ControlHandlerRegistry`, and public exports.

## Files

- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/pytanga/viz/_scene_handle.py`
- Edit: `py/pytanga/viz/__init__.py`
- Edit: `py/tests/viz/test_file_chooser.py` (or `test_controls.py`) — add the
  `add_table` registration test here.

## Steps

- [x] **3.1 — `add_table` / `_add_scene_table` (`visualizer.py`)**
  - `add_table(cid, *, label="", columns=None, rows=None,
    allow_add_rows=True, allow_add_columns=True, tooltip="",
    on_cell_change=None, on_row_add=None, on_column_add=None, parent_id=None)`
    delegating to `_add_scene_table("", ...)`.
  - `_add_scene_table` builds a `Table`, calls
    `self._scenes[scene_name].add_control(ctrl)`, registers
    `on_cell_change` → `cid`, `on_row_add` → `__row_add__{cid}`,
    `on_column_add` → `__column_add__{cid}` (only when not `None`), pushes
    `_push_controls(scene_name)`, returns `cid`.

- [x] **3.2 — `VizSceneHandle.add_table` (`_scene_handle.py`)**
  - Forward to `self._viz._add_scene_table(self._name, ...)` (mirror
    `add_text_area`).

- [x] **3.3 — Public exports (`__init__.py`)**
  - Import and add to `__all__`: `Table`, `TableCellChange`, `TableRowAdd`,
    `TableColumnAdd`, `TableView`.

- [x] **3.4 — Tests**
  - `test_add_table_registers_handlers_and_pushes`: monkeypatch `_push_controls`;
    add a table with the three handlers; assert `_handler_registry` maps
    `cid`/`__row_add__{cid}`/`__column_add__{cid}` and the stored control is a
    `Table` with the expected `columns`/`rows`.

## Validation

`uv run pytest py/tests/viz/test_controls.py py/tests/viz/test_views.py
py/tests/viz/test_file_chooser.py py/tests/viz/test_entry_points.py -q`

## Notes

- Dispatch is **not** wired yet (Phase 4); this phase only stores the control
  and registers handlers.
- `__init__.py` imports `TableView` from `.views` (it already imports the other
  `*View` classes there) and the dataclasses from `._controls`.
