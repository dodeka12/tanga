# Viz Table Undo/Redo — Overview

**Created:** 2026-09-01 | **Status:** Done | **Branch:** `fix/tabular`

## Goal

Give the editable `Table` / `TableView` grid backend-driven **undo and redo**.
The user can press **Ctrl+Z** (undo) and **Ctrl+Shift+Z** or **Ctrl+Y** (redo) in
the browser, and the backend can trigger the same operations programmatically
(`viz.undo_table(cid)` / `viz.redo_table(cid)`) so application code can wire its
own buttons. History depth is configurable, defaulting to **100**.

The **backend stays the source of truth**: every undo/redo mutates the Python
`Table` model and re-syncs the browser through the existing `control_update`
channel.

## Architecture (short)

- **History lives on the `Table` control** (`_controls.py`) — the one model shared
  by both `add_table` (panel) and `TableView` (layout), so both surfaces get the
  feature from a single implementation.
- **Snapshot-based history.** Each committed edit records a deep copy of
  `(columns, rows)` *before* the mutation. Undo/redo restores a snapshot; there
  is no per-operation inverse logic (row/column index shifts and multi-row
  delete come for free).
- **Commit granularity (not per keystroke).** Tabulator's `cellEdited` fires on
  commit (Enter / Tab / click-away / blur), so `control:cell_change` already
  arrives once per committed edit. Row/column add and row delete are discrete
  commits. One snapshot per commit.
- **Authoritative dispatch.** `_dispatch_control_event` now *also* mutates the
  resolved `Table` (recording history) before invoking the existing user
  handler. Handler signatures are unchanged.
- **Two triggers.** (1) Frontend keyboard → new `control:undo` / `control:redo`
  events round-trip to the backend; (2) backend API methods. Both end in the
  same `Table.undo()` / `Table.redo()` + `control_update` push.

## Canonical contract (fixed up front; later phases implement against this)

### `Table` model methods (`_controls.py`)

| Method | Effect |
|--------|--------|
| `set_cell(row, col, value) -> bool` | Record snapshot, set `rows[row][col]` |
| `insert_row(row, values) -> bool` | Record snapshot, insert a row |
| `insert_column(col, header, values) -> bool` | Record snapshot, insert a column |
| `delete_rows(rows) -> bool` | Record snapshot, delete rows (descending) |
| `undo() -> bool` / `redo() -> bool` | Restore previous/next snapshot |
| `clear_history() -> None` | Empty both stacks |
| `can_undo` / `can_redo` (properties) | Stack non-empty? |

- `max_history: int = 100` field on `Table`; oldest snapshot dropped past the cap.
- Mutation methods bounds-check and no-op (return `False`, no snapshot) when out
  of range. Every mutation clears the redo stack.

### Backend API

- `Visualizer.undo_table(cid) -> bool`
- `Visualizer.redo_table(cid) -> bool`
- `Visualizer.clear_table_history(cid) -> None`
- `Visualizer.can_undo_table(cid) -> bool`
- `Visualizer.can_redo_table(cid) -> bool`
- `VizSceneHandle` mirrors (`undo_table`, `redo_table`, `clear_table_history`,
  `can_undo_table`, `can_redo_table`), forwarding to `self._viz.<method>(cid)`.
- `TableView.undo() / redo() / can_undo / can_redo` delegate to `self.control`
  (model-only; browser re-sync goes through `viz.undo_table(...)`).

All resolve the control via `_resolve_control` (panel **and** layout) and push
`control_update` with `{columns, rows}` after a successful undo/redo.

### Events (client → server, new)

Sent through the unified `event` envelope (via `sendControlEvent`), so they route
through `_EVENT_MSG_MAP` (NOT the legacy `control:*` top-level tuple):

```json
{ "type": "event", "target": "tbl", "event": "undo", "data": {} }
{ "type": "event", "target": "tbl", "event": "redo", "data": {} }
```

- `_EVENT_MSG_MAP`: `"undo" → "control:undo"`, `"redo" → "control:redo"`.
- `_CONTROL_EVENTS` (frontend): `"control:undo" → "undo"`,
  `"control:redo" → "redo"`.
- No payload body beyond `control_id` / `browser_id`.

### Backend-driven refresh (unchanged channel)

```json
{ "type": "control_update", "scene": "", "id": "tbl",
  "value": { "columns": [...], "rows": [...] } }
```

### Keyboard (frontend)

- **Ctrl+Z** → undo; **Ctrl+Shift+Z** or **Ctrl+Y** → redo.
- Ignored while focus is inside the Tabulator cell-editor `<input>` (preserves
  native text undo mid-edit).
- No built-in Undo/Redo buttons; the grid renders the table only.

## Decisions (confirmed)

- Backend undo/redo, **not** Tabulator's History module (it never round-trips to
  Python and ignores column operations).
- History lives on `Table` (not a sidecar keyed by id), shared by `add_table`
  and `TableView`.
- Snapshot-per-commit, depth **100** default, configurable via `max_history`.
- `set_control_value` full-replace **clears** history (programmatic reset = new
  baseline, not an undoable step).
- Keyboard uses `Ctrl+Z` / `Ctrl+Shift+Z` / `Ctrl+Y`; no auto-generated buttons.
- `add_table` vs `TableView` are **not** unified in this plan — they already
  share the `Table` model + `createTable` frontend; the undo/redo work targets
  that shared model only.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-table-history-model.md](./01-table-history-model.md) | `Table` history + mutation methods + depth cap (`_controls.py`) |
| 2 | [02-authoritative-dispatch.md](./02-authoritative-dispatch.md) | `_dispatch_control_event` mutates the model on the 4 table events |
| 3 | [03-undo-redo-api.md](./03-undo-redo-api.md) | `Visualizer` / `VizSceneHandle` / `TableView` undo-redo API |
| 4 | [04-server-events-dispatch.md](./04-server-events-dispatch.md) | Route `undo`/`redo` events + dispatch branches |
| 5 | [05-frontend-keyboard.md](./05-frontend-keyboard.md) | `createTable` keydown → `control:undo`/`control:redo` |
| 6 | [06-example-docs-changelog.md](./06-example-docs-changelog.md) | Example + docs + changelog |

## Testing as you go

- **Python:** `uv run pytest py/tests/viz/test_controls.py py/tests/viz/test_table.py
  py/tests/viz/test_views.py py/tests/viz/test_control_value_api.py -q` (extend
  as phases add cases).
- **JS unit:** `node --test dev/src/js-tests/*.test.mjs` (extend with a
  `table-keyboard.test.mjs` for the undo/redo key mapping).
- **JS syntax:** `node --input-type=module --check py/pytanga/viz/templates/controls-panel.js`.
- **Docs:** `uv run mkdocs build --strict` (final phase).

## Non-goals

- No built-in Undo/Redo buttons in the grid (backend API + keyboard only).
- No undo of column *deletion* or column reorder (the grid has no column-delete
  UI; only the operations the UI already emits are recorded).
- No CSV/Excel/clipboard/formulas; the table remains a data-entry surface.
- No change to the `add_table` vs `TableView` entry-point duplication (separate
  refactor, out of scope here).
