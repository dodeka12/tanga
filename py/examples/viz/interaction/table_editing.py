# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""table_editing.py — An editable table with spreadsheet-style keyboard navigation.

Adds a ``table`` control (backed by Tabulator) and echoes every cell edit, row
add, and column add into the viewport annotation, so the exact
``TableCellChange(row, col, value)`` payload can be inspected.  The grid is wired
for spreadsheet-style editing: Tab / Shift+Tab move between cells, Enter moves to
the same column in the next row, and Tab past the last cell appends a new row.

Run with:  uv run python py/examples/viz/interaction/table_editing.py

Keywords: controls, table, tabular data, add_table, cell editing, keyboard navigation
"""

from __future__ import annotations

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ControlEvent,
    TableCellChange,
    TableColumnAdd,
    TableRowAdd,
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
            "Tab / Shift+Tab to move between cells · Enter to the next row · "
            "Tab past the last cell adds a row."
        )
        self.viz.add_table(
            "data",
            label="Data",
            columns=self._columns,
            rows=self._rows,
            tooltip="Editable data grid (keyboard friendly)",
            on_cell_change=self.on_cell_change,
            on_row_add=self.on_row_add,
            on_column_add=self.on_column_add,
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

    async def on_reset(self, _value: None, _event: ControlEvent) -> None:
        self.viz.set_control_value(
            "data", {"columns": self._columns, "rows": self._rows}
        )
        self.viz.set_annotation("Table reset.")


if __name__ == "__main__":
    TableEditingApp().run()
