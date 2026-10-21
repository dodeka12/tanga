# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for :class:`ParamsView` (dict + dataclass modes)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pytanga.viz import (
    ButtonUI,
    CheckboxUI,
    ControlEvent,
    DropdownUI,
    GroupUI,
    MarkdownUI,
    ParamsView,
    RowSpec,
    SliderUI,
    ValueEditUI,
    param_ui,
)
from pytanga.viz.views import iter_control_views


def test_dict_mode_serialize() -> None:
    pv = ParamsView(
        {"radius": 2.0, "wireframe": False},
        styles={"radius": SliderUI(title="Radius", min=0.1, max=5.0)},
    )
    node = pv._serialize()
    assert node["type"] == "params_view"
    assert [r["key"] for r in node["rows"]] == ["radius", "wireframe"]
    assert node["rows"][0]["title"] == "Radius"
    assert node["rows"][0]["control"]["type"] == "slider_view"
    assert node["rows"][0]["control"]["hide_label"] is True
    assert node["rows"][1]["control"]["type"] == "checkbox_view"


@dataclass
class _Params:
    radius: float = param_ui(2.0, ui=SliderUI(title="Radius", min=0.1, max=5.0))
    wireframe: bool = param_ui(False, ui=CheckboxUI(title="Wireframe"))
    mode: str = param_ui("solid", ui=DropdownUI(title="Mode", options=["solid", "wire"]))


def test_dataclass_mode_serialize_and_value() -> None:
    pv = ParamsView(_Params())
    node = pv._serialize()
    assert [r["key"] for r in node["rows"]] == ["radius", "wireframe", "mode"]
    assert node["rows"][2]["control"]["type"] == "dropdown_view"
    assert pv.get_value() == {"radius": 2.0, "wireframe": False, "mode": "solid"}


def test_raw_field_metadata() -> None:
    @dataclass
    class Raw:
        radius: float = field(
            default=2.0,
            metadata={"param_ui": SliderUI(title="Radius", min=0.1, max=5.0)},
        )

    pv = ParamsView(Raw())
    node = pv._serialize()
    assert node["rows"][0]["title"] == "Radius"
    assert node["rows"][0]["control"]["type"] == "slider_view"


def test_inference() -> None:
    pv = ParamsView({"count": 3, "name": "x", "color": "#4488ff"})
    node = pv._serialize()
    kinds = {r["key"]: r["control"]["type"] for r in node["rows"]}
    assert kinds == {
        "count": "value_edit_view",
        "name": "text_field_view",
        "color": "color_picker_view",
    }


def test_set_value() -> None:
    pv = ParamsView({"radius": 2.0}, styles={"radius": SliderUI(min=0.1, max=5.0)})
    pv.set_value("radius", 3.0)
    assert pv.get_value() == {"radius": 3.0}


def test_on_change_receives_key_and_value() -> None:
    calls: list[tuple[Any, ControlEvent]] = []

    async def handler(state: Any, event: ControlEvent) -> None:
        calls.append((state, event))

    pv = ParamsView(
        {"radius": 2.0},
        styles={"radius": SliderUI(min=0.1, max=5.0)},
        on_change=handler,
    )
    ctrl = pv._control_views["radius"].control
    asyncio.run(ctrl.on_change(3.0, ControlEvent()))
    assert calls[0][0] == {"radius": 3.0}
    assert calls[0][1].key == "radius"
    assert calls[0][1].value == 3.0


def test_per_field_handler_overrides_shared() -> None:
    per_field_calls: list[Any] = []
    shared_calls: list[Any] = []

    async def per_field(value: Any, event: ControlEvent) -> None:
        per_field_calls.append(value)

    async def shared(state: Any, event: ControlEvent) -> None:
        shared_calls.append(state)

    pv = ParamsView(
        {"a": 1, "b": 2},
        styles={"a": ValueEditUI(on_change=per_field)},
        on_change=shared,
    )
    ctrl_a = pv._control_views["a"].control
    ctrl_b = pv._control_views["b"].control
    asyncio.run(ctrl_a.on_change(10, ControlEvent()))
    asyncio.run(ctrl_b.on_change(20, ControlEvent()))
    assert per_field_calls == [10]
    assert shared_calls == [{"a": 10, "b": 20}]
    assert pv.get_value() == {"a": 10, "b": 20}


