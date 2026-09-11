# An editable tabular-data control driven by the backend

**Keywords:** controls · table · tabular data · TableView · VisualizerApp

Adds a declarative `TableView` (a dependency-free native grid) whose columns
and initial rows are defined by the backend.  Editing a cell, adding a row, or
adding a column each fires a distinct async handler; this app echoes the latest
change into the viewport annotation.  The "+ Row" / "+ Column" / "Reset table"
buttons drive the table from the backend via `TableView.add_row` /
`add_column` / `set_value`.

## Run

```bash
uv run python py/examples/viz/ui/controls/table_data.py
```

## Source

[`viz/ui/controls/table_data.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/ui/controls/table_data.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""table_data.py — An editable tabular-data control driven by the backend.

Adds a declarative ``TableView`` (a dependency-free native grid) whose columns
and initial rows are defined by the backend.  Editing a cell, adding a row, or
adding a column each fires a distinct async handler; this app echoes the latest
change into the viewport annotation.  The "+ Row" / "+ Column" / "Reset table"
buttons drive the table from the backend via ``TableView.add_row`` /
``add_column`` / ``set_value``.

Run with:  uv run python py/examples/viz/ui/controls/table_data.py

Keywords: controls, table, tabular data, TableView, VisualizerApp
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
    TableView,
    VisualizerApp,
)


class TableDataApp(VisualizerApp):
    """A sphere annotated by an editable data table."""

    def __init__(self) -> None:
        super().__init__(title="Table Data")
        self._columns = ["x", "y", "active", "status"]
        self._rows = [[1.5, 2.5, True, "on"], [3.5, 4.5, False, "off"]]
        self._table: TableView | None = None

    async def init(self) -> None:
        self.viz.add(
            Sphere(Point(0.0, 0.0, 0.0), 1.0),
            entity_id="ball",
            color="#4488ff",
            opacity=0.9,
        )
        self.viz.set_annotation("Edit the table — every change is echoed here.")
        self._table = TableView(
            "data",
            label="Data",
            columns=self._columns,
            rows=self._rows,
            column_types=[None, None, "bool", ["on", "off"]],
            tooltip="Editable data grid",
            on_cell_change=self.on_cell_change,
            on_row_add=self.on_row_add,
            on_column_add=self.on_column_add,
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
                                "reset",
                                label="Reset table",
                                tooltip="Restore the initial grid",
                                on_click=self.on_reset,
                            ),
                            ButtonView(
                                "add_row",
                                label="+ Row",
                                tooltip="Append a row",
                                on_click=self.on_add_row,
                            ),
                            ButtonView(
                                "add_column",
                                label="+ Column",
                                tooltip="Append a column",
                                on_click=self.on_add_column,
                            ),
                        ],
                        position="bottom-right",
                    )
                ],
            )
        )
        self.viz.flush()

    # ── handlers ────────────────────────────────────────────

    async def on_cell_change(self, change: TableCellChange, _event: ControlEvent) -> None:
        self.viz.set_annotation(f"Cell ({change.row}, {change.col}) = {change.value!r}")

    async def on_row_add(self, add: TableRowAdd, _event: ControlEvent) -> None:
        self.viz.set_annotation(f"Added row {add.row}")

    async def on_column_add(self, add: TableColumnAdd, _event: ControlEvent) -> None:
        self.viz.set_annotation(f"Added column {add.col} ({add.header!r})")

    async def on_reset(self, _value: None, _event: ControlEvent) -> None:
        self._table.set_value({"columns": self._columns, "rows": self._rows})
        self.viz.set_annotation("Table reset.")

    async def on_add_row(self, _value: None, _event: ControlEvent) -> None:
        if self._table.add_row():
            self.viz.set_annotation("Added a row.")
        else:
            self.viz.set_annotation("Could not add a row.")

    async def on_add_column(self, _value: None, _event: ControlEvent) -> None:
        header = f"C{len(self._table.columns) + 1}"
        if self._table.add_column(header):
            self.viz.set_annotation(f"Added column {header!r}.")
        else:
            self.viz.set_annotation("Could not add a column.")


if __name__ == "__main__":
    TableDataApp().run()
````
