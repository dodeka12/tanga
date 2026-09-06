# Editable table: column types, keyboard nav, undo/redo

**Keywords:** controls · table · tabular data · TableView · column types · cell editing · keyboard navigation · undo · redo

Adds a declarative `TableView` (a native, dependency-free grid) demonstrating
every column type — numbers (right-aligned, with a per-column `str.format`
display template), strings, booleans (an always-on checkbox), and an enum (a
dropdown of allowed values) — plus Undo/Redo/Reset and row/column add/delete
buttons in the layout.  Double-click a cell to edit it, double-click a header
to rename the column, right-click a header to propose a different column type
(a rejected switch shows a warning banner), move the active cell with the
cursor keys, sort by clicking the header arrow, and zoom the columns/rows with
the title-bar icon buttons.  Row/column insertion is relative to the selected
cell (above/below, left/right); with no selection it falls back to the
top/bottom or left/right, and delete is a no-op without a selection.

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

"""table_editing.py — Editable table: column types, keyboard nav, undo/redo.

Adds a declarative ``TableView`` (a native, dependency-free grid) demonstrating
every column type — numbers (right-aligned, with a per-column ``str.format``
display template), strings, booleans (an always-on checkbox), and an enum (a
dropdown of allowed values) — plus Undo/Redo/Reset and row/column add/delete
buttons in the layout.  Double-click a cell to edit it, double-click a header
to rename the column, right-click a header to propose a different column type
(a rejected switch shows a warning banner), move the active cell with the
cursor keys, sort by clicking the header arrow, and zoom the columns/rows with
the title-bar icon buttons.  Row/column insertion is relative to the selected
cell (above/below, left/right); with no selection it falls back to the
top/bottom or left/right, and delete is a no-op without a selection.

Run with:  uv run python py/examples/viz/ui/controls/table_editing.py

Keywords: controls, table, tabular data, TableView, column types, cell editing, keyboard navigation, undo, redo
"""

from __future__ import annotations

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ButtonView,
    ControlEvent,
    EIconMaterial,
    GroupView,
    SceneView,
    TableCellChange,
    TableColumnAdd,
    TableColumnTypeChange,
    TableRowAdd,
    TableRowsDelete,
    TableView,
    ToolbarView,
    VisualizerApp,
)