class _Mode(Enum):
    SOLID = "solid"
    WIRE = "wire"


@dataclass
class _Inferred:
    count: int = 3
    ratio: float = 0.5
    name: str = "x"
    mode: _Mode = _Mode.SOLID


def test_dataclass_inference_uses_resolved_types() -> None:
    pv = ParamsView(_Inferred())
    node = pv._serialize()
    kinds = {r["key"]: r["control"]["type"] for r in node["rows"]}
    assert kinds == {
        "count": "value_edit_view",
        "ratio": "value_edit_view",
        "name": "text_field_view",
        "mode": "dropdown_view",
    }


def test_int_field_coerces_to_int() -> None:
    pv = ParamsView(_Inferred())
    ctrl = pv._control_views["count"].control
    asyncio.run(ctrl.on_change(3.0, ControlEvent()))
    assert pv.get_value()["count"] == 3
    assert isinstance(pv.get_value()["count"], int)


def test_enum_field_coerces_to_enum() -> None:
    pv = ParamsView(_Inferred())
    ctrl = pv._control_views["mode"].control
    asyncio.run(ctrl.on_change("wire", ControlEvent()))
    assert pv.get_value()["mode"] is _Mode.WIRE


def test_explicit_coerce_and_integer() -> None:
    pv = ParamsView(
        {"a": 2.0, "b": 2.0},
        styles={"a": SliderUI(coerce=int), "b": SliderUI(integer=True)},
    )
    asyncio.run(pv._control_views["a"].control.on_change(2.7, ControlEvent()))
    asyncio.run(pv._control_views["b"].control.on_change(2.7, ControlEvent()))
    assert pv.get_value() == {"a": 2, "b": 2}


def test_extra_rows_ordering() -> None:
    pv = ParamsView(
        {"a": 1, "b": 2},
        extra_rows=[
            RowSpec("top", MarkdownUI(title="Top"), "above", position="above"),
            RowSpec("run", ButtonUI(title="Run")),
            RowSpec("bottom", MarkdownUI(title="Bottom"), "below"),
        ],
    )
    node = pv._serialize()
    keys = [r["key"] for r in node["rows"]]
    assert keys == ["top", "a", "b", "run", "bottom"]
    assert node["rows"][0]["control"]["type"] == "markdown_view"
    assert node["rows"][3]["control"]["type"] == "button_view"


def test_extra_row_button_click() -> None:
    clicks: list[str] = []

    async def on_click(value: Any, event: ControlEvent) -> None:
        clicks.append(event.key)

    pv = ParamsView(
        {"a": 1},
        extra_rows=[RowSpec("run", ButtonUI(title="Run"), on_click=on_click)],
    )
    btn = pv._control_views["run"].control
    asyncio.run(btn.on_click(None, ControlEvent()))
    assert clicks == ["run"]


def test_set_value_updates_display_row() -> None:
    pv = ParamsView(
        {"a": 1},
        extra_rows=[RowSpec("status", MarkdownUI(title="Status"), "idle")],
    )
    pv.set_value("status", "busy")
    assert pv.get_value() == {"a": 1}
    assert pv._control_views["status"].control.value == "busy"


def test_visible_initially_hidden() -> None:
    pv = ParamsView({"a": 1}, styles={"a": ValueEditUI(visible=False)})
    assert pv._control_views["a"].control.visible is False
    assert pv._serialize()["rows"][0]["control"]["visible"] is False


def test_set_visible_delegates_to_child() -> None:
    pv = ParamsView({"radius": 2.0}, styles={"radius": SliderUI(min=0.1, max=5.0)})
    pv.set_visible("radius", False)
    assert pv._control_views["radius"].control.visible is False


def test_set_enabled_delegates_to_child() -> None:
    pv = ParamsView({"radius": 2.0}, styles={"radius": SliderUI(min=0.1, max=5.0)})
    pv.set_enabled("radius", False)
    assert pv._control_views["radius"].control.enabled is False


def test_set_title_pushes_and_updates() -> None:
    pushed: list[tuple[str, dict[str, Any]]] = []
    pv = ParamsView({"radius": 2.0}, styles={"radius": SliderUI(title="Radius")})
    pv._push_state = lambda cid, state: pushed.append((cid, state))
    pv.set_title("radius", "R")
    assert pv._serialize()["rows"][0]["title"] == "R"
    assert pushed == [(pv.id, {"row": "radius", "title": "R"})]


