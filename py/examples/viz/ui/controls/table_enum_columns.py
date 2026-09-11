# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""table_enum_columns.py — A ``TableView`` with a column-fed enum and a backend-fed enum.

Shows the two dynamic enum column types side by side in a seating-plan grid:

* ``column`` — the "seat buddy" column's dropdown lists the de-duped values of
  the "pupil" column (each pupil picks a buddy).  It is set here with
  ``{"kind": "column", "source": 0}`` and can also be (re)pointed from the
  header context menu via "From column…".
* ``custom`` — the "activity" column's dropdown is populated at edit time by a
  backend ``on_enum_options`` handler, so the offered activities can depend on
  the row.  It is backend-only: it cannot be selected or changed from the
  frontend.

Run with:  uv run python py/examples/viz/ui/controls/table_enum_columns.py

Keywords: controls, table, tabular data, TableView, column types, enum, custom enum
"""

from __future__ import annotations

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ButtonView,
    ControlEvent,
    GroupView,
    SceneView,
    TableCellChange,
    TableEnumOptionsRequest,
    TableView,
    VisualizerApp,
)


class TableEnumColumnsApp(VisualizerApp):
    """A seating-plan table demonstrating ``column`` and ``custom`` enums."""

    def __init__(self) -> None:
        super().__init__(title="Table Enum Columns")
        self._columns = ["pupil", "seat_buddy", "activity"]
        self._rows = [
            ["Alice", "Bob", "reading"],
            ["Bob", "Alice", "drawing"],
            ["Carol", "Alice", "reading"],
        ]
        # "seat_buddy" is a column-fed enum: its dropdown lists the de-duped
        # values of column 0 ("pupil").  "activity" is a backend-only custom
        # enum, populated at edit time by `on_enum_options`.
        self._column_types = [None, {"kind": "column", "source": 0}, "custom"]
        self._table: TableView | None = None

    async def init(self) -> None:
        self.viz.add(
            Sphere(Point(0.0, 0.0, 0.0), 1.0),
            entity_id="ball",
            color="#4488ff",
            opacity=0.9,
        )
        self.viz.set_annotation(
            "Double-click an 'activity' cell to fetch its options from the backend · "
            "right-click a header → 'From column…' to (re)point a column enum."
        )
        self._table = TableView(
            "data",
            label="Seating plan",
            columns=self._columns,
            rows=self._rows,
            column_types=self._column_types,
            tooltip="Column-fed and backend-fed enum columns",
            on_enum_options=self.on_enum_options,
            on_cell_change=self.on_cell_change,
        )
        self.viz.set_layout(
            SceneView(
                "",
                overlay=[
                    GroupView(
                        "Seating plan",
                        [
                            self._table,
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

    async def on_enum_options(
        self, request: TableEnumOptionsRequest, event: ControlEvent
    ) -> list[str]:
        """Return the activities offered for a cell in the ``custom`` column.

        The backend is asked afresh every time a cell enters edit mode, so the
        list can vary by row (and by ``request.current`` if needed).
        """
        activities = ["reading", "drawing", "building", "chess"]
        if request.row == 0:
            activities = ["reading", "chess"]
        elif request.row == 1:
            activities = ["drawing", "building"]
        return activities

    async def on_cell_change(
        self, change: TableCellChange, _event: ControlEvent
    ) -> None:
        self.viz.set_annotation(f"Cell ({change.row}, {change.col}) = {change.value!r}")

    async def on_reset(self, _value: None, _event: ControlEvent) -> None:
        self._table.set_value(
            {
                "columns": self._columns,
                "rows": self._rows,
                "column_types": self._column_types,
            }
        )
        self.viz.set_annotation("Table reset.")


if __name__ == "__main__":
    TableEnumColumnsApp().run()
