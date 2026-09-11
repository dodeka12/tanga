# Native Editable Table — Overview

**Created:** 2026-09-05 | **Status:** Done | **Branch:** `fix/examples`

## Goal

Replace the CDN-loaded Tabulator grid (the source of the double-click-edit bug on
the last column/row inside auto-sized `GroupView` overlays) with a small,
dependency-free, plain-DOM editable table. It keeps the same backend API and dark
look, and adds:

- optional **column titles** (header row) and **row numbers** (leading index column);
- a single **active cell** (border highlight) that is clicked into place and moved
  with the cursor keys, and is the indicator for **row and column deletion**;
- **frontend-only sorting** by column (backend row order unchanged);
- **backend undo/redo** (already present — extended to cover column deletion).

## Architecture (short)

- **Mostly frontend** — plus small backend additions (display/sort/delete flags, a
  `column_delete` event/mutation, and a table control API). The `Table`/`TableView`
  model, existing events, and `control_update` re-sync stay unchanged.
- **One `<table>` with a sticky header** and a scrollable container — no virtual
  DOM, no separate header/body, so the sub-pixel `fitColumns` overflow bug cannot
  happen.
- **Proportional column fit that fills naturally.** Column widths are relative
  weights; on container resize they are re-distributed over the full available
  width (clamped to a minimum), so the table fills the container edge-to-edge.
  User drags update the weights, so resizes survive re-fits.
- **Scrollbars.** The container scrolls both axes (`overflow: auto`, thin
  `.tanga-scroll` styling); the header is sticky so it stays put during vertical
  scroll, and the table keeps a `min-width` (sum of column minimums) so many or
  narrow columns overflow into a horizontal scrollbar.
- **Active cell** (not multi-range selection): a single highlighted cell; click to
  set it, arrow keys move it. Deleting a row/column uses that cell's row/column.
- **Display-only sort.** Clicking a header reorders the rendered `<tr>` elements;
  every `control:*` event carries the **original** data row index (a per-row
  `data-original-index` attribute maps display position → original row).
- **Themeable.** The grid is styled purely with `--tanga-*` CSS custom properties
  (dark/light/pastel + custom themes). No hardcoded colors, no Tabulator
  stylesheet — so theme switching restyles the table like every other control.
- **Unified view + event contract.** The frontend `TableView` extends `ControlView`
  (which extends the base `View`), so it fits any `SplitView`/`StackView`/`GroupView`
  /overlay, and declares default min/max/preferred sizes via the base `View`
  setters. Every action goes through the single `sendEvent(id, event, data)`
  envelope (`events.js`) and the one `_controlRegistry` — per
  `docs/dev/architecture/viz-controls-and-interactions.md`.

## Fixed contract (up front; later phases implement against this)

### Wire flags (Python → browser)

| Field | Type | Default | Meaning |
|-------|------|---------|---------|
| `show_column_titles` | bool | `true` | Render the header row (column titles). |
| `show_row_numbers` | bool | `false` | Render a leading frozen row-number column (1-based display position). |
| `allow_delete_columns` | bool | `true` | Gate the "− Column" button. |
| `sortable` | bool | `true` | Enable header-click sorting (frontend-only). |

- Added to `Table._fields()` (panel path) and threaded through `TableView.__init__`
  + `build.js`/`table-view.js` (layout path).

### Events

| Event | Payload | Notes |
|-------|---------|-------|
| `control:cell_change` | `{row, col, value}` | original row index |
| `control:row_add` | `{row, values}` | appended at end of original data |
| `control:column_add` | `{col, header, values}` | |
| `control:row_delete` | `{rows: [original indexes]}` | unchanged |
| `control:column_delete` | `{col}` | **new** |
| `control:undo` / `control:redo` | — | unchanged; covers column delete |

- `column_delete` mirrors `row_delete` end-to-end: a `TableColumnDelete` payload
  dataclass, a `Table.delete_column(col)` mutation (bounds-checked, snapshot for
  undo), an `on_column_delete` handler, and dispatch through `_EVENT_MSG_MAP`.

### Backend control API (`TableView`)

Full programmatic control, backend-authoritative (all mutations go through the
`Table` model so undo/redo stays correct; browser re-sync reuses `control_update`):

