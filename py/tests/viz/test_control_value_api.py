# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the control value/history API (``Control.set_value`` / ``Table`` undo/redo)."""

import pytest

from pytanga.viz import Size, TableView
from pytanga.viz._controls import Button, Slider, Table, ValueEdit
from pytanga.viz._controls import set_control_value as _set_ctrl


# ── Helper coercion ─────────────────────────────────────────


def test_helper_slider_coerces_float() -> None:
    ctrl = Slider(id="s", value=1)
    _set_ctrl(ctrl, "2.5")
    assert ctrl.value == 2.5


def test_helper_value_edit_coerces_float() -> None:
    ctrl = ValueEdit(id="v", value=1.0)
    _set_ctrl(ctrl, "2.25")
    assert ctrl.value == 2.25


def test_helper_button_raises() -> None:
    with pytest.raises(TypeError):
        _set_ctrl(Button(id="go"), None)


# ── Control.set_value / get_value ───────────────────────────


def test_control_set_value_get_value() -> None:
    s = Slider(id="s")
    s.set_value("3.5")
    assert s.get_value() == 3.5
    assert s.value == 3.5


def test_table_set_value_replaces_grid_and_clears_history() -> None:
    t = Table(id="t", columns=["x"], rows=[["1"]])
    t.set_cell(0, 0, "9")
    assert t.can_undo is True
    t.set_value({"columns": ["y"], "rows": [["2"]]})
    assert t.columns == ["y"]
    assert t.rows == [["2"]]
    assert t.can_undo is False  # set_value clears history


# ── TableView forwards history/value through its control ────


def test_table_view_undo_redo_operate_on_control() -> None:
    view = TableView("tbl", columns=["x"], rows=[["1"]])
    view.control.set_cell(0, 0, "9")
    assert view.can_undo is True
    assert view.undo() is True
    assert view.control.rows == [["1"]]
    assert view.redo() is True
    assert view.control.rows == [["9"]]


def test_table_view_max_history_flows_through() -> None:
    view = TableView("tv", columns=["x"], max_history=7)
    assert view.control.max_history == 7


def test_table_view_undo_redo_push_grid() -> None:
    view = TableView("tbl", columns=["x"], rows=[["1"]])
    pushed: list[tuple] = []
    view._push = lambda vid, value: pushed.append((vid, value))
    view.control.set_cell(0, 0, "9")

    assert view.undo() is True
    assert pushed == [("tbl", {"columns": ["x"], "rows": [["1"]], "column_types": [{"kind": "string"}]})]

    assert view.redo() is True
    assert pushed[-1] == ("tbl", {"columns": ["x"], "rows": [["9"]], "column_types": [{"kind": "string"}]})


def test_table_view_undo_empty_history_does_not_push() -> None:
    view = TableView("tbl", columns=["x"], rows=[["1"]])
    pushed: list[tuple] = []
    view._push = lambda vid, value: pushed.append((vid, value))

    assert view.undo() is False
    assert pushed == []


def test_table_view_default_min_width_scales_with_columns() -> None:
    assert TableView("a", columns=["x"]).min_width == Size.px(120)
    assert TableView("b", columns=["x", "y", "z"]).min_width == Size.px(180)
    # An explicit min_width still wins.
    assert TableView(
        "c", columns=["x", "y", "z"], min_width=Size.px(99)
    ).min_width == Size.px(99)


def test_table_view_default_preferred_size() -> None:
    view = TableView("tbl", columns=["x", "y"])
    assert view.preferred_width == Size.px(480)
    assert view.preferred_height == Size.px(320)
    # An explicit preferred still wins.
    assert TableView("tbl", preferred_height=Size.px(200)).preferred_height == Size.px(200)


def test_table_get_cell_out_of_range_raises() -> None:
    ctrl = Table(id="tbl", columns=["x"], rows=[["1"]])
    with pytest.raises(IndexError):
        ctrl.get_cell(1, 0)
    with pytest.raises(IndexError):
        ctrl.get_cell(0, 1)
    with pytest.raises(IndexError):
        ctrl.get_cell(-1, 0)


