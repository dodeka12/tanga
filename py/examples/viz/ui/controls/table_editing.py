# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""table_editing.py — Editable table: keyboard navigation, undo/redo, row delete.

Adds a declarative ``TableView`` and Undo/Redo/Reset buttons.  Undo and redo
call ``TableView.undo`` / ``TableView.redo`` (the control owns its own history).

Run with:  uv run python py/examples/viz/ui/controls/table_editing.py

Keywords: controls, table, tabular data, TableView, cell editing, keyboard navigation, row delete, undo, redo
"""

from __future__ import annotations

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ButtonView,
    ControlEvent,
    GroupView,
    SceneView,
    TableCellChange,
    TableColumnAdd,
    TableRowAdd,
    TableRowsDelete,
    TableView,
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
        self._table: TableView | None = None

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
        self._table = TableView(
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
        self.viz.set_layout(
            SceneView(
                "",
                overlay=[
                    GroupView(
                        "",
                        [
                            self._table,
                            ButtonView(
                                "undo",
                                label="Undo",
                                tooltip="Undo the last table edit (Ctrl+Z)",
                                on_click=self.on_undo,
                            ),
                            ButtonView(
                                "redo",
                                label="Redo",
                                tooltip="Redo the last undone edit (Ctrl+Shift+Z)",
                                on_click=self.on_redo,
                            ),
                            ButtonView(
                                "reset",
                                label="Reset table",
                                tooltip="Restore the initial grid",
                                on_click=self.on_reset,
                            ),
                        ],
                        position="bottom-right",
                    )
                ],
            )
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
        if self._table.undo():
            self.viz.set_annotation("Undid the last table edit.")
        else:
            self.viz.set_annotation("Nothing to undo.")

    async def on_redo(self, _value: None, _event: ControlEvent) -> None:
        if self._table.redo():
            self.viz.set_annotation("Redid the last table edit.")
        else:
            self.viz.set_annotation("Nothing to redo.")

    async def on_reset(self, _value: None, _event: ControlEvent) -> None:
        self._table.set_value({"columns": self._columns, "rows": self._rows})
        self.viz.set_annotation("Table reset.")


if __name__ == "__main__":
    TableEditingApp().run()
