# An editable table with spreadsheet-style keyboard editing

**Keywords:** controls · table · tabular data · add_table · cell editing · keyboard navigation · row delete · undo · redo

Adds a `table` control (backed by Tabulator) and echoes every cell edit, row
add, column add, and row delete into the viewport annotation, so the handler
payloads can be inspected.  Double-click a cell to edit it; Tab / Shift+Tab move
between cells, Enter moves to the next row, Tab past the last cell appends a
row, and dragging across cells selects rows that can be deleted with the
"− Selected" button.  Ctrl+Z / Ctrl+Shift+Z / Ctrl+Y undo and redo edits, and
the "Undo" / "Redo" buttons drive the same backend API.  A table `on_change`
handler echoes the full table whenever undo/redo changes many cells at once.

## Run

```bash
uv run python py/examples/viz/ui/controls/table_editing.py
```

## Source

[`viz/ui/controls/table_editing.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/ui/controls/table_editing.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""table_editing.py — An editable table with spreadsheet-style keyboard editing.

Adds a ``table`` control (backed by Tabulator) and echoes every cell edit, row
add, column add, and row delete into the viewport annotation, so the handler
payloads can be inspected.  Double-click a cell to edit it; Tab / Shift+Tab move
between cells, Enter moves to the next row, Tab past the last cell appends a
row, and dragging across cells selects rows that can be deleted with the
"− Selected" button.  Ctrl+Z / Ctrl+Shift+Z / Ctrl+Y undo and redo edits, and
the "Undo" / "Redo" buttons drive the same backend API.  A table `on_change`
handler echoes the full table whenever undo/redo changes many cells at once.

Run with:  uv run python py/examples/viz/ui/controls/table_editing.py

Keywords: controls, table, tabular data, add_table, cell editing, keyboard navigation, row delete, undo, redo
"""

from __future__ import annotations

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ControlEvent,
    TableCellChange,
    TableColumnAdd,
    TableRowAdd,
    TableRowsDelete,
    VisualizerApp,
)


class TableEditingApp(VisualizerApp):
    """A table whose edits are echoed back, exercising keyboard navigation."""

    def __init__(self) -> None:
        super().__init__(title="Table Editing")
        self._columns = ["x", "y", "z"]
        self._rows = [
            ["1", "2", "3"],
            ["4", "5", "6"],
            ["7", "8", "9"],
        ]

    async def init(self) -> None:
        self.viz.add(
            Sphere(Point(0.0, 0.0, 0.0), 1.0),
            entity_id="ball",
            color="#4488ff",
            opacity=0.9,
        )
        self.viz.set_annotation(
            "Double-click to edit · Tab / Shift+Tab move between cells · Enter to the next row · "
            "Ctrl+Z undo · Ctrl+Shift+Z / Ctrl+Y redo · drag cells, then − Selected deletes."
        )
        self.viz.add_table(
            "data",
            label="Data",
            columns=self._columns,
            rows=self._rows,
            max_history=100,
            tooltip="Editable data grid (keyboard friendly)",
            on_cell_change=self.on_cell_change,
            on_row_add=self.on_row_add,
            on_column_add=self.on_column_add,
            on_row_delete=self.on_row_delete,
            on_change=self.on_change,
        )
        self.viz.add_button(
            "undo",
            label="Undo",
            tooltip="Undo the last table edit (Ctrl+Z)",
            on_click=self.on_undo,
        )
        self.viz.add_button(
            "redo",
            label="Redo",
            tooltip="Redo the last undone edit (Ctrl+Shift+Z)",
            on_click=self.on_redo,
        )
        self.viz.add_button(
            "reset",
            label="Reset table",
            tooltip="Restore the initial grid",
            on_click=self.on_reset,
        )
        self.viz.flush()

    # ── handlers ────────────────────────────────────────────

    async def on_cell_change(
        self, change: TableCellChange, _event: ControlEvent
    ) -> None:
        self.viz.set_annotation(f"Cell ({change.row}, {change.col}) = {change.value!r}")

    async def on_row_add(self, add: TableRowAdd, _event: ControlEvent) -> None:
        self.viz.set_annotation(f"Added row {add.row}")

    async def on_column_add(self, add: TableColumnAdd, _event: ControlEvent) -> None:
        self.viz.set_annotation(f"Added column {add.col} ({add.header!r})")

    async def on_row_delete(
        self, delete: TableRowsDelete, _event: ControlEvent
    ) -> None:
        self.viz.set_annotation(f"Deleted rows {delete.rows}")

    async def on_change(self, value: dict, _event: ControlEvent) -> None:
        rows = value.get("rows", [])
        self.viz.set_annotation(f"Table changed ({len(rows)} row(s)) — undo/redo.")

    async def on_undo(self, _value: None, _event: ControlEvent) -> None:
        if self.viz.undo_table("data"):
            self.viz.set_annotation("Undid the last table edit.")
        else:
            self.viz.set_annotation("Nothing to undo.")

    async def on_redo(self, _value: None, _event: ControlEvent) -> None:
        if self.viz.redo_table("data"):
            self.viz.set_annotation("Redid the last table edit.")
        else:
            self.viz.set_annotation("Nothing to redo.")

    async def on_reset(self, _value: None, _event: ControlEvent) -> None:
        self.viz.set_control_value(
            "data", {"columns": self._columns, "rows": self._rows}
        )
        self.viz.set_annotation("Table reset.")


if __name__ == "__main__":
    TableEditingApp().run()
````
