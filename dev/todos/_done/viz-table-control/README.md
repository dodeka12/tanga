# Viz Table Control — Overview

**Created:** 2026-08-30 | **Status:** Done | **Branch:** `feat/table-control`

## Goal

Add a tabular-data entry control — `Table` (panel/attached, via `add_table`) and
`TableView` (layout, via `views.py`) — to the interactive control system. The
backend defines the column count/headers and the initial rows; the browser
renders an editable grid (Tabulator) in which the user can edit any cell and
optionally add rows and/or columns. Every mutation is streamed back to the
backend over WebSocket as a fine-grained event, and the backend registers
separate async handlers for cell edits, row additions, and column additions.

## Architecture (short)

- **Library.** Tabulator 6.5.2 (MIT) from CDN, loaded exactly like the existing
  optional CDN libs (`marked`, `katex`, `html2canvas`): a pinned
  `tabulator-tables@6.5.2` in `viewer.html`'s `document.write` loader, guarded
  by `typeof Tabulator !== 'undefined'`, with a `/tabulator/` case in the
  optional-dependency error detector. Dark `tabulator_midnight` theme.
- **Python is the source of truth.** A `Table` dataclass holds `columns`
  (headers; count = column count) and `rows` (row-major strings) plus
  `allow_add_rows` / `allow_add_columns` flags and three handlers. Serialization
  is centralized in `_serialize_one_control`, so `controls_define` (panel +
  attached + banner) and `view_layout` both pick it up.
- **Events are per-cell / per-row / per-column.** Three new inbound message
  types carry only the mutated data, dispatched to the `ControlHandlerRegistry`
  under `cid` (`on_cell_change`) and `__row_add__{cid}` / `__column_add__{cid}`
  (the same prefix convention as slider `on_press` / `on_release`).
- **Backend-driven refresh** reuses the existing `control_update` channel: the
  table's `_controlRegistry` `apply(value)` calls Tabulator
  `setColumns`/`setData` in place.

## Canonical wire contract (fixed up front; both sides implement against this)

### Control definition (`controls_define.controls[]`)

```json
{
  "id": "tbl",
  "kind": "table",
  "label": "Data",
  "columns": ["x", "y", "z"],
  "rows": [["1", "2", "3"], ["4", "5", "6"]],
  "allow_add_rows": true,
  "allow_add_columns": true
}
```

- `columns` is a list of header strings; its length is the column count.
- `rows` is a row-major list of string lists (all cells are strings; the backend
  coerces numbers with `str`).
- `allow_add_rows` / `allow_add_columns` are always booleans (default `true`);
  `tooltip` is omitted when empty (as with other controls).

### Events (client → server, new)

```json
{ "type": "control:cell_change", "control_id": "tbl", "row": 2, "col": 1, "value": "42" }
{ "type": "control:row_add", "control_id": "tbl", "row": 3, "values": ["", "", ""] }
{ "type": "control:column_add", "control_id": "tbl", "col": 3, "header": "D", "values": ["", ""] }
```

- `row` / `col` are zero-based.
- `control:cell_change` carries only the changed cell; `control:row_add` /
  `control:column_add` carry the full new row/column contents (empty strings
  unless the UI prefills).

### Backend-driven refresh (`control_update`, server → client)

```json
{ "type": "control_update", "scene": "", "id": "tbl",
  "value": { "columns": ["x", "y", "z"], "rows": [["1", "2", "3"]] } }
```

### Handler registry keys

| Handler | Registry key | Payload (first arg) |
|---------|--------------|---------------------|
| `on_cell_change` | `cid` | `TableCellChange(row, col, value)` |
| `on_row_add` | `__row_add__{cid}` | `TableRowAdd(row, values)` |
| `on_column_add` | `__column_add__{cid}` | `TableColumnAdd(col, header, values)` |

Handlers are async `(value, event: ControlEvent) -> None`, matching the existing
`Handler` alias.

### Tabulator mapping (frontend-only, fixed)

- Column `i` → Tabulator field `c{i}`; data rows are objects `{c0, c1, …}`.
- Columns get `editor: "input"`; table uses `height: "220px"`,
  `layout: "fitColumns"`.
- CDN: `dist/css/tabulator_midnight.min.css` + `dist/js/tabulator.min.js`
  (UMD → global `Tabulator`), pinned at `tabulator-tables@6.5.2`.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-table-model.md](./01-python-table-model.md) | `_controls.py`: event dataclasses, `Table` dataclass, serialization, value helpers (+ tests) |
| 2 | [02-python-table-view.md](./02-python-table-view.md) | `views.py`: `TableView`, `set_control_view_value`, exports (+ tests) |
| 3 | [03-visualizer-api.md](./03-visualizer-api.md) | `add_table` / `_add_scene_table`, `_scene_handle` forwarding, `__init__.py` exports (+ tests) |
| 4 | [04-server-dispatch.md](./04-server-dispatch.md) | `server.py` routing + `_dispatch_control_event` branches + `test_table.py` |
| 5 | [05-frontend-cdn.md](./05-frontend-cdn.md) | `viewer.html`: Tabulator CDN CSS/JS + error detector |
| 6 | [06-frontend-table-factory.md](./06-frontend-table-factory.md) | `controls-panel.js` `createTable` + `table-view.js` + `build.js` wiring |
| 7 | [07-example.md](./07-example.md) | `table_data.py` example + regenerate example docs |
| 8 | [08-docs-changelog.md](./08-docs-changelog.md) | Docs (`controls.md`) + changelog |

## Testing as you go

- **Python:** `uv run pytest py/tests/viz/test_controls.py py/tests/viz/test_views.py
  py/tests/viz/test_table.py py/tests/viz/test_entry_points.py -q`.
- **JS/DOM** (`controls-panel.js`, `views/table-view.js`, `viewer.html`): manual
  viewer smoke; the repo has no DOM test harness.
- **Docs:** `uv run mkdocs build --strict`.

## Guiding decisions / no-refactor rule

- The wire contract above is **fixed now**; later phases implement *against* it
  and never change it.
- **Tabulator (MIT)** is the rendering library (confirmed). The Python model,
  serialization, and dispatch are library-agnostic — the Tabulator mapping lives
  only in `createTable`.
- Table cell values are **strings** on the wire; the backend coerces as needed.
- Row/column additions are **user-driven** (the "+ Row" / "+ Column" buttons),
  gated by `allow_add_rows` / `allow_add_columns`.

## Non-goals

- No CSV/Excel import/export, clipboard, formulas, sorting/filtering UI, or
  per-column typing — the table is a data-entry surface, not a spreadsheet.
- No standalone-HTML export support for controls (export is scene-only today;
  controls render only in the live WebSocket viewer).
- No row/column *deletion* or reordering.
