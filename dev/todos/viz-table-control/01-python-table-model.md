# Phase 1 — Python table model

## Goal

The backend data model for the table control: three event dataclasses, the
`Table` control dataclass, its serialization branch, and value coercion — all in
`py/pytanga/viz/_controls.py`, with unit tests.

## Files

- Edit: `py/pytanga/viz/_controls.py`
- Edit: `py/tests/viz/test_controls.py`

## Steps

- [ ] **1.1 — Event dataclasses (`_controls.py`)**
  - Add `TableCellChange(row: int, col: int, value: str)`,
    `TableRowAdd(row: int, values: list[str])`, and
    `TableColumnAdd(col: int, header: str, values: list[str])` after
    `ControlEvent`, with docstrings noting zero-based indices.

- [ ] **1.2 — `Table` control dataclass**
  - `class Table(Control)` with `kind: str = "table"`, `columns: list[str]`,
    `rows: list[list[str]]`, `allow_add_rows: bool = True`,
    `allow_add_columns: bool = True`, `on_cell_change: Handler | None = None`,
    `on_row_add: Handler | None = None`, `on_column_add: Handler | None = None`.
  - Use `field(default_factory=list)` for `columns` and `rows`.

- [ ] **1.3 — Serialization branch (`_serialize_one_control`)**
  - Add an `elif isinstance(ctrl, Table)` branch emitting `columns`, `rows`,
    `allow_add_rows`, `allow_add_columns`.

- [ ] **1.4 — Value helpers (`get_control_value` / `set_control_value`)**
  - Add `Table` to the value-bearing tuple in `get_control_value`.
  - Add a `Table` branch in `set_control_value`: accept a
    `{"columns": [...], "rows": [...]}` dict (or a `Table`) and copy its
    `columns`/`rows` (string-coercing cells).

- [ ] **1.5 — Unit tests (`test_controls.py`)**
  - Serialization: a `Table` with columns/rows/flags round-trips to the exact
    dict shape (flags present, `tooltip` omitted when empty).
  - `get_control_value` returns the grid dict; `set_control_value` replaces
    `columns`/`rows`.

## Validation

`uv run pytest py/tests/viz/test_controls.py -q`

## Notes

- Mirror the `FileChooser` / `ValueEdit` precedent: `kind` is a class-level
  default, `on_*` handlers are plain attributes (not serialized).
- Keep cell values as `str` on the wire; coercion to numbers is the backend's
  job in its handler.
