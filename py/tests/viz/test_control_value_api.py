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
    assert pushed == [("tbl", {"columns": ["x"], "rows": [["1"]]})]

    assert view.redo() is True
    assert pushed[-1] == ("tbl", {"columns": ["x"], "rows": [["9"]]})


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
