# Phase 1 — Column types (model, deduction, serialization)

## Goal

Introduce the per-column `ColumnType` model: deduction from data, explicit
`column_types=[…]` hints, and `column_types` on the wire.

## Files

- Edit: `py/pytanga/viz/_controls.py`
- Edit: `py/pytanga/viz/views.py`
- Edit: `py/pytanga/viz/__init__.py`
- Edit: `py/tests/viz/test_table.py`, `py/tests/viz/test_control_value_api.py`

## Steps

- [x] **1.1 — `ColumnType` + deduction helpers (`_controls.py`)**
  - Add `import numbers` (or a numeric check) and helpers `_is_number(v)` /
    `_is_bool(v)` / `_cell_to_str(v)` (bool → `"true"`/`"false"`, else `str(v)`).
  - Add `@dataclass(frozen=True) class ColumnType(kind: str, values: tuple[str, ...] = ())`
    with `to_dict()` → `{"kind": …, "values": […]}` (omit `values` unless enum).
  - Add `_deduce_column_type(values) -> ColumnType`: all-bool → `bool`; else
    all-numeric (bool excluded) → `number`; else `string`; empty → `string`.
  - Add `_resolve_column_type(hint, values) -> ColumnType`: normalize a hint
    (`None`→deduce; `"number"|"float"|"int"`→number; `"string"|"text"`→string;
    `"bool"|"boolean"`→bool; a list/tuple/set of str→enum) else deduce.

- [x] **1.2 — `Table` state (`_controls.py`)**
  - Add `column_types: list[Any] | None = field(default=None)` (the explicit
    hints) and internal `_column_types: list[ColumnType] =
    field(default_factory=list, repr=False, compare=False)` (resolved).
  - Resolve `_column_types` once in `__post_init__` from hints + `self.rows`.
  - Broaden `rows` annotation to `list[list[Any]]`.

- [x] **1.3 — stop coercing cell values (`_controls.py`)**
  - In `set_value`, `set_cell`, `insert_row`, `insert_column`: keep values as
    given (drop `str(...)` coercion) so numeric/bool types survive for deduction;
    keep `columns` coerced via `str(c)` and keep padding missing cells with `""`.

- [x] **1.4 — serialization (`_controls.py`)**
  - Add `_serialized_rows()` → `(rows_as_strings, column_types)` where
    `column_types = [t.to_dict() for t in self._column_types]`.
  - `get_value()` and `_fields()` return `columns` + string `rows` +
    `column_types` (replacing the inline coercion). Re-resolve `_column_types`
    when the column set changes (`set_value`, `insert_column`, `delete_column`).

- [x] **1.5 — `TableView` surface (`views.py`, `__init__.py`)**
  - Add `column_types` param to `TableView.__init__`, pass to `Table`.
  - Add `column_type=None` param to `TableView.add_column` (and
    `Table.insert_column`) so new columns can carry an explicit type.
  - Re-export `ColumnType` (and any new symbols) from `py/pytanga/viz/__init__.py`.

- [x] **1.6 — tests**
  - Deduction: all-bool → bool; all-num → number; mixed → string; bool+num → string;
    empty column → string; enum never deduced.
  - Explicit: `column_types=[None, ["a","b"], "bool"]` round-trips through
    `serialize()`/`get_value()`; sticky across `set_value`.
  - Update existing exact-payload assertions (`get_value()` now includes
    `column_types`).

## Validation

`uv run pytest py/tests/viz/ -q`

## Notes

- The undo/redo `_snapshot` keeps original types (list copies, no coercion), so
  `_restore` round-trips types; `handle_event` undo/redo pushes `get_value()`
  (strings + `column_types`), not `_snapshot()`.