def test_table_view_get_cell_set_cell_round_trip() -> None:
    view = TableView("tbl", columns=["x", "y"], rows=[["1", "2"]])
    assert view.get_cell(0, 0) == "1"
    assert view.set_cell(0, 1, "9") is True
    assert view.get_cell(0, 1) == "9"
    assert view.control.rows == [["1", "9"]]


def test_table_view_set_cell_pushes_grid() -> None:
    view = TableView("tbl", columns=["x"], rows=[["1"]])
    pushed: list[tuple] = []
    view._push = lambda vid, value: pushed.append((vid, value))
    assert view.set_cell(0, 0, "9") is True
    assert pushed == [("tbl", {"columns": ["x"], "rows": [["9"]], "column_types": [{"kind": "string"}]})]


def test_table_view_set_cell_records_history() -> None:
    view = TableView("tbl", columns=["x"], rows=[["1"]])
    view.set_cell(0, 0, "9")
    assert view.can_undo is True
    assert view.undo() is True
    assert view.get_value()["rows"] == [["1"]]


def test_table_view_clear_history() -> None:
    view = TableView("tbl", columns=["x"], rows=[["1"]])
    view.control.set_cell(0, 0, "9")
    assert view.can_undo is True
    view.clear_history()
    assert view.can_undo is False
    assert view.can_redo is False


def test_table_view_add_delete_row_column() -> None:
    view = TableView("tbl", columns=["x", "y"], rows=[["1", "2"]])
    pushed: list[tuple] = []
    view._push = lambda vid, value: pushed.append((vid, value))

    assert view.add_row(["3", "4"]) is True
    assert view.control.rows == [["1", "2"], ["3", "4"]]

    assert view.add_column("z", ["a", "b"]) is True
    assert view.control.columns == ["x", "y", "z"]
    assert view.control.rows == [["1", "2", "a"], ["3", "4", "b"]]

    assert view.delete_row(0) is True
    assert view.control.rows == [["3", "4", "b"]]

    assert view.delete_column(0) is True
    assert view.control.columns == ["y", "z"]
    assert view.control.rows == [["4", "b"]]

    # Every mutation pushed a control_update.
    assert len(pushed) == 4
    assert pushed[-1] == (
        "tbl",
        {"columns": ["y", "z"], "rows": [["4", "b"]], "column_types": [{"kind": "string"}, {"kind": "string"}]},
    )


def test_table_view_insert_row_column() -> None:
    view = TableView("tbl", columns=["x", "y"], rows=[["1", "2"]])
    pushed: list[tuple] = []
    view._push = lambda vid, value: pushed.append((vid, value))

    assert view.insert_row(0, ["0a", "0b"]) is True
    assert view.control.rows == [["0a", "0b"], ["1", "2"]]

    assert view.insert_column(0, "z", ["za", "zb"]) is True
    assert view.control.columns == ["z", "x", "y"]
    assert view.control.rows == [["za", "0a", "0b"], ["zb", "1", "2"]]

    assert view.insert_row(5) is False  # out of range
    assert len(pushed) == 2


def test_table_view_active_cell_delegates() -> None:
    view = TableView("tbl", columns=["x"], rows=[["1"], ["2"]])
    assert view.active_cell is None
    view.control.handle_event("cell_select", {"value": {"row": 1, "col": 0}})
    assert view.active_cell == (1, 0)


def test_table_view_editable_titles_and_title_handler() -> None:
    async def handler(*_args, **_kwargs) -> None:
        """No-op title handler."""

    view = TableView("tbl", columns=["a"], rows=[["1"]], on_column_title_change=handler)
    assert view.control.editable_titles is True
    assert view.control.serialize()["editable_titles"] is True
    assert view.control.on_column_title_change is handler
    off = TableView("t2", columns=["a"], rows=[["1"]], editable_titles=False)
    assert off.control.editable_titles is False


def test_table_view_delete_out_of_range_no_push() -> None:
    view = TableView("tbl", columns=["x"], rows=[["1"]])
    pushed: list[tuple] = []
    view._push = lambda vid, value: pushed.append((vid, value))

    assert view.delete_row(5) is False
    assert view.delete_column(5) is False
    assert pushed == []
