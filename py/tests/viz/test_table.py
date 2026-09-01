# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the table control dispatch (``control:cell_change`` etc.)."""

import pytest

from pytanga.viz import Visualizer
from pytanga.viz._controls import (
    TableCellChange,
    TableColumnAdd,
    TableRowAdd,
    TableRowsDelete,
)


def _viz() -> Visualizer:
    return Visualizer(add_default_axes=False, add_default_grid=False)


@pytest.mark.anyio
async def test_dispatch_cell_change() -> None:
    viz = _viz()
    calls = []

    async def _on_cell(change, event):
        calls.append(change)

    viz.add_table("tbl", columns=["x", "y"], rows=[["1", "2"]], on_cell_change=_on_cell)
    await viz._dispatch_control_event(
        "control:cell_change", {"control_id": "tbl", "row": 1, "col": 0, "value": "42"}
    )

    assert len(calls) == 1
    assert calls[0] == TableCellChange(row=1, col=0, value="42")


@pytest.mark.anyio
async def test_dispatch_row_add() -> None:
    viz = _viz()
    calls = []

    async def _on_row(add, event):
        calls.append(add)

    viz.add_table("tbl", columns=["x", "y"], on_row_add=_on_row)
    await viz._dispatch_control_event(
        "control:row_add", {"control_id": "tbl", "row": 2, "values": ["", ""]}
    )

    assert len(calls) == 1
    assert calls[0] == TableRowAdd(row=2, values=["", ""])


@pytest.mark.anyio
async def test_dispatch_column_add() -> None:
    viz = _viz()
    calls = []

    async def _on_col(add, event):
        calls.append(add)

    viz.add_table("tbl", columns=["x"], rows=[["1"]], on_column_add=_on_col)
    await viz._dispatch_control_event(
        "control:column_add",
        {"control_id": "tbl", "col": 1, "header": "y", "values": [""]},
    )

    assert len(calls) == 1
    assert calls[0] == TableColumnAdd(col=1, header="y", values=[""])


@pytest.mark.anyio
async def test_dispatch_unknown_id_is_noop() -> None:
    viz = _viz()
    await viz._dispatch_control_event(
        "control:cell_change", {"control_id": "nope", "row": 0, "col": 0, "value": "x"}
    )
    await viz._dispatch_control_event(
        "control:row_add", {"control_id": "nope", "row": 0, "values": []}
    )
    await viz._dispatch_control_event(
        "control:column_add",
        {"control_id": "nope", "col": 0, "header": "", "values": []},
    )


def test_set_layout_registers_table_handlers() -> None:
    from pytanga.viz.views import TableView

    viz = _viz()

    async def _on_cell(change, event):
        pass

    async def _on_row(add, event):
        pass

    async def _on_col(add, event):
        pass

    async def _on_del(delete, event):
        pass

    viz.set_layout(
        TableView(
            "tbl",
            columns=["x"],
            rows=[["1"]],
            on_cell_change=_on_cell,
            on_row_add=_on_row,
            on_column_add=_on_col,
            on_row_delete=_on_del,
        )
    )

    assert viz._handler_registry.get("tbl", "cell_change") is _on_cell
    assert viz._handler_registry.get("tbl", "row_add") is _on_row
    assert viz._handler_registry.get("tbl", "column_add") is _on_col
    assert viz._handler_registry.get("tbl", "row_delete") is _on_del


@pytest.mark.anyio
async def test_dispatch_cell_change_nested_payload() -> None:
    """The frontend nests the table payload under ``value`` (see ``sendControlEvent``)."""
    viz = _viz()
    calls = []

    async def _on_cell(change, event):
        calls.append(change)

    viz.add_table("tbl", columns=["x", "y"], rows=[["1", "2"]], on_cell_change=_on_cell)
    await viz._dispatch_control_event(
        "control:cell_change",
        {"control_id": "tbl", "value": {"row": 1, "col": 0, "value": "42"}},
    )

    assert len(calls) == 1
    assert calls[0] == TableCellChange(row=1, col=0, value="42")


@pytest.mark.anyio
async def test_dispatch_row_add_nested_payload() -> None:
    viz = _viz()
    calls = []

    async def _on_row(add, event):
        calls.append(add)

    viz.add_table("tbl", columns=["x", "y"], on_row_add=_on_row)
    await viz._dispatch_control_event(
        "control:row_add",
        {"control_id": "tbl", "value": {"row": 2, "values": ["", ""]}},
    )

    assert len(calls) == 1
    assert calls[0] == TableRowAdd(row=2, values=["", ""])


@pytest.mark.anyio
async def test_dispatch_column_add_nested_payload() -> None:
    viz = _viz()
    calls = []

    async def _on_col(add, event):
        calls.append(add)

    viz.add_table("tbl", columns=["x"], rows=[["1"]], on_column_add=_on_col)
    await viz._dispatch_control_event(
        "control:column_add",
        {"control_id": "tbl", "value": {"col": 1, "header": "y", "values": [""]}},
    )

    assert len(calls) == 1
    assert calls[0] == TableColumnAdd(col=1, header="y", values=[""])


@pytest.mark.anyio
async def test_dispatch_row_delete_nested_payload() -> None:
    viz = _viz()
    calls = []

    async def _on_del(delete, event):
        calls.append(delete)

    viz.add_table("tbl", columns=["x", "y"], rows=[["1", "2"]], on_row_delete=_on_del)
    await viz._dispatch_control_event(
        "control:row_delete",
        {"control_id": "tbl", "value": {"rows": [1, 2]}},
    )

    assert len(calls) == 1
    assert calls[0] == TableRowsDelete(rows=[1, 2])
