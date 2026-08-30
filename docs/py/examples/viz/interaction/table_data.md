# An editable tabular-data control driven by the backend

**Keywords:** controls · table · tabular data · add_table · VisualizerApp

Adds a `table` control (backed by Tabulator) whose columns and initial rows
are defined by the backend.  Editing a cell, adding a row, or adding a column
each fires a distinct async handler; this app echoes the latest change into the
viewport annotation.  A "Reset table" button pushes the grid back to its initial
state via `set_control_value`.

## Run

```bash
uv run python py/examples/viz/interaction/table_data.py
```

## Source

[`viz/interaction/table_data.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/interaction/table_data.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""table_data.py — An editable tabular-data control driven by the backend.

Adds a ``table`` control (backed by Tabulator) whose columns and initial rows
are defined by the backend.  Editing a cell, adding a row, or adding a column
each fires a distinct async handler; this app echoes the latest change into the
viewport annotation.  A "Reset table" button pushes the grid back to its initial
state via ``set_control_value``.

Run with:  uv run python py/examples/viz/interaction/table_data.py

Keywords: controls, table, tabular data, add_table, VisualizerApp
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


class TableDataApp(VisualizerApp):
    """A sphere annotated by an editable data table."""

    def __init__(self) -> None:
        super().__init__(title="Table Data")
        self._columns = ["x", "y", "z"]
        self._rows = [["1", "2", "3"], ["4", "5", "6"]]

    async def init(self) -> None:
        self.viz.add(
            Sphere(Point(0.0, 0.0, 0.0), 1.0),
            entity_id="ball",
            color="#4488ff",
            opacity=0.9,
        )
        self.viz.set_annotation("Edit the table — every change is echoed here.")
        self.viz.add_table(
            "data",
            label="Data",
            columns=self._columns,
            rows=self._rows,
            tooltip="Editable data grid",
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

    async def on_cell_change(self, change: TableCellChange, _event: ControlEvent) -> None:
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
    TableDataApp().run()
````
