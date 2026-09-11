# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""table_file.py — Table auto-save: JSON load/save + CSV export.

Binds a ``TableView`` to a JSON file via ``json_path=…``: the file is loaded at
startup (if it exists) and auto-saved after every edit, so changes persist
across runs.  A button exports the current data to CSV, and another reloads the
table from the JSON file.  Edit a cell, then press "Export CSV" and inspect the
written files (``table_autosave.json`` / ``table_export.csv`` in the working
directory).

Run with:  uv run python py/examples/viz/ui/controls/table_file.py

Keywords: controls, table, tabular data, TableView, persistence, JSON, CSV, auto-save
"""

from __future__ import annotations

from pathlib import Path

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ButtonView,
    ControlEvent,
    GroupView,
    SceneView,
    TableCellChange,
    TableView,
    VisualizerApp,
)

TABLE_FILE = Path("_output/table_autosave.json")
CSV_FILE = Path("_output/table_export.csv")


class TableFileApp(VisualizerApp):
    """A table bound to a JSON file (auto-save) with CSV export + reload."""

    def __init__(self) -> None:
        super().__init__(title="Table Auto-Save")
        self._table: TableView | None = None

    async def init(self) -> None:
        self.viz.add(
            Sphere(Point(0.0, 0.0, 0.0), 1.0),
            entity_id="ball",
            color="#4488ff",
            opacity=0.9,
        )
        self.viz.set_annotation(
            f"Auto-save: {TABLE_FILE} (edits are written automatically) · "
            f"Export CSV writes {CSV_FILE}."
        )
        self._table = TableView(
            "data",
            label="Data",
            columns=["x", "y", "active", "status"],
            rows=[[1.0, 2.0, True, "on"], [3.0, 4.0, False, "off"]],
            column_types=[None, None, "bool", ["on", "off"]],
            json_path=str(TABLE_FILE),
            tooltip="Auto-saved data grid",
            on_cell_change=self.on_cell_change,
        )
        self.viz.set_layout(
            SceneView(
                "",
                overlay=[
                    GroupView(
                        "Table",
                        position="bottom-right",
                        children=[
                            self._table,
                            ButtonView(
                                "export_csv",
                                label="Export CSV",
                                tooltip=f"Write the table to {CSV_FILE}",
                                on_click=self.on_export_csv,
                            ),
                            ButtonView(
                                "reload",
                                label="Reload",
                                tooltip=f"Reload the table from {TABLE_FILE}",
                                on_click=self.on_reload,
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
        self.viz.set_annotation(
            f"Saved cell ({change.row}, {change.col}) = {change.value!r} to {TABLE_FILE}."
        )

    async def on_export_csv(self, _value: None, _event: ControlEvent) -> None:
        self._table.to_csv(str(CSV_FILE))
        self.viz.set_annotation(f"Exported table to {CSV_FILE}.")

    async def on_reload(self, _value: None, _event: ControlEvent) -> None:
        self._table.load(str(TABLE_FILE))
        self.viz.set_annotation(f"Reloaded table from {TABLE_FILE}.")


if __name__ == "__main__":
    TableFileApp().run()