def test_set_options_updates_dropdown() -> None:
    pushed: list[tuple[str, dict[str, Any]]] = []
    pv = ParamsView(
        {"mode": "solid"}, styles={"mode": DropdownUI(options=["solid", "wire"])}
    )
    view = pv._control_views["mode"]
    view._push_state = lambda cid, state: pushed.append((cid, state))
    pv.set_options("mode", ["solid", "wire", "xray"])
    assert view.control.options == ["solid", "wire", "xray"]
    assert pushed == [
        (
            view.id,
            {
                "options": [
                    {"value": "solid", "label": "solid"},
                    {"value": "wire", "label": "wire"},
                    {"value": "xray", "label": "xray"},
                ]
            },
        )
    ]


@dataclass
class _Inner:
    x: float = 1.0


@dataclass
class _Outer:
    name: str = "a"
    inner: _Inner = field(default_factory=_Inner)


def test_nested_dataclass_serializes_as_group() -> None:
    pv = ParamsView(_Outer())
    node = pv._serialize()
    rows = node["rows"]
    assert [r["key"] for r in rows] == ["name", "inner"]
    assert rows[1]["title"] == ""
    control = rows[1]["control"]
    assert control["type"] == "group"
    assert control["title"] == "inner"
    nested = control["children"][0]
    assert nested["type"] == "params_view"
    assert [r["key"] for r in nested["rows"]] == ["x"]


def test_nested_group_ui_title_override() -> None:
    pv = ParamsView(_Outer(), styles={"inner": GroupUI(title="Sub", collapsed=True)})
    node = pv._serialize()
    control = node["rows"][1]["control"]
    assert control["type"] == "group"
    assert control["title"] == "Sub"
    assert control["collapsed"] is True


def test_nested_controls_register() -> None:
    pv = ParamsView(_Outer())
    ids = [v.id for v in iter_control_views(pv)]
    assert len(ids) == 2
    assert any(i.endswith(".inner.x") for i in ids)


def test_nested_change_fires_shared_with_dotted_key() -> None:
    calls: list[tuple[Any, ControlEvent]] = []

    async def shared(state: Any, event: ControlEvent) -> None:
        calls.append((state, event))

    pv = ParamsView(_Outer(), on_change=shared)
    nested_ctrl = pv._control_views["inner"].children[0]._control_views["x"].control
    asyncio.run(nested_ctrl.on_change(2.5, ControlEvent()))

    assert len(calls) == 1
    state, event = calls[0]
    assert event.key == "inner.x"
    assert event.value == 2.5
    assert isinstance(state, _Outer)
    assert state.inner.x == 2.5


def test_nested_per_field_handler_still_fires() -> None:
    per_field: list[tuple[Any, str]] = []
    shared: list[str] = []

    async def _per_field(value: Any, event: ControlEvent) -> None:
        per_field.append((value, event.key))

    async def _shared(state: Any, event: ControlEvent) -> None:
        shared.append(event.key)

    @dataclass
    class Inner2:
        x: float = param_ui(1.0, ui=SliderUI(on_change=_per_field))

    @dataclass
    class Outer2:
        inner: Inner2 = field(default_factory=Inner2)

    pv = ParamsView(Outer2(), on_change=_shared)
    nested_ctrl = pv._control_views["inner"].children[0]._control_views["x"].control
    asyncio.run(nested_ctrl.on_change(3.0, ControlEvent()))

    assert per_field == [(3.0, "inner.x")]
    assert shared == []


def test_dotted_set_value() -> None:
    pv = ParamsView(_Outer())
    pv.set_value("inner.x", 3.5)
    assert pv.instance.inner.x == 3.5
    assert pv.get_value()["inner"].x == 3.5


def test_dotted_set_visible() -> None:
    pv = ParamsView(_Outer())
    pv.set_visible("inner.x", False)
    nested_view = pv._control_views["inner"].children[0]
    assert nested_view._control_views["x"].control.visible is False


def test_set_state_rebinds_nested() -> None:
    pv = ParamsView(_Outer())
    new_outer = _Outer(name="b", inner=_Inner(x=9.0))
    pv.set_state(new_outer)
    assert pv.instance is new_outer
    assert pv.instance.inner is new_outer.inner
    nested_view = pv._control_views["inner"].children[0]
    assert nested_view.instance is new_outer.inner
    assert nested_view._control_views["x"].control.value == 9.0


