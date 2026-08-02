# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Unit tests for pytanga.viz._controls — data model, serialization, handler registry."""

from __future__ import annotations

import pytest
from pytanga.viz._controls import (
    Button,
    ControlGroup,
    ControlHandlerRegistry,
    Dropdown,
    Slider,
    _serialize_one_control,
    serialize_controls,
)

# ── Test: Slider serialization ──────────────────────────────


def test_serialize_slider() -> None:
    ctrl = Slider(
        id="pos_x",
        label="X Position",
        min=0.0,
        max=5.0,
        step=0.1,
        default=2.0,
    )
    result = _serialize_one_control(ctrl)
    assert result == {
        "id": "pos_x",
        "kind": "slider",
        "label": "X Position",
        "min": 0.0,
        "max": 5.0,
        "step": 0.1,
        "default": 2.0,
    }


# ── Test: Dropdown serialization ────────────────────────────


def test_serialize_dropdown() -> None:
    ctrl = Dropdown(
        id="mode",
        label="Mode",
        options=["Wireframe", "Solid", "Translucent"],
        default="Solid",
    )
    result = _serialize_one_control(ctrl)
    assert result == {
        "id": "mode",
        "kind": "dropdown",
        "label": "Mode",
        "options": ["Wireframe", "Solid", "Translucent"],
        "default": "Solid",
    }


# ── Test: Button serialization ──────────────────────────────


def test_serialize_button() -> None:
    ctrl = Button(id="reset_btn", label="Reset")
    result = _serialize_one_control(ctrl)
    assert result == {
        "id": "reset_btn",
        "kind": "button",
        "label": "Reset",
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
    slider = Slider(id="pos_x", label="X", min=0.0, max=10.0, step=0.5, default=5.0)
    dropdown = Dropdown(id="mode", label="Mode", options=["A", "B"], default="A")
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
    s1 = Slider(id="s1", label="S1", min=0.0, max=1.0, step=0.1, default=0.5)
    s2 = Slider(id="s2", label="S2", min=0.0, max=1.0, step=0.1, default=0.5)
    g1 = ControlGroup(id="g1", title="Group 1", controls=[s1], position="top-left")
    g2 = ControlGroup(id="g2", title="Group 2", controls=[s2], position="bottom-right")
    result = serialize_controls([g1, g2])
    assert len(result["controls"]) == 2
    assert len(result["groups"]) == 2
    assert result["groups"][0]["id"] == "g1"
    assert result["groups"][1]["id"] == "g2"


def test_serialize_controls_group_with_parent_id() -> None:
    """Groups with parentId should serialize that field correctly."""
    slider = Slider(id="s", label="S", min=0.0, max=1.0, step=0.1, default=0.5)
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
