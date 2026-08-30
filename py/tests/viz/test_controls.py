# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Unit tests for pytanga.viz._controls — data model, serialization, handler registry."""

from __future__ import annotations

from pytanga.viz._controls import (
    Button,
    Checkbox,
    ColorPicker,
    ControlGroup,
    ControlHandlerRegistry,
    Dropdown,
    Slider,
    Table,
    TextArea,
    TextField,
    ValueEdit,
    _serialize_one_control,
    get_control_value,
    serialize_controls,
    set_control_value,
)

# ── Test: Slider serialization ──────────────────────────────


def test_serialize_slider() -> None:
    ctrl = Slider(
        id="pos_x",
        label="X Position",
        min=0.0,
        max=5.0,
        step=0.1,
        value=2.0,
    )
    result = _serialize_one_control(ctrl)
    assert result == {
        "id": "pos_x",
        "kind": "slider",
        "label": "X Position",
        "min": 0.0,
        "max": 5.0,
        "step": 0.1,
        "value": 2.0,
    }


# ── Test: Dropdown serialization ────────────────────────────


def test_serialize_dropdown() -> None:
    ctrl = Dropdown(
        id="mode",
        label="Mode",
        options=["Wireframe", "Solid", "Translucent"],
        value="Solid",
    )
    result = _serialize_one_control(ctrl)
    assert result == {
        "id": "mode",
        "kind": "dropdown",
        "label": "Mode",
        "options": ["Wireframe", "Solid", "Translucent"],
        "value": "Solid",
    }


# ── Test: Button serialization ──────────────────────────────


def test_serialize_button() -> None:
    ctrl = Button(id="reset_btn", label="Reset")
    result = _serialize_one_control(ctrl)
    assert result == {
        "id": "reset_btn",
        "kind": "button",
        "label": "Reset",
        "icon_only": False,
    }


# ── Test: serialize_controls builds the full JSON message ──


def test_serialize_controls_empty() -> None:
    result = serialize_controls([])
    assert result == {
        "type": "controls_define",
        "controls": [],
        "groups": [],
        "orphanControls": [],
    }


def test_serialize_controls_single_group() -> None:
    slider = Slider(id="pos_x", label="X", min=0.0, max=10.0, step=0.5, value=5.0)
    dropdown = Dropdown(id="mode", label="Mode", options=["A", "B"], value="A")
    button = Button(id="btn", label="Go")
    group = ControlGroup(
        id="main_group",
        title="Controls",
        controls=[slider, dropdown, button],
        position="bottom-right",
        collapsed=False,
    )
    result = serialize_controls([group])
    assert result["type"] == "controls_define"
    assert len(result["controls"]) == 3
    assert len(result["groups"]) == 1
    assert result["groups"][0] == {
        "id": "main_group",
        "title": "Controls",
        "controls": ["pos_x", "mode", "btn"],
        "position": "bottom-right",
        "collapsed": False,
        "parentId": None,
    }
    # Verify all three controls are present
    control_ids = {c["id"] for c in result["controls"]}
    assert control_ids == {"pos_x", "mode", "btn"}


def test_serialize_controls_multiple_groups() -> None:
    s1 = Slider(id="s1", label="S1", min=0.0, max=1.0, step=0.1, value=0.5)
    s2 = Slider(id="s2", label="S2", min=0.0, max=1.0, step=0.1, value=0.5)
    g1 = ControlGroup(id="g1", title="Group 1", controls=[s1], position="top-left")
    g2 = ControlGroup(id="g2", title="Group 2", controls=[s2], position="bottom-right")
    result = serialize_controls([g1, g2])
    assert len(result["controls"]) == 2
    assert len(result["groups"]) == 2
    assert result["groups"][0]["id"] == "g1"
    assert result["groups"][1]["id"] == "g2"


def test_serialize_controls_group_with_parent_id() -> None:
    """Groups with parentId should serialize that field correctly."""
    slider = Slider(id="s", label="S", min=0.0, max=1.0, step=0.1, value=0.5)
    group = ControlGroup(
        id="attached_group",
        title="Attached",
        controls=[slider],
        parent_id="some_sphere_id",
        collapsed=True,
    )
    result = serialize_controls([group])
    assert result["groups"][0]["parentId"] == "some_sphere_id"
    assert result["groups"][0]["collapsed"] is True


# ── Test: ControlHandlerRegistry ────────────────────────────


def test_handler_registry_register_and_get() -> None:
    registry = ControlHandlerRegistry()

    async def my_handler(value: float) -> None:
        pass

    registry.register("pos_x", my_handler)
    assert registry.get("pos_x") is my_handler
    assert registry.get("nonexistent") is None


def test_handler_registry_unregister() -> None:
    registry = ControlHandlerRegistry()

    async def my_handler(value: float) -> None:
        pass

    registry.register("pos_x", my_handler)
    registry.unregister("pos_x")
    assert registry.get("pos_x") is None
    # Unregistering again should not raise
    registry.unregister("pos_x")


