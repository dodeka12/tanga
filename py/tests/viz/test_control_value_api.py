# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the control value-update API (``control_update``)."""

import asyncio
import json

import pytest
from pytanga.viz import ButtonView, SliderView, TableView, Visualizer
from pytanga.viz._controls import (
    Button,
    Slider,
    ValueEdit,
)
from pytanga.viz._controls import (
    set_control_value as _set_ctrl,
)


class _FakeServer:
    def __init__(self):
        self.pushed: list[str] = []

    async def push_raw(self, data: str) -> None:
        self.pushed.append(data)


def _viz() -> Visualizer:
    return Visualizer(add_default_axes=False, add_default_grid=False)


def _patch_push(viz: Visualizer, server: _FakeServer, monkeypatch) -> None:
    monkeypatch.setattr(viz, "_server", server)
    monkeypatch.setattr(viz, "_loop", object())
    monkeypatch.setattr(
        asyncio, "run_coroutine_threadsafe", lambda coro, loop: asyncio.run(coro)
    )


def _messages(server: _FakeServer) -> list[dict]:
    return [json.loads(d) for d in server.pushed]


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


# ── Visualizer.set_control_value ────────────────────────────


def test_set_control_value_slider_mutates_and_pushes(monkeypatch) -> None:
    viz = _viz()
    viz.add_slider("radius", min=0, max=5, value=2.0)
    server = _FakeServer()
    _patch_push(viz, server, monkeypatch)

    viz.set_control_value("radius", 3.5)

    assert viz._scenes[""]._controls["radius"].value == 3.5
    assert _messages(server) == [
        {"type": "control_update", "scene": "", "id": "radius", "value": 3.5},
    ]


def test_set_control_value_dropdown_coerces_to_str(monkeypatch) -> None:
    viz = _viz()
    viz.add_dropdown("mode", options=["a", "b"], value="a")
    server = _FakeServer()
    _patch_push(viz, server, monkeypatch)

    viz.set_control_value("mode", "b")

    assert viz._scenes[""]._controls["mode"].value == "b"
    assert _messages(server)[-1]["value"] == "b"


def test_set_control_value_checkbox_coerces_to_bool(monkeypatch) -> None:
    viz = _viz()
    viz.add_checkbox("wire", value=False)
    server = _FakeServer()
    _patch_push(viz, server, monkeypatch)

    viz.set_control_value("wire", True)

    assert viz._scenes[""]._controls["wire"].value is True
    assert _messages(server)[-1]["value"] is True


def test_set_control_value_missing_raises() -> None:
    viz = _viz()
    with pytest.raises(KeyError):
        viz.set_control_value("nope", 1.0)


def test_set_control_value_button_raises() -> None:
    viz = _viz()
    viz.add_button("go")
    with pytest.raises(TypeError):
        viz.set_control_value("go", None)


def test_set_control_value_table_pushes_grid(monkeypatch) -> None:
    viz = _viz()
    viz.add_table("tbl", columns=["x"], rows=[["1"]])
    server = _FakeServer()
    _patch_push(viz, server, monkeypatch)

    viz.set_control_value("tbl", {"columns": ["y", "z"], "rows": [[2], [3]]})

    ctrl = viz._scenes[""]._controls["tbl"]
    assert ctrl.columns == ["y", "z"]
    assert ctrl.rows == [["2"], ["3"]]
    assert _messages(server) == [
        {
            "type": "control_update",
            "scene": "",
            "id": "tbl",
            "value": {"columns": ["y", "z"], "rows": [["2"], ["3"]]},
        },
    ]


# ── Visualizer.set_control_view_value ───────────────────────


def test_set_control_view_value_mutates_and_pushes(monkeypatch) -> None:
    viz = _viz()
    view = SliderView("s1", min=0, max=5, value=2.0)
    server = _FakeServer()
    _patch_push(viz, server, monkeypatch)

    viz.set_control_view_value(view, 4.0)

    assert view.value == 4.0
    assert _messages(server) == [
        {"type": "control_update", "scene": "", "id": "s1", "value": 4.0},
    ]


def test_set_control_view_value_button_view_raises() -> None:
    viz = _viz()
    with pytest.raises(TypeError):
        viz.set_control_view_value(ButtonView("b1"), None)


def test_set_control_view_value_table_pushes_grid(monkeypatch) -> None:
    viz = _viz()
    view = TableView("tbl", columns=["x"], rows=[["1"]])
    server = _FakeServer()
    _patch_push(viz, server, monkeypatch)

    viz.set_control_view_value(view, {"columns": ["y"], "rows": [[2]]})

    assert view.columns == ["y"]
    assert view.rows == [["2"]]
    assert _messages(server) == [
        {
            "type": "control_update",
            "scene": "",
            "id": "tbl",
            "value": {"columns": ["y"], "rows": [["2"]]},
        },
    ]


