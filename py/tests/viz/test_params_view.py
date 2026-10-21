# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for :class:`ParamsView` (dict + dataclass modes)."""

from __future__ import annotations

from dataclasses import dataclass, field

from pytanga.viz import (
    CheckboxUI,
    DropdownUI,
    ParamsView,
    SliderUI,
    param_ui,
)


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
