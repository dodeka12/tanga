# viz-table-enum-columns — Overview

**Created:** 2026-09-07 | **Status:** Done | **Branch:** `fix/misc`

## Goal

Extend the editable `Table`/`TableView` column-type system with two new kinds:

1. **`column`** — an enum whose allowed values are the de-duped values of
   another column (e.g. a pupil-preferences column whose dropdown is the pupil
   names from the first column). Selectable from the header context menu via a
   submenu that picks the source column.
2. **`custom`** — a backend-only enum whose values are supplied by a registered
   handler every time a cell in the column enters edit mode. It cannot be
   selected from the frontend, and once set the frontend cannot change the
   column's type.

## Architecture (short)

- **Model/authority** — `py/pytanga/viz/_controls.py` (`ColumnType`, `Table`,
  `_resolve_column_type`, `convert_column`, `handle_event`/`parse_table_event`).
- **Dispatch** — `py/pytanga/viz/server.py` (`_EVENT_MSG_MAP`) and
  `py/pytanga/viz/_layout.py` (`dispatch_control_event`); a new targeted
  `enum_options` reply reuses `Transport.send_to_browser`.
- **Frontend** — `py/pytanga/viz/templates/controls/table.js`,
  `py/pytanga/viz/templates/controls-panel.js`,
  `py/pytanga/viz/templates/viewer.js`,
  `py/pytanga/viz/templates/themes/controls/table.css`.

## Fixed contract (decided up front)

### Column type wire forms (additions)

| `kind` | Wire form | Meaning |
|--------|-----------|---------|
| `column` | `{"kind": "column", "source": <int>}` | dropdown = de-duped (insertion-order, empty strings skipped) values of the column at zero-based `source` |
| `custom` | `{"kind": "custom"}` | dropdown populated on edit by the `enum_options` handler |

Existing kinds are unchanged: `number` (+ optional `format`), `string`, `bool`,
`enum` (+ `values`).

### `ColumnType` (backend)

- New field `source: int | None = None`; meaningful only for `kind == "column"`.
- `_resolve_column_type` accepts dict `{"kind": "column", "source": <int>}`,
  dict `{"kind": "custom"}`, and string `"custom"`.

### `column_type_change` payload (frontend → backend)

- Gains an optional `source` (int), meaningful only for `type == "column"`.
- `TableColumnTypeChange` gains `source: int | None = None`.
- `convert_column(col, target, source=None)`: `"column"` is a valid target
  (requires a valid in-range source `!= col`, keeps cell values); `"custom"` is
  never a valid target; a column whose current kind is `"custom"` cannot be
  converted.

### Custom-enum handler API (backend)

```python
TableEnumOptionsRequest(col: int, row: int | None, current: str)
EnumOptionsHandler = Callable[[TableEnumOptionsRequest, ControlEvent],
                              Awaitable[list[str] | tuple | None]]

TableView(..., enum_options=handler)   # also Table(..., enum_options=handler)
```

- `enum_options` is a plain (non-`on_*`) field, so it is **not** auto-registered
  as an `(id, event)` handler and is **not** serialized.
- `Table.enum_options_values(request, event) -> list[str]` invokes the handler
  (or returns `[]` when unset) and stringifies the result.

### Custom-enum request/response (wire)

- Frontend sends the existing `event` envelope with event name `enum_options`
  and `data = {"value": {"col", "row", "request_id"}}`
  (i.e. `control:enum_options` after `_EVENT_MSG_MAP`).
- Backend replies to the requesting browser only, via
  `Transport.send_to_browser`:

```json
{"type": "enum_options", "id": "<cid>", "request_id": <id>, "values": ["...", ...]}
```

- The reply is applied by `applyEnumOptions(id, requestId, values)` in the
  frontend registry (mirrors `applyControlValue`).

## Decisions (confirmed)

- Kind names: `"column"` (context-menu label "From column…") and `"custom"`.
- `column` stores the source by zero-based **index** (consistent with all other
  `col` fields); it shifts on column insert/delete, and the frontend treats an
  out-of-range source as "no options".
- `column` dropdown values are computed **client-side** from the live grid so
  the list stays fresh as the source column is edited (no full-grid push
  required). The backend stores/serializes only `source`.
- `custom` options are fetched **on edit** (not pre-serialized), so the handler
  can return dynamic entities per cell/row.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-column-types.md](./01-python-column-types.md) | `ColumnType` `column`/`custom` kinds, resolve/serialize, handler API + exports |
| 2 | [02-column-conversion-and-dispatch.md](./02-column-conversion-and-dispatch.md) | `convert_column` source + custom guard, type-change payload/dispatch |
| 3 | [03-custom-enum-server-route.md](./03-custom-enum-server-route.md) | `enum_options` inbound route + targeted reply |
| 4 | [04-frontend-column-values.md](./04-frontend-column-values.md) | frontend `column` rendering + context submenu |
| 5 | [05-frontend-custom-enum-editor.md](./05-frontend-custom-enum-editor.md) | frontend `custom` edit-time options request/response |
| 6 | [06-docs-changelog.md](./06-docs-changelog.md) | docs + branch changelog |

## Testing as you go

- Python: `uv run pytest py/tests/viz/test_table_types.py -q`
- Python (broader): `uv run pytest py/tests/viz -q`
- JS syntax: `node --check <file>`
- Docs: `uv run mkdocs build --strict`

## Non-goals

- No server-side validation of enum/column/custom cell values on `cell_change`
  (the frontend dropdown restricts input, matching the existing `enum` behavior).
- No re-targeting of the `column` source when the source column is renamed —
  it stays index-based.
- No change to the existing `number`/`string`/`bool`/`enum` conversion rules.
