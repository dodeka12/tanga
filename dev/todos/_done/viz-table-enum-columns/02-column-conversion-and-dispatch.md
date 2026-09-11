# Phase 2 — Conversion + type-change dispatch

## Goal

Make `convert_column` understand the `"column"` target (with a `source`), refuse
`"custom"`, and block converting a `"custom"` column; thread `source` through the
`column_type_change` payload and handler dataclass.

## Files

- Edit: `py/pytanga/viz/_controls.py`
- Edit: `py/tests/viz/test_table_types.py`

## Steps

- [x] **2.1 — `TableColumnTypeChange` gains `source`**
  - Add `source: int | None = None` to the dataclass (~line 155) and update the
    docstring to mention the `column` source.

- [x] **2.2 — `parse_table_event` reads `source`**
  - In the `column_type_change` branch (~line 570), read
    `source = table_payload.get("source")`, coerce to `int` or `None`, and pass
    it into `TableColumnTypeChange(...)`.

- [x] **2.3 — `convert_column(col, target, source=None)`**
  - Signature gains `source: int | None = None`.
  - Early guard: `if self._column_types[col].kind == "custom": return False`.
  - Allowed targets become `("number", "string", "bool", "enum", "column")`;
    keep `"custom"` out.
  - For `"column"`: require `source` is an int, in range, and `!= col`, else
    return `False`; keep cell values as strings (no rewrite) and set
    `ColumnType("column", source=source)`.
  - Idempotency: when the current kind already equals the target, return `True`
    early — **except** for `"column"` where a differing `source` must still
    re-point the type.
  - Existing `number`/`bool`/`enum`/`string` behavior unchanged.

- [x] **2.4 — `handle_event` passes `source` through**
  - In the `column_type_change` branch (~line 1238), call
    `self.convert_column(change.col, change.target, change.source)` and build the
    returned `TableColumnTypeChange(change.col, change.target, ok, ..., source=change.source)`.

- [x] **2.5 — Tests**
  - `convert_column(col, "column", source=1)` sets
    `{"kind": "column", "source": 1}` and keeps cell text; rejects
    `source=None`, out-of-range, and `source == col`.
  - `convert_column(col, "custom")` returns `False` (no mutation).
  - A `"custom"` column refuses `convert_column(..., "number")`.
  - Re-pointing a `column` source (same kind, different source) updates `source`.
  - `handle_event("column_type_change", {"value": {"col": 0, "type": "column",
    "source": 1}})` returns `TableColumnTypeChange` with `source == 1` and pushes
    the grid.

## Validation

```
uv run pytest py/tests/viz/test_table_types.py -q
```

## Notes

- The "current kind is `custom`" guard runs before the idempotency check so a
  custom column can never be switched.
- `"column"` conversion intentionally does not rewrite cells (parity with
  `"enum"`, which keeps string values).
