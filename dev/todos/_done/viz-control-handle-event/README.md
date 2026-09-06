# Viz Control Event Handling — Overview

**Created:** 2026-09-04 | **Status:** Done | **Branch:** `feat/view-architecture`

## Goal

Move per-control-kind event handling out of the `Visualizer` "God class"
(`visualizer.py` is ~4900 lines) and onto the controls themselves, then use that
seam to add a bulk-change handler to the table.

1. Introduce a polymorphic `Control.handle_event(event, payload) -> Dispatch`
   interface so each control kind owns its own event → mutation → handler
   mapping; `Visualizer` only resolves a control, delegates, pushes, and fires.
2. Add `Table.on_change` — a handler that fires **once** with the whole table
   (`{"columns": [...], "rows": [[...]]}`) when many cells change at once, i.e.
   on undo/redo (browser Ctrl+Z and programmatic `undo_table`/`redo_table`).

After this plan, `_dispatch_control_event` no longer has a per-kind
`if msg_type == "control:..."` ladder for controls (the ~105-line table ladder +
generic tail collapse to a delegate call); that logic lives in `_controls.py`
next to the model it mutates.

## Architecture (short)

- The model already owns table mutations + undo/redo (`Table.set_cell`,
  `insert_row`, `insert_column`, `delete_rows`, `undo`, `redo`). This plan adds
  the **dispatch mapping** to the model too, so `visualizer.py` stops
  special-casing control kinds.
- `Control.handle_event` is the single seam. The generic base default covers
  `change`/`click`/`press`/`release` (pass-through, as today); `Table` overrides
  it for its six events. No per-kind overrides needed for slider/button/etc.
- `_dispatch_control_event` keeps its non-control special cases
  (`close`/`accept`/`file_browser_*`/banner/editor/`group_toggle`) and only
  delegates the actual control events to `handle_event`.
- `on_change` needs no new wire event or frontend change: undo/redo already emit
  `control:undo`/`control:redo`, and `on_change` rides the existing `"change"`
  handler channel.

## Canonical contract (fixed up front; later phases implement against this)

### `Dispatch` (`_controls.py`)

```python
@dataclass
class Dispatch:
    event: str | None = None  # (id, event) handler to fire; None → none
    value: Any = None         # value handed to that handler
    push: Any = None          # control_update value to push; None → don't push
```

### `Control.handle_event(event: str, payload: dict) -> Dispatch`

Generic default (no model mutation — behavior-preserving):

| event | returns |
|-------|---------|
| `click` | `Dispatch("click", None, None)` |
| `press` / `release` | `Dispatch(event, payload["value"], None)` |
| anything else | `Dispatch("change", payload["value"], None)` |

### `Table.handle_event` override

`table_value = {"columns": list(columns), "rows": [list(r) for r in rows]}`.
Payloads are read from `payload["value"]` (nested) with a top-level fallback to
preserve the legacy `control:*` tuple shape.

| event | mutation | returns |
|-------|----------|---------|
| `cell_change` | `set_cell(row, col, value)` | `Dispatch("cell_change", TableCellChange(...))` |
| `row_add` | `insert_row(row, values)` | `Dispatch("row_add", TableRowAdd(...))` |
| `column_add` | `insert_column(col, header, values)` | `Dispatch("column_add", TableColumnAdd(...))` |
| `row_delete` | `delete_rows(rows)` | `Dispatch("row_delete", TableRowsDelete(...))` |
| `undo` | `undo()` | success: `Dispatch("change", table_value, push=table_value)`, else `Dispatch()` |
| `redo` | `redo()` | same shape as `undo` |

### `Visualizer` delegation

```python
d = ref.control.handle_event(event, payload)
if d.push is not None:
    self._push_control_update(ref.scene, cid, d.push)
handler = self._handler_registry.get(cid, d.event) if d.event else None
if handler:
    await handler(d.value, event)   # existing try/except + logging
```

### `Table.on_change`

- New field `on_change: Handler | None = None` on `Table`.
- Registered under the `"change"` event (same channel as Slider's `on_change`),
  so undo/redo fire it via the `Dispatch("change", ...)` above.
- Payload = the full table value dict (matches `get_control_value(Table)` and
  the `control_update` push).

## Decisions (confirmed)

- Handler name `on_change` (consistent with Slider/Dropdown); payload = full
  table value dict.
- Fires on undo/redo only (dispatch **and** `undo_table`/`redo_table`).
  `set_control_value` whole-grid replace does **not** fire it (avoids a
  handler → `set_control_value` write-back loop); possible follow-up.
- `handle_event` is behavior-preserving: generic controls stay pass-through
  (no model mutation in dispatch, as today); only `Table` is authoritative.
- Non-control special cases (`close`/`accept`/`file_browser_*`/banner/editor/
  `group_toggle`) stay in `_dispatch_control_event`.
- `undo_table`/`redo_table` keep their synchronous signatures; they fire
  `on_change` by scheduling the async handler on the server loop (reusing
  `_dispatch_event`), fire-and-forget with the existing exception logging.
- No frontend change, no new wire event.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-handle-event-interface.md](./01-handle-event-interface.md) | `Dispatch` + `Control.handle_event` base default (`_controls.py`) |
| 2 | [02-table-handle-event.md](./02-table-handle-event.md) | `Table.handle_event` + `on_change` field |
| 3 | [03-visualizer-dispatch-delegation.md](./03-visualizer-dispatch-delegation.md) | `_dispatch_control_event` delegates through `handle_event` |
| 4 | [04-on-change-wiring.md](./04-on-change-wiring.md) | `TableView`/`add_table`/`VizSceneHandle`/`control_to_view` accept `on_change` |
| 5 | [05-sync-undo-redo-api.md](./05-sync-undo-redo-api.md) | `undo_table`/`redo_table` route through `handle_event` + fire `on_change` |
| 6 | [06-docs-changelog.md](./06-docs-changelog.md) | Docs + changelog |

## Testing as you go

- **Python:** `uv run pytest py/tests/viz/test_controls.py py/tests/viz/test_table.py
  py/tests/viz/test_views.py py/tests/viz/test_control_value_api.py -q` (extend
  per phase).
- **JS syntax (guard only):** `node --check py/pytanga/viz/templates/controls-panel.js`
  (no JS change expected; verify if touched).
- **Docs:** `uv run mkdocs build --strict` (final phase).

## Non-goals

- No frontend change; no new wire event.
- No per-kind overrides for slider/button/dropdown/etc. (they inherit the base
  default).
- No migration of `close`/`accept`/`file_browser_*`/banner/editor/`group_toggle`.
- No `on_change` on `set_control_value` whole-grid replace.
- No de-duplication of the `add_*`/`_add_scene_*`/`VizSceneHandle.add_*`
  facades (separate follow-up).
- No change to `banner`/`dialog`/`editor` control handling.

