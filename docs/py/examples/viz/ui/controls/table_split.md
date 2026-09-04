# An editable data table beside a 3D scene

**Keywords:** split view · table · tabular data · TableView

A horizontal split layout: the left pane is a single `TableView` (an editable
Tabulator grid) filling its pane, and the right pane is the 3D `SceneView`.
Editing a cell, or adding a row/column, echoes the change into the scene's
annotation; a button overlaid on the scene resets the table to its initial grid.

## Run

```bash
uv run python py/examples/viz/ui/controls/table_split.py
```

## Source

[`viz/ui/controls/table_split.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/ui/controls/table_split.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""table_split.py — An editable data table beside a 3D scene.

A horizontal split layout: the left pane is a single ``TableView`` (an editable
Tabulator grid) filling its pane, and the right pane is the 3D ``SceneView``.
Editing a cell, or adding a row/column, echoes the change into the scene's
annotation; a button overlaid on the scene resets the table to its initial grid.

Run with:  uv run python py/examples/viz/ui/controls/table_split.py

Keywords: split view, table, tabular data, TableView
"""

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ButtonView,
    GroupView,
    SceneView,
    Size,
    SplitView,
    TableView,
    Visualizer,
)

viz = Visualizer(reuse_existing=False, title="Tanga — Table + Scene")

# Main scene content (the default scene, name "").
viz.add(
    Sphere(Point(0, 0, 0), radius=2), entity_id="sphere", color="#4488ff", opacity=0.3
)
viz.add(Point(1, 1, 1), color="#ff4444")

_COLUMNS = ["x", "y", "z"]
_ROWS = [["1", "2", "3"], ["4", "5", "6"]]


async def _on_cell(change, _event):
    viz.set_annotation(f"Cell ({change.row}, {change.col}) = {change.value!r}")


async def _on_row(add, _event):
    viz.set_annotation(f"Added row {add.row}")


async def _on_column(add, _event):
    viz.set_annotation(f"Added column {add.col} ({add.header!r})")


async def _on_reset(_value, _event):
    # Layout control views are updated in place via set_control_view_value.
    viz.set_control_view_value(table_view, {"columns": _COLUMNS, "rows": _ROWS})
    viz.set_annotation("Table reset.")


table_view = TableView(
    "data",
    label="Data",
    columns=_COLUMNS,
    rows=_ROWS,
    on_cell_change=_on_cell,
    on_row_add=_on_row,
    on_column_add=_on_column,
)

layout = SplitView(
    orientation="horizontal",
    sizes=[Size.percent(40), Size.percent(60)],
    children=[
        table_view,
        SceneView(
            "",
            overlay=[
                GroupView(
                    "Actions",
                    [ButtonView("btn_reset", label="Reset table", on_click=_on_reset)],
                    position="top-left",
                ),
            ],
        ),
    ],
)

viz.show(layout=layout)
print("Table + scene split view is shown at a single URL. Press Ctrl+C to exit.")
viz.wait()
````