# ── Visualizer.update_control routes value= ─────────────────


def test_update_control_value_routes_in_place(monkeypatch) -> None:
    viz = _viz()
    viz.add_slider("s", min=0, max=10, value=1.0)
    server = _FakeServer()
    _patch_push(viz, server, monkeypatch)

    viz.update_control("s", value=5.5)

    assert viz._scenes[""]._controls["s"].value == 5.5
    msgs = _messages(server)
    assert len(msgs) == 1
    assert msgs[0]["type"] == "control_update"
    assert msgs[0]["id"] == "s"
    assert msgs[0]["value"] == 5.5


def test_update_control_other_fields_redefines(monkeypatch) -> None:
    viz = _viz()
    viz.add_slider("s", min=0, max=10, value=1.0)
    server = _FakeServer()
    _patch_push(viz, server, monkeypatch)

    viz.update_control("s", max=20.0)

    assert viz._scenes[""]._controls["s"].max == 20.0
    assert _messages(server)[-1]["type"] == "controls_define"


# ── Table undo/redo API ─────────────────────────────────────


def test_undo_table_mutates_and_pushes(monkeypatch) -> None:
    viz = _viz()
    viz.add_table("tbl", columns=["x"], rows=[["1"]])
    viz._resolve_control("tbl").control.set_cell(0, 0, "9")
    server = _FakeServer()
    _patch_push(viz, server, monkeypatch)

    assert viz.undo_table("tbl") is True

    assert viz.get_control("tbl") == {"columns": ["x"], "rows": [["1"]]}
    assert _messages(server) == [
        {
            "type": "control_update",
            "scene": "",
            "id": "tbl",
            "value": {"columns": ["x"], "rows": [["1"]]},
        },
    ]


def test_undo_table_empty_history_returns_false(monkeypatch) -> None:
    viz = _viz()
    viz.add_table("tbl", columns=["x"], rows=[["1"]])
    server = _FakeServer()
    _patch_push(viz, server, monkeypatch)

    assert viz.undo_table("tbl") is False
    assert server.pushed == []


def test_redo_table_reapplies_after_undo(monkeypatch) -> None:
    viz = _viz()
    viz.add_table("tbl", columns=["x"], rows=[["1"]])
    viz._resolve_control("tbl").control.set_cell(0, 0, "9")
    server = _FakeServer()
    _patch_push(viz, server, monkeypatch)

    viz.undo_table("tbl")
    assert viz.redo_table("tbl") is True
    assert viz.get_control("tbl") == {"columns": ["x"], "rows": [["9"]]}
    assert _messages(server)[-1]["value"] == {"columns": ["x"], "rows": [["9"]]}


def test_can_undo_redo_table_reflect_state() -> None:
    viz = _viz()
    viz.add_table("tbl", columns=["x"], rows=[["1"]])
    assert viz.can_undo_table("tbl") is False
    viz._resolve_control("tbl").control.set_cell(0, 0, "9")
    assert viz.can_undo_table("tbl") is True
    assert viz.can_redo_table("tbl") is False
    viz.undo_table("tbl")
    assert viz.can_redo_table("tbl") is True


def test_scene_handle_undo_table_routes(monkeypatch) -> None:
    viz = _viz()
    handle = viz.scene("detail")
    handle.add_table("tbl", columns=["x"], rows=[["1"]])
    viz._resolve_control("tbl").control.set_cell(0, 0, "9")
    server = _FakeServer()
    _patch_push(viz, server, monkeypatch)

    assert handle.undo_table("tbl") is True
    assert viz.get_control("tbl") == {"columns": ["x"], "rows": [["1"]]}
    assert _messages(server)[-1]["scene"] == "detail"


def test_table_view_undo_redo_operate_on_control() -> None:
    view = TableView("tbl", columns=["x"], rows=[["1"]])
    view.control.set_cell(0, 0, "9")
    assert view.can_undo is True
    assert view.undo() is True
    assert view.control.rows == [["1"]]
    assert view.redo() is True
    assert view.control.rows == [["9"]]


def test_max_history_flows_through_add_table_and_table_view() -> None:
    viz = _viz()
    viz.add_table("tbl", columns=["x"], max_history=5)
    assert viz._resolve_control("tbl").control.max_history == 5

    view = TableView("tv", columns=["x"], max_history=7)
    assert view.control.max_history == 7
