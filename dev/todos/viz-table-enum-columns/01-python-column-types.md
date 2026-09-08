# Phase 1 — Python column-type model: `column` + `custom` kinds

## Goal

Add the two new `ColumnType` kinds to the Python model with serialization and
hint resolution, plus the custom-enum handler type/field/helper. No behavior
changes to conversion or dispatch yet (phase 2/3).

## Files

- Edit: `py/pytanga/viz/_controls.py`
- Edit: `py/pytanga/viz/__init__.py`
- Edit: `py/tests/viz/test_table_types.py`

## Steps

- [x] **1.1 — `ColumnType` gains `source`**
  - Add `source: int | None = None` to the frozen `ColumnType` dataclass
    (`_controls.py`, ~line 590). Update the class docstring: `kind` may now be
    `"column"`/`"custom"`; `source` is the zero-based source column for `column`.

- [x] **1.2 — `ColumnType.to_dict()` emits the new fields**
  - For `kind == "column"` emit `out["source"] = self.source if self.source is not None else 0`.
  - `kind == "custom"` emits nothing beyond `{"kind": "custom"}` (default path
    already does this).

- [x] **1.3 — `_resolve_column_type` parses the new hints**
  - In the dict branch: `{"kind": "column", "source": n}` →
    `ColumnType("column", source=int(n))`; `{"kind": "custom"}` →
    `ColumnType("custom")`.
  - In the string branch: accept `"custom"` (→ `ColumnType("custom")`).
  - Keep `"column"` dict-only (a bare string has no source).

- [x] **1.4 — Custom-enum handler types**
  - Add `TableEnumOptionsRequest` dataclass (`col: int`, `row: int | None`,
    `current: str`) and `EnumOptionsHandler` type alias near the other table
    payloads (~line 155). Import `Callable`/`Awaitable` are already available.

- [x] **1.5 — `Table.enum_options` field + `enum_options_values`**
  - Add `enum_options: EnumOptionsHandler | None = field(default=None, repr=False, compare=False)`
    to `Table` (plain field, **not** `on_*`-prefixed, so `register_handlers`
    ignores it and `serialize()` never emits it).
  - Add `async def enum_options_values(self, request, event) -> list[str]` that
    returns `[str(v) for v in (await self.enum_options(request, event) or [])]`
    when set, else `[]`.

- [x] **1.6 — Exports**
  - Export `TableEnumOptionsRequest` (and `EnumOptionsHandler`) from
    `_controls.py` `__all__` if one exists; add `TableEnumOptionsRequest` to
    `py/pytanga/viz/__init__.py` imports and `__all__`.

- [x] **1.7 — Tests**
  - `ColumnType("column", source=1).to_dict() == {"kind": "column", "source": 1}`.
  - `ColumnType("custom").to_dict() == {"kind": "custom"}`.
  - `_resolve_column_type({"kind": "column", "source": 1}, [])` and
    `_resolve_column_type({"kind": "custom"}, [])` and
    `_resolve_column_type("custom", [])`.
  - `Table(...).get_value()["column_types"]` serializes `column`/`custom`
    hints correctly.
  - `TableEnumOptionsRequest` fields; `enum_options_values` invokes an async
    handler, stringifies, and returns `[]` when unset.
  - `enum_options` is not in `Table(...).serialize()`.

## Validation

```
uv run pytest py/tests/viz/test_table_types.py -q
```

## Notes

- Keep `values`/`format` semantics untouched; `source` is only read for `column`.
- `enum_options_values` is the unit-testable seam phase 3 wires to the wire
  reply; it stays handler-agnostic to the transport.