def test_nested_group_extra_rows() -> None:
    pv = ParamsView(
        _Outer(),
        styles={
            "inner": GroupUI(
                extra_rows=[RowSpec("run", ButtonUI(label="Run"), position="above")]
            )
        },
    )
    group_node = pv._serialize()["rows"][1]["control"]
    assert group_node["type"] == "group"
    nested = group_node["children"][0]
    assert nested["type"] == "params_view"
    assert [r["key"] for r in nested["rows"]] == ["run", "x"]


def test_set_state_updates_without_on_change() -> None:
    calls: list[Any] = []

    async def handler(state: Any, event: ControlEvent) -> None:
        calls.append(state)

    pv = ParamsView({"a": 1, "b": 2}, on_change=handler)
    pv.set_state({"a": 10, "b": 20})
    assert pv.get_value() == {"a": 10, "b": 20}
    assert calls == []


def test_set_state_dataclass() -> None:
    pv = ParamsView(_Inferred())
    pv.set_state(_Inferred(count=5, ratio=0.8, name="y", mode=_Mode.WIRE))
    assert pv.get_value() == {"count": 5, "ratio": 0.8, "name": "y", "mode": _Mode.WIRE}
    assert pv.instance.mode is _Mode.WIRE


def test_add_remove_rows() -> None:
    pushed: list[str] = []
    pv = ParamsView({"a": 1})
    pv._push_layout = lambda: pushed.append("layout")

    pv.add("b", 2, SliderUI(min=0, max=10))
    assert [r["key"] for r in pv._serialize()["rows"]] == ["a", "b"]
    assert pv.get_value() == {"a": 1, "b": 2}
    assert pushed == ["layout"]

    pv.remove("b")
    assert [r["key"] for r in pv._serialize()["rows"]] == ["a"]
    assert pv.get_value() == {"a": 1}
    assert pushed == ["layout", "layout"]


def test_dropdown_value_label_options() -> None:
    pv = ParamsView(
        {"mode": "solid"},
        styles={"mode": DropdownUI(options=[("solid", "Solid"), ("wire", "Wireframe")])},
    )
    control = pv._serialize()["rows"][0]["control"]
    assert control["options"] == [
        {"value": "solid", "label": "Solid"},
        {"value": "wire", "label": "Wireframe"},
    ]


def test_value_edit_unit() -> None:
    pv = ParamsView({"length": 2.0}, styles={"length": ValueEditUI(unit="m")})
    control = pv._serialize()["rows"][0]["control"]
    assert control["unit"] == "m"


def test_validate_rejects_invalid() -> None:
    def _positive(value: Any) -> bool:
        return value > 0

    pv = ParamsView({"a": 1.0}, styles={"a": ValueEditUI(validate=_positive)})
    ctrl = pv._control_views["a"].control
    asyncio.run(ctrl.on_change(-5.0, ControlEvent()))
    assert pv.get_value() == {"a": 1.0}
    assert ctrl.value == 1.0


def test_tooltip_from_metadata_description() -> None:
    @dataclass
    class WithDesc:
        radius: float = field(default=2.0, metadata={"description": "Sphere radius"})

    pv = ParamsView(WithDesc())
    control = pv._serialize()["rows"][0]["control"]
    assert control["tooltip"] == "Sphere radius"


def test_title_from_name() -> None:
    pv = ParamsView({"radius_mm": 2.0}, title_from_name=True)
    assert pv._serialize()["rows"][0]["title"] == "Radius mm"


def test_dense_serializes() -> None:
    pv = ParamsView({"a": 1}, dense=True)
    assert pv._serialize()["dense"] is True


def test_button_caption_and_full_width() -> None:
    pv = ParamsView(
        {"a": 1},
        extra_rows=[
            RowSpec("run", ButtonUI(label="Compute circles"), position="above"),
            RowSpec("status", MarkdownUI(), "**Idle**"),
        ],
    )
    node = pv._serialize()
    run_row, a_row, status_row = node["rows"]
    assert run_row["full_width"] is True
    assert run_row["control"]["label"] == "Compute circles"
    assert "hide_label" not in run_row["control"]
    assert "full_width" not in a_row
    assert a_row["control"]["hide_label"] is True
    assert status_row["full_width"] is True
