# Bug: `TableView` cell edits are dispatched with a nested payload (row/col lost)

**Created:** 2026-09-01 | **Status:** Reported | **Branch:** `seating-plan-app`

A standalone bug description for the pytanga repo. Documents why editing a cell
in a `TableView` / `add_table` grid corrupts the data — the real `row`/`col` are
lost and the whole payload is stringified into column 0 — and requests the
standard Tabulator keyboard navigation (Tab / Enter) be wired up.

## Metadata

- Package: `tanga-py` (import name `pytanga`), version **1.14.1**.
- Module: `pytanga/viz/templates/controls-panel.js` (`createTable`,
  `sendControlEvent`) · `pytanga/viz/templates/events.js` (event envelope) ·
  `pytanga/viz/server.py` (event parsing) · `pytanga/viz/visualizer.py`
  (`_dispatch_control_event`).
- Frontend grid library: Tabulator **6.5.2** (loaded from CDN).
- Severity: high — the editable grid cannot be used at all; every edit corrupts
  the first cell instead of the edited one.

## Summary

When a cell is edited, the frontend reports the change through the unified event
envelope with the table payload nested under `value`
(`data.value = {row, col, value}`). The backend dispatcher, however, reads
`row`, `col` and `value` as **top-level** keys of the payload, so it always sees
`row=0`, `col=0` and `value=<the whole {row, col, value} dict>`. The handler
therefore receives `TableCellChange(row=0, col=0, value="{'row': …, 'col': …,
'value': …}")` — the real coordinates are lost and the stringified dict lands in
column 0.

## Steps to reproduce

```python
from pytanga.viz import VisualizerApp


class Repro(VisualizerApp):
    async def init(self):
        self.viz.add_table(
            "data",
            label="Data",
            columns=["x", "y", "z"],
            rows=[["1", "2", "3"]],
            on_cell_change=self.on_cell_change,
        )
        self.viz.flush()

    async def on_cell_change(self, change, _event):
        print(f"row={change.row} col={change.col} value={change.value!r}")


Repro().run()
```

1. Run the script.
2. In the browser, edit the cell in the first row (e.g. change `1` to `42`).
3. Observe the printed handler arguments.

### Expected

```
row=0 col=0 value='42'
```

### Actual

```
row=0 col=0 value="{'row': 0, 'col': 0, 'value': '42'}"
```

The coordinates are wrong (they fall back to `0`) and the value is the
stringified payload rather than the typed text.

## Root cause

1. `createTable` reports a completed edit (`controls-panel.js:928`) by passing
   the whole change as the `value` argument to `sendControlEvent`:

   ```js
   table.on('cellEdited', (cell) => {
       sendControlEvent('control:cell_change', ctrl.id, {
           row: cell.getRow().getPosition(),
           col: colOf(cell.getColumn().getField()),
           value: String(cell.getValue()),
       });
   });
   ```

2. `sendControlEvent` (`controls-panel.js:1016`) always wraps its `value`
   argument in a `data.value` key, and `sendEvent` (`events.js:22`) sends it as
   `{ type:'event', target, event, data }`. The wire message is therefore:

   ```json
   {"type":"event","target":"data","event":"cell_change","data":{"value":{"row":0,"col":0,"value":"42"}}}
   ```

3. The server (`server.py:871`) extracts `event_data = data["data"]` — i.e.
   `{value: {row, col, value}}` — adds `control_id`, and routes it to
   `_dispatch_control_event`.

4. `_dispatch_control_event` (`visualizer.py:3572`) reads the payload flat:

   ```python
   TableCellChange(
       row=int(payload.get("row", 0)),      # no top-level "row" → 0
       col=int(payload.get("col", 0)),      # no top-level "col" → 0
       value=str(payload.get("value", "")), # the nested {row, col, value} dict
   )
   ```

   Because the table payload sits under `payload["value"]` rather than at the
   top level, `row`/`col` default to `0` and `value` becomes `str({...})`.

The same mismatch affects `row_add` (`payload.get("row")` /
`payload.get("values")`) and `column_add` (`payload.get("col")` /
`payload.get("header")` / `payload.get("values")`); their payloads are also
nested under `value`.

## Suggested fix

Preferably unwrap the nested payload in `_dispatch_control_event` (one place,
keeps the frontend envelope uniform):

```python
if msg_type == "control:cell_change":
    v = payload.get("value") if isinstance(payload.get("value"), dict) else {}
    await handler(
        TableCellChange(
            row=int(v.get("row", 0)),
            col=int(v.get("col", 0)),
            value=str(v.get("value", "")),
        ),
        event,
    )
```

…and analogously for `row_add` / `column_add`. Alternatively, the frontend could
send the table events with a flat payload (skip the `data.value` wrapper) — but
that special-cases the envelope.

## Feature requests (standard Tabulator keyboard navigation)

The editable grid is backed by Tabulator 6.5.2, which already supports these
navigation behaviours natively, but pytanga's `createTable` constructs the
Tabulator instance with a minimal config (no `keybindings`, no `tabEndNewRow`).
Please wire up the standard spreadsheet-style editing keyboard flow:

- **Tab → next cell** — pressing Tab commits the current cell and moves focus to
  the next editable cell in the row; Shift+Tab moves to the previous cell.
- **Enter → next row** — pressing Enter commits the current cell and moves focus
  to the same column in the next row.
- **Enter / Tab at the end → new row** — when focus is on the last cell of the
  last row, pressing Enter (or Tab) appends a new blank row and focuses its
  first cell, so the user can keep typing without leaving the keyboard or
  reaching for the "+ Row" button.

Mechanism: Tabulator exposes this via its `keybindings` option (Tab/Shift+Tab
are the default `navNext`/`navPrev` bindings) and the `tabEndNewRow` option
(Tab past the last cell appends a row); Enter-to-next-row and
Enter-at-end-append require an explicit `keybindings` mapping for the Enter key.
pytanga's `createTable` should set these so both `add_table` and `TableView` get
spreadsheet-style editing out of the box.

## Workaround

None applied downstream — the `seating-plan-app` repo is waiting for this
upstream fix; see `dev/todos/seating-plan-app/05-visualizer-app.md`.