class TableEditingApp(VisualizerApp):
    """A table whose edits are echoed back, exercising keyboard navigation."""

    def __init__(self) -> None:
        super().__init__(title="Table Editing")
        self._columns = ["x", "y", "name", "active", "status"]
        self._rows = [
            [1.5, 2.5, "alpha", True, "on"],
            [3.5, 4.5, "beta", False, "off"],
            [5.5, 6.5, "gamma", True, "on"],
        ]
        self._column_types = ["number", None, "string", "bool", ["on", "off"]]
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
            "Ctrl+Z undo · Ctrl+Shift+Z / Ctrl+Y redo · add/delete rows & columns relative to the selected cell."
        )
        self._table = TableView(
            "data",
            label="Data",
            columns=self._columns,
            rows=self._rows,
            column_types=self._column_types,
            max_history=100,
            tooltip="Editable data grid (keyboard friendly)",
            on_cell_change=self.on_cell_change,
            on_row_add=self.on_row_add,
            on_column_add=self.on_column_add,
            on_row_delete=self.on_row_delete,
            on_column_type_change=self.on_column_type_change,
            on_change=self.on_change,
        )
        # A `number` column carries a Python str.format display template.
        self._table.set_column_format(0, "{:.2f} m")
        self.viz.set_layout(
            SceneView(
                "",
                overlay=[
                    GroupView(
                        "Table",
                        position="bottom-right",
                        children=[
                            self._table,
                            ToolbarView(
                                [
                                    ButtonView(
                                        "undo",
                                        label="Undo",
                                        icon=EIconMaterial.UNDO,
                                        icon_only=True,
                                        tooltip="Undo the last table edit (Ctrl+Z)",
                                        on_click=self.on_undo,
                                    ),
                                    ButtonView(
                                        "redo",
                                        label="Redo",
                                        icon=EIconMaterial.REDO,
                                        icon_only=True,
                                        tooltip="Redo the last undone edit (Ctrl+Shift+Z)",
                                        on_click=self.on_redo,
                                    ),
                                    ButtonView(
                                        "reset",
                                        label="Reset table",
                                        icon=EIconMaterial.RESTART_ALT,
                                        icon_only=True,
                                        tooltip="Restore the initial grid",
                                        on_click=self.on_reset,
                                    ),
                                    ButtonView(
                                        "add_row_above",
                                        label="+ Row Above",
                                        icon=EIconMaterial.ADD_ROW_ABOVE,
                                        icon_only=True,
                                        tooltip="Insert a row above the selected cell",
                                        on_click=self.on_add_row_above,
                                    ),
                                    ButtonView(
                                        "add_row_below",
                                        label="+ Row Below",
                                        icon=EIconMaterial.ADD_ROW_BELOW,
                                        icon_only=True,
                                        tooltip="Insert a row below the selected cell",
                                        on_click=self.on_add_row_below,
                                    ),
                                    ButtonView(
                                        "add_column_left",
                                        label="+ Column Left",
                                        icon=EIconMaterial.ADD_COLUMN_LEFT,
                                        icon_only=True,
                                        tooltip="Insert a column left of the selected cell",
                                        on_click=self.on_add_column_left,
                                    ),
                                    ButtonView(
                                        "add_column_right",
                                        label="+ Column Right",
                                        icon=EIconMaterial.ADD_COLUMN_RIGHT,
                                        icon_only=True,
                                        tooltip="Insert a column right of the selected cell",
                                        on_click=self.on_add_column_right,
                                    ),
                                    ButtonView(
                                        "del_row",
                                        label="− Row",
                                        icon=EIconMaterial.REMOVE,
                                        icon_only=True,
                                        tooltip="Delete the selected cell's row",
                                        on_click=self.on_delete_row,
                                    ),
                                    ButtonView(
                                        "del_column",
                                        label="− Column",
                                        icon=EIconMaterial.DELETE,
                                        icon_only=True,
                                        tooltip="Delete the selected cell's column",
                                        on_click=self.on_delete_column,
                                    ),
                                ],
                            ),
                        ],
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

    async def on_column_type_change(
        self, change: TableColumnTypeChange, _event: ControlEvent
    ) -> None:
        # `change.ok` is the base `convert_column` return value.
        if change.ok:
            self.viz.set_annotation(
                f"Column {change.col} converted to {change.column_type.kind!r}."
            )
        else:
            self.viz.show_banner(
                f"Column {change.col} could not be converted to {change.target!r}.",
                title="Type change not possible",
                auto_hide=False,
            )

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
        self._table.set_value(
            {
                "columns": self._columns,
                "rows": self._rows,
                "column_types": self._column_types,
            }
        )
        self.viz.set_annotation("Table reset.")

    def _row_index(self, above: bool) -> int:
        """Insert index for a new row relative to the active cell.

        Inserts at the active row (``above=True``) or just after it
        (``above=False``); falls back to the top/bottom when no cell is
        selected.
        """
        cell = self._table.active_cell
        if cell is None:
            return 0 if above else len(self._table.rows)
        return cell[0] if above else cell[0] + 1

    def _col_index(self, left: bool) -> int:
        """Insert index for a new column relative to the active cell."""
        cell = self._table.active_cell
        if cell is None:
            return 0 if left else len(self._table.columns)
        return cell[1] if left else cell[1] + 1

    async def on_add_row_above(self, _value: None, _event: ControlEvent) -> None:
        if self._table.insert_row(self._row_index(True)):
            self.viz.set_annotation("Inserted a row above the selected cell.")
        else:
            self.viz.set_annotation("Could not insert a row.")

    async def on_add_row_below(self, _value: None, _event: ControlEvent) -> None:
        if self._table.insert_row(self._row_index(False)):
            self.viz.set_annotation("Inserted a row below the selected cell.")
        else:
            self.viz.set_annotation("Could not insert a row.")

    async def on_add_column_left(self, _value: None, _event: ControlEvent) -> None:
        header = f"C{len(self._table.columns) + 1}"
        if self._table.insert_column(self._col_index(True), header):
            self.viz.set_annotation(f"Inserted column {header!r} left of the selected cell.")
        else:
            self.viz.set_annotation("Could not insert a column.")

    async def on_add_column_right(self, _value: None, _event: ControlEvent) -> None:
        header = f"C{len(self._table.columns) + 1}"
        if self._table.insert_column(self._col_index(False), header):
            self.viz.set_annotation(f"Inserted column {header!r} right of the selected cell.")
        else:
            self.viz.set_annotation("Could not insert a column.")

    async def on_delete_row(self, _value: None, _event: ControlEvent) -> None:
        cell = self._table.active_cell
        if cell is None:
            self.viz.set_annotation("Select a cell first to delete its row.")
            return
        if self._table.delete_row(cell[0]):
            self.viz.set_annotation(f"Deleted row {cell[0]}.")
        else:
            self.viz.set_annotation(f"Could not delete row {cell[0]}.")

    async def on_delete_column(self, _value: None, _event: ControlEvent) -> None:
        cell = self._table.active_cell
        if cell is None:
            self.viz.set_annotation("Select a cell first to delete its column.")
            return
        if self._table.delete_column(cell[1]):
            self.viz.set_annotation(f"Deleted column {cell[1]}.")
        else:
            self.viz.set_annotation(f"Could not delete column {cell[1]}.")


if __name__ == "__main__":
    TableEditingApp().run()
````
