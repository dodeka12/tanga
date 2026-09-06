# Phase 1 — Number format string

## Goal

Add a per-column `format` string to `number` columns (Python `str.format`
template), persisted in the JSON and settable at runtime, with the value applied
on the backend at serialization.

## Files

- Edit: `py/pytanga/viz/_controls.py`
- Edit: `py/pytanga/viz/views.py`
- Edit: `py/pytanga/viz/templates/controls/table.js`
- Edit: `py/tests/viz/test_controls.py`, `py/tests/viz/test_control_value_api.py`

## Steps

- [x] **1.1 — `ColumnType.format` + wire round-trip**
  - Add `format: str | None = None` to the frozen `ColumnType` dataclass.
  - `ColumnType.to_dict()` emits `"format"` when `kind == "number"` and
    `format` is not `None`.
  - `_resolve_column_type()` parses `format` from a dict hint
    (`{"kind": "number", "format": "{:.2f}m"}`) and returns
    `ColumnType("number", format=fmt)`.

- [x] **1.2 — Format-aware serialization**
  - Change `_serialize_cells()` so each number cell with a non-null `format` is
    serialized via `fmt.format(value)` (e.g. `"{:.2f}m".format(3.5)` →
    `"3.50m"`); all other cells use the existing `_cell_to_str(value)`.
  - Pass the column's resolved `ColumnType` into the per-cell helper (rename or
    add an arg — do not guess the type from the value alone).

- [x] **1.3 — `Table.set_column_format(col, fmt)`**
  - Validate the template with a dry-run `fmt.format(0)` (raise `ValueError` on
    a bad template); store `ColumnType("number", format=fmt)` in
    `_column_types[col]` and mirror it in the `column_types` hint list.
  - Only meaningful when the column's kind is `number` (no-op/`False` otherwise).
  - Record undo history and `_save()`.

- [x] **1.4 — Parse a formatted number on edit**
  - Add a `_parse_number(value: str, column_type: ColumnType)` helper: try
    `int`/`float` on the raw string first; otherwise strip the template's
    literal text (everything outside `{:spec}`) and parse the numeric core with
    the spec's conversion (`d`/`x`… → int, else float).
  - `Table.set_cell` for a `number` column coerces the entered string via
    `_parse_number` (rejecting unparseable input) so the model keeps a real
    number and re-serialization re-applies the format.

- [x] **1.5 — `TableView.set_column_format(col, fmt)`**
  - Delegate to `self.control.set_column_format(...)` and `_push_value()` on
    success; return the bool.

- [x] **1.6 — Frontend carries `format` + relaxes number validation**
  - `normalizeColumnType(t)` in `table.js` keeps `format: t.format || null`.
  - The number editor (`openEditor`, `kind === "number"`) skips the local
    `isNumeric` rejection when the column has a `format` (the backend parses
    and is authoritative); still sends the raw entered string via
    `control:cell_change`.

- [x] **1.7 — Tests**
  - `ColumnType.to_dict`/`_resolve_column_type` round-trip `format`.
  - `get_value()` serializes a formatted number as the formatted string.
  - `set_column_format` mutates + persists (via `to_dict`) + rejects a bad
    template.
  - `set_cell` parses `"4.20m"` and `"4.2"` back to `4.2` for a `.2f` format.

## Validation

```
uv run pytest py/tests/viz/test_controls.py py/tests/viz/test_control_value_api.py -q
uv run ruff check py/pytanga/viz/
node --check py/pytanga/viz/templates/controls/table.js
```

## Notes

- Display uses the wire value verbatim (the backend already formatted it), so no
  JS format-spec shim is needed; the only frontend change is carrying `format`
  for the editor's validation relaxation.
- `set_value` / `from_dict` already re-resolve types, so a loaded `format` flows
  through unchanged.