| Method | Effect |
|--------|--------|
| `get_value() -> {columns, rows}` | Read the whole grid. |
| `set_value({columns, rows})` | Replace the grid (pushes `control_update`). |
| `get_cell(row, col) -> str` | Read one cell. |
| `set_cell(row, col, value)` | Set one cell (records history, pushes). |
| `undo()` / `redo()` | Restore previous/next snapshot. |
| `clear_history()` | Empty both stacks. |
| `can_undo` / `can_redo` | Read-only stack state. |
| `sortable` flag | Enable/disable header sorting. |

### Frontend view + communication

- `views/table-view.js` `TableView` extends `ControlView` → base `View`, so it is a
  first-class layout node in any container.
- `TableView` declares default **min** and **preferred** sizes via the base `View`
  setters (`minWidth`/`minHeight`/`preferredWidth`/`preferredHeight`); `maxWidth`/
  `maxHeight` stay `null` unless the Python model sets them. `build.js` still
  overrides with the serialized Python values.
- All user actions use the single client→server envelope
  `sendEvent(id, event, data)` (`events.js`, via `sendControlEvent`), registered in
  the one `(id, event)` handler registry and the one `_controlRegistry.apply`.
- New events (`column_delete`) map through `server.py::_EVENT_MSG_MAP` — no new
  transport.

### Width fit helper (pure, unit-testable)

`fitColumnWidths(available, weights, opts) -> number[]`:
- `available = container.clientWidth` minus the row-number column width when
  present (the table fills naturally — no reserved gap).
- `width[i] = clamp(available * weight[i] / Σweight, MIN, ∞)`, `MIN = 24`.
- The table keeps a `min-width` equal to Σ `MIN` so it overflows into a horizontal
  scrollbar instead of squeezing columns below `MIN`.

### Theme contract (CSS tokens)

The table's appearance is driven by a small set of new design tokens, defined in
`base.css` (dark defaults) and overridden in `light/tokens.css` / `pastel/tokens.css`:

`--tanga-table-header-bg`, `--tanga-table-header-fg`, `--tanga-table-border`,
`--tanga-table-cell-bg`, `--tanga-table-row-alt-bg`, `--tanga-table-row-hover-bg`,
`--tanga-table-active-border`, `--tanga-table-sort-arrow`,
`--tanga-table-row-number-bg`, `--tanga-table-row-number-fg`.

`controls/table.css` stays registered in `themes/registry.json` `components` (it
already is) and must only reference these tokens — so the drift guard in
`test_themes.py` continues to pass and theme switching needs no extra JS.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-model-flags-column-delete.md](./01-python-model-flags-column-delete.md) | Backend: flags + `column_delete` event/mutation/dispatch/handler. |
| 2 | [02-backend-control-api.md](./02-backend-control-api.md) | Backend control API: get/set cell, get/set value, clear history, sortable. |
| 3 | [03-native-grid-render-fit.md](./03-native-grid-render-fit.md) | Rewrite `createTable` to a native grid with proportional fill + scrollbars. |
| 4 | [04-cell-editing-keyboard-apply-undo.md](./04-cell-editing-keyboard-apply-undo.md) | Double-click editing, keyboard nav, +Row/+Column, registry apply, undo/redo. |
| 5 | [05-active-cell-delete.md](./05-active-cell-delete.md) | Active cell (border + cursor keys) and row/column deletion. |
| 6 | [06-frontend-sorting.md](./06-frontend-sorting.md) | Header-click sorting (display-only reorder). |
| 7 | [07-remove-tabulator-cdn.md](./07-remove-tabulator-cdn.md) | Drop the Tabulator CDN + fallback + stale references. |
| 8 | [08-docs-changelog.md](./08-docs-changelog.md) | Update docs + changelog. |

## Testing as you go

- Python: `uv run pytest py/tests/viz/test_table.py py/tests/viz/test_controls.py py/tests/viz/test_control_value_api.py`
- JS: `node --test 'dev/src/js-tests/*.test.mjs'`
- Smoke: `uv run python py/examples/viz/ui/controls/table_editing.py`,
  `table_split.py`, `table_data.py` — edit every cell incl. last column/row in the
  group overlay; move the active cell with arrows; delete the active row/column;
  undo/redo; sort; toggle titles/row numbers.

## Non-goals

- No `Visualizer`-specific table methods — all control is via the `TableView`
  view + `Table` data class, matching every other control's structure.
- No data-backed row labels (row titles are display row numbers only).
- No persisted sort (backend row order never changes).
- No multi-range/multi-cell selection (single active cell only).
- No column reordering, cell copy/paste, or export.
