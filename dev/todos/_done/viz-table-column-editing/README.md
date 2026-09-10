# Table Column Editing — Overview

**Created:** 2026-09-06 | **Status:** Done | **Branch:** `fix/examples`

## Goal

Add four capabilities to the native `TableView`:

1. **Editable column titles** — double-click a header cell to rename it, gated
   by a backend flag (default **on**).
2. **Number format strings** — each `number` column carries a Python
   `str.format` template (e.g. `"{:.2f}m"`, `"EUR {:03d}"`), settable/changeable
   at runtime and persisted in the saved JSON.
3. **Sort icons** — larger, and directly clickable to toggle sort, without
   growing the header row height.
4. **Column type change via context menu** — right-click a header to *propose* a
   different type; the backend applies (or rejects) it via a conversion
   algorithm, with an optional custom handler that can call the base handler and
   use its `bool` return (e.g. to show a warning banner).

## Architecture (short)

- **Model + serialization**: `py/pytanga/viz/_controls.py` — `ColumnType`
  (gains `format`), `Table` (gains `rename_column`, `convert_column`,
  `set_column_format`, `on_column_title_change`, `on_column_type_change`), and
  the table event dataclasses.
- **View/API layer**: `py/pytanga/viz/views.py` — `TableView` exposes the same
  methods + `editable_titles`, and `control_to_view` forwards the new handlers.
- **Exports**: `py/pytanga/viz/__init__.py` — the new payload dataclasses.
- **Event routing**: `py/pytanga/viz/server.py` (`_EVENT_MSG_MAP`).
- **Frontend**: `py/pytanga/viz/templates/controls/table.js` (header render,
  title editor, sort arrow, context menu), `controls-panel.js`
  (`_CONTROL_EVENTS`), `themes/controls/table.css` (sort arrow + menu styling).

## Fixed contract (decided up front)

### Column type wire form (extended)

`ColumnType` gains an optional `format` field, meaningful for `number` columns
only:

```json
{"kind": "number", "format": "{:.2f}m"}
{"kind": "string"}
{"kind": "bool"}
{"kind": "enum", "values": ["on", "off"]}
```

The `format` is a Python `str.format` template applied to the numeric value via
`fmt.format(value)`: `"{:.2f}m".format(3.5) == "3.50m"`,
`"EUR {:03d}".format(42) == "EUR 042"`. It is stored in the JSON file for free,
because `to_dict`/`from_dict` already round-trip `column_types`
(`ColumnType.to_dict` emits `format`; `_resolve_column_type` parses it back).

### New client → server events

| short event name | message | payload |
|---|---|---|
| `column_title_change` | `control:column_title_change` | `{col, title}` |
| `column_type_change` | `control:column_type_change` | `{col, type}` (type ∈ `number`/`string`/`bool`/`enum`) |

### New server → handler payloads

```python
@dataclass
class TableColumnTitleChange:
    col: int
    title: str

@dataclass
class TableColumnTypeChange:
    col: int
    target: str            # "number" | "string" | "bool" | "enum"
    ok: bool               # base convert_column() return value
    column_type: ColumnType | None   # resulting type, or None when not applied
```

### New API surface

- `TableView(..., editable_titles=True, on_column_title_change=None, on_column_type_change=None)`.
- `Table` + `TableView` methods (mutate the model, record undo history, and the
  `TableView` variants push the full grid):
  - `rename_column(col, title) -> bool`
  - `convert_column(col, target) -> bool`
  - `set_column_format(col, fmt) -> bool`

### Column conversion rules (base `convert_column(col, target) -> bool`)

`target` ∈ `{"number", "string", "bool", "enum"}`. If `target` equals the
current kind → `True` (idempotent). Otherwise convert every cell in the column
and fail the whole proposal (`False`, no mutation) if any cell cannot convert:

- → `string`: `str(v)` for every cell (always succeeds).
- → `number`: bool → `1`/`0`; number → keep; string → parse (int/float); else
  fail.
- → `bool`: bool → keep; number → `0`→`False`, `1`→`True` (any other value
  fails); string → `"true"`/`"1"`→`True`, `"false"`/`"0"`→`False` (else fail).
- → `enum`: distinct non-empty string values of the column; only when
  `0 < len(distinct) < 20` (otherwise fail).

On success: record undo, replace the column's cell values, set the resolved
column type (converting *to* `number` starts with `format=None`), re-resolve
types, `_save()`, and — for the `column_type_change` event path — push the full
grid. On failure the model is untouched and nothing is pushed.

## Decisions (confirmed)

- **Format string = Python `str.format` template** (user-confirmed): applied via
  `fmt.format(value)`; a single value is substituted using standard
  `str.format`/`{:spec}` syntax.
- **Formatting is applied on the backend at serialization** (`_serialize_cells`),
  so the wire carries the formatted string; the raw number stays in the model.
- **Editing a formatted number cell** parses the entered text back to a number
  (accepting a plain number, or the formatted form by stripping the template's
  literal text); an unparseable edit is rejected.
- **Title edits follow the `cell_change` pattern**: the frontend applies the
  title locally and sends `column_title_change`; the backend mutates the model
  + records history (no full-grid push, so the inline editor isn't torn down).
- **Type changes are backend-driven**: the context menu only *proposes*; the
  backend converts and pushes the full grid on success.
- **Sort becomes an arrow-only action** so the header title is free for
  double-click rename; the header cell itself no longer toggles sort.
- **`on_column_type_change` is the custom-handler seam**: it receives
  `TableColumnTypeChange` (with `ok` = the base `convert_column` return), so a
  custom handler can call the base method itself and, using its `bool`, show a
  warning banner on rejection.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-number-format-string.md](./01-number-format-string.md) | `ColumnType.format` + serialization + `set_column_format` + frontend display |
| 2 | [02-editable-column-titles.md](./02-editable-column-titles.md) | `editable_titles` + `column_title_change` + frontend header editor |
| 3 | [03-sort-icon-sizes.md](./03-sort-icon-sizes.md) | larger, directly-clickable sort arrow (CSS + frontend) |
| 4 | [04-column-type-conversion.md](./04-column-type-conversion.md) | `convert_column` + `column_type_change` + context menu + handler |
| 5 | [05-docs-changelog.md](./05-docs-changelog.md) | Docs, example, changelog |

## Testing as you go

- Python: `uv run pytest py/tests/viz/ -q`
- Lint: `uv run ruff check py/pytanga/viz/ py/examples/viz/ui/controls/table_editing.py`
- JS: `node --check py/pytanga/viz/templates/controls/table.js py/pytanga/viz/templates/controls-panel.js`
- JS unit: `node --test 'dev/src/js-tests/*.test.mjs'`
- Docs: `uv run mkdocs build --strict`
- Example docs: `uv run python tools/generate-example-docs.py --check`

## Non-goals

- Per-cell formats (format is per-column only).
- Formatting for non-`number` columns.
- Persisting the active cell, sort state UI beyond what already exists, or a
  full table redesign.
- Drag-to-reorder columns or multi-column type changes.
- A server-driven list of allowed types beyond the four fixed kinds.