def test_handler_registry_clear() -> None:
    registry = ControlHandlerRegistry()

    async def handler_a(value: float) -> None:
        pass

    async def handler_b(value: str) -> None:
        pass

    registry.register("a", handler_a)
    registry.register("b", handler_b)
    registry.clear()
    assert registry.get("a") is None
    assert registry.get("b") is None


# ── Test: new control serialization ──────────────────────────


def test_serialize_text_field() -> None:
    ctrl = TextField(id="name", label="Name", value="a", placeholder="…")
    result = _serialize_one_control(ctrl)
    assert result == {
        "id": "name",
        "kind": "text",
        "label": "Name",
        "value": "a",
        "placeholder": "…",
    }


def test_serialize_text_area() -> None:
    ctrl = TextArea(id="notes", label="Notes", value="", rows=6)
    result = _serialize_one_control(ctrl)
    assert result == {
        "id": "notes",
        "kind": "textarea",
        "label": "Notes",
        "value": "",
        "placeholder": "",
        "rows": 6,
    }


def test_serialize_color_picker() -> None:
    ctrl = ColorPicker(id="col", label="Color", value="#ff0000")
    result = _serialize_one_control(ctrl)
    assert result == {
        "id": "col",
        "kind": "color",
        "label": "Color",
        "value": "#ff0000",
    }


def test_serialize_checkbox() -> None:
    ctrl = Checkbox(id="wire", label="Wireframe", value=True)
    result = _serialize_one_control(ctrl)
    assert result == {
        "id": "wire",
        "kind": "checkbox",
        "label": "Wireframe",
        "value": True,
    }


def test_serialize_value_edit() -> None:
    ctrl = ValueEdit(
        id="zoom",
        label="Zoom",
        min=0.5,
        max=4.0,
        step=0.25,
        digits=2,
        value=1.5,
    )
    result = _serialize_one_control(ctrl)
    assert result == {
        "id": "zoom",
        "kind": "value_edit",
        "label": "Zoom",
        "min": 0.5,
        "max": 4.0,
        "step": 0.25,
        "digits": 2,
        "value": 1.5,
        "editable": True,
    }


def test_serialize_value_edit_not_editable() -> None:
    ctrl = ValueEdit(id="zoom", editable=False)
    assert _serialize_one_control(ctrl)["editable"] is False


def test_serialize_button_with_icon() -> None:
    ctrl = Button(id="reset", label="Reset", icon="material:refresh", icon_only=True)
    result = _serialize_one_control(ctrl)
    assert result == {
        "id": "reset",
        "kind": "button",
        "label": "Reset",
        "icon": "material:refresh",
        "icon_only": True,
    }


def test_serialize_button_without_icon_has_no_icon_key() -> None:
    ctrl = Button(id="reset", label="Reset")
    result = _serialize_one_control(ctrl)
    assert "icon" not in result
    assert result["icon_only"] is False


def test_serialize_control_tooltip_present_when_set() -> None:
    ctrl = Slider(id="s", label="S", tooltip="hover text")
    assert _serialize_one_control(ctrl)["tooltip"] == "hover text"


def test_serialize_control_tooltip_absent_when_empty() -> None:
    ctrl = Slider(id="s", label="S")
    assert "tooltip" not in _serialize_one_control(ctrl)


def test_serialize_group_with_icon_and_tooltip() -> None:
    slider = Slider(id="s", label="S")
    group = ControlGroup(
        id="g",
        title="Group",
        controls=[slider],
        icon="material:settings",
        tooltip="group tooltip",
    )
    result = serialize_controls([group])
    entry = result["groups"][0]
    assert entry["icon"] == "material:settings"
    assert entry["tooltip"] == "group tooltip"


# ── Test: Table control ──────────────────────────────────────


def test_serialize_table() -> None:
    ctrl = Table(
        id="tbl",
        label="Data",
        columns=["x", "y", "z"],
        rows=[["1", "2", "3"], ["4", "5", "6"]],
    )
    result = _serialize_one_control(ctrl)
    assert result == {
        "id": "tbl",
        "kind": "table",
        "label": "Data",
        "columns": ["x", "y", "z"],
        "rows": [["1", "2", "3"], ["4", "5", "6"]],
        "allow_add_rows": True,
        "allow_add_columns": True,
    }


def test_serialize_table_disallows_adds() -> None:
    ctrl = Table(id="tbl", columns=["a"], allow_add_rows=False, allow_add_columns=False)
    result = _serialize_one_control(ctrl)
    assert result["allow_add_rows"] is False
    assert result["allow_add_columns"] is False


def test_table_get_control_value() -> None:
    ctrl = Table(id="tbl", columns=["x"], rows=[["1"]])
    assert get_control_value(ctrl) == {"columns": ["x"], "rows": [["1"]]}


def test_table_set_control_value() -> None:
    ctrl = Table(id="tbl", columns=["x"], rows=[["1"]])
    set_control_value(ctrl, {"columns": ["y", "z"], "rows": [[2], [3]]})
    assert ctrl.columns == ["y", "z"]
    assert ctrl.rows == [["2"], ["3"]]
