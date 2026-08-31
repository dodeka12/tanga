# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for interaction config serialization, deserialization, and utilities."""

import pytest
from pytanga.viz._interaction import (
    ClickEvent,
    DragEvent,
    InteractionConfig,
    InteractionEventType,
    InteractionHandlerRegistry,
    InteractionTrigger,
    ModifierKey,
    MouseButton,
    ScrollEvent,
    _coalesce_drag_events,
    _parse_event,
    apply_delta_transform,
    extract_camera_directions,
)
from pytanga.geometry import Direction, Point


class TestInteractionTrigger:
    def test_to_dict_minimal(self):
        t = InteractionTrigger(event_type=InteractionEventType.CLICK)
        d = t.to_dict()
        assert d == {"event_type": "click", "modifiers": []}

    def test_to_dict_full(self):
        t = InteractionTrigger(
            event_type=InteractionEventType.DRAG,
            mouse_button=MouseButton.LEFT,
            modifiers=frozenset({ModifierKey.CTRL, ModifierKey.SHIFT}),
        )
        d = t.to_dict()
        assert d["event_type"] == "drag"
        assert d["mouse_button"] == "left"
        assert set(d["modifiers"]) == {"ctrl", "shift"}

    def test_from_dict(self):
        d = {"event_type": "drag", "mouse_button": "right", "modifiers": ["alt"]}
        t = InteractionTrigger.from_dict(d)
        assert t.event_type == InteractionEventType.DRAG
        assert t.mouse_button == MouseButton.RIGHT
        assert t.modifiers == frozenset({ModifierKey.ALT})

    def test_from_dict_no_button(self):
        d = {"event_type": "scroll", "modifiers": []}
        t = InteractionTrigger.from_dict(d)
        assert t.mouse_button is None


class TestInteractionConfig:
    def test_to_dict(self):
        ic = InteractionConfig(
            enabled=True,
            triggers=[InteractionTrigger(event_type=InteractionEventType.DRAG)],
            throttle_ms=30,
        )
        d = ic.to_dict()
        assert d["enabled"] is True
        assert len(d["triggers"]) == 1
        assert d["throttle_ms"] == 30

    def test_to_dict_disabled(self):
        ic = InteractionConfig(enabled=False)
        d = ic.to_dict()
        assert d["enabled"] is False
        assert d["triggers"] == []
        assert d["throttle_ms"] == 50

    def test_to_dict_hover_fields(self):
        ic = InteractionConfig(
            enabled=True,
            hover_emissive="#ffff44",
            hover_scale=1.5,
            hover_opacity=0.5,
        )
        d = ic.to_dict()
        assert d["hover_emissive"] == "#ffff44"
        assert d["hover_scale"] == 1.5
        assert d["hover_opacity"] == 0.5

    def test_to_dict_hover_fields_omitted_when_none(self):
        ic = InteractionConfig(enabled=True)
        d = ic.to_dict()
        assert "hover_emissive" not in d
        assert "hover_scale" not in d
        assert "hover_opacity" not in d


class TestParseEvent:
    def test_parse_click(self):
        data = {
            "type": "interaction:click",
            "event_type": "click",
            "object_id": "abc",
            "mouse_button": "left",
            "modifiers": ["ctrl"],
            "screen_position": [100, 200],
            "world_position": [1.0, 2.0, 3.0],
            "world_normal": [0.0, 0.0, 1.0],
        }
        event = _parse_event(data)
        assert isinstance(event, ClickEvent)
        assert event.object_id == "abc"
        assert event.event_type == InteractionEventType.CLICK
        assert event.mouse_button == MouseButton.LEFT
        assert event.modifiers == frozenset({ModifierKey.CTRL})
        assert event.screen_position == (100, 200)
        assert event.world_position == (1.0, 2.0, 3.0)
        assert event.world_normal == (0.0, 0.0, 1.0)

    def test_parse_drag_move(self):
        data = {
            "type": "interaction:drag_move",
            "event_type": "drag_move",
            "object_id": "x",
            "mouse_button": "left",
            "modifiers": [],
            "screen_position": [300, 400],
            "delta_pixels": [5, -2],
            "world_position": [1.0, 2.0, 3.0],
            "delta_transform": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
        }
        event = _parse_event(data)
        assert isinstance(event, DragEvent)
        assert event.event_type == InteractionEventType.DRAG_MOVE
        assert event.delta_pixels == (5, -2)
        assert len(event.delta_transform) == 16

    def test_parse_drag_move_ray_fields(self):
        data = {
            "type": "interaction:drag_start",
            "event_type": "drag_start",
            "object_id": "x",
            "ray_origin": [1.0, 2.0, 3.0],
            "ray_direction": [0.0, 0.0, 1.0],
        }
        event = _parse_event(data)
        assert isinstance(event, DragEvent)
        assert event.ray_origin == Point(1.0, 2.0, 3.0)
        assert event.ray_direction == Direction(0.0, 0.0, 1.0)

    def test_parse_drag_move_ray_defaults(self):
        data = {
            "type": "interaction:drag_move",
            "event_type": "drag_move",
            "object_id": "x",
        }
        event = _parse_event(data)
        assert isinstance(event, DragEvent)
        assert event.ray_origin == Point(0.0, 0.0, 0.0)
        assert event.ray_direction == Direction(0.0, 0.0, 0.0)

    def test_parse_scroll(self):
        data = {
            "type": "interaction:scroll",
            "event_type": "scroll",
            "object_id": "s",
            "modifiers": ["shift"],
            "screen_position": [400, 300],
            "delta_xy": [0, -120],
        }
        event = _parse_event(data)
        assert isinstance(event, ScrollEvent)
        assert event.event_type == InteractionEventType.SCROLL
        assert event.delta_xy == (0, -120)

    def test_parse_unknown_event_type(self):
        with pytest.raises(ValueError):
            _parse_event({"type": "interaction:foo", "event_type": "bogus"})

    def test_parse_missing_event_type(self):
        with pytest.raises(ValueError):
            _parse_event({"type": "interaction:click"})


class TestCoalesceDragEvents:
    def test_single_event(self):
        e = DragEvent(delta_pixels=(1, 0), screen_position=(100, 200))
        result = _coalesce_drag_events([e])
        assert result.delta_pixels == (1, 0)

    def test_two_events(self):
        e1 = DragEvent(delta_pixels=(1, 0), screen_position=(100, 200))
        e2 = DragEvent(delta_pixels=(2, 3), screen_position=(105, 208))
        result = _coalesce_drag_events([e1, e2])
        assert result.delta_pixels == (3, 3)
        assert result.screen_position == (105, 208)

    def test_modifiers_from_last(self):
        e1 = DragEvent(
            delta_pixels=(1, 0),
            modifiers=frozenset({ModifierKey.CTRL}),
        )
        e2 = DragEvent(
            delta_pixels=(2, 3),
            modifiers=frozenset({ModifierKey.SHIFT}),
        )
        result = _coalesce_drag_events([e1, e2])
        assert result.modifiers == frozenset({ModifierKey.SHIFT})

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            _coalesce_drag_events([])

    def test_preserves_ray(self):
        e1 = DragEvent(
            delta_pixels=(1, 0),
            ray_origin=Point(1.0, 2.0, 3.0),
            ray_direction=Direction(0.0, 0.0, 1.0),
        )
        e2 = DragEvent(delta_pixels=(2, 3))
        result = _coalesce_drag_events([e1, e2])
        assert result.ray_origin == Point(1.0, 2.0, 3.0)
        assert result.ray_direction == Direction(0.0, 0.0, 1.0)


class TestHandlerRegistry:
    @pytest.mark.anyio
    async def test_register_and_dispatch(self):
        results = []

        async def handler(event):
            results.append(event.object_id)

        registry = InteractionHandlerRegistry()
        registry.register("obj1", InteractionEventType.CLICK, handler)
        await registry.dispatch(ClickEvent(object_id="obj1"))
        await asyncio.sleep(0.01)
        assert results == ["obj1"]

    @pytest.mark.anyio
    async def test_unregister(self):
        results = []

        async def handler(event):
            results.append(1)

        registry = InteractionHandlerRegistry()
        registry.register("obj1", InteractionEventType.CLICK, handler)
        registry.unregister("obj1", InteractionEventType.CLICK)
        await registry.dispatch(ClickEvent(object_id="obj1"))
        await asyncio.sleep(0.01)
        assert results == []

    @pytest.mark.anyio
    async def test_clear(self):
        results = []

        async def handler(event):
            results.append(1)

        registry = InteractionHandlerRegistry()
        registry.register("obj1", InteractionEventType.CLICK, handler)
        registry.clear()
        await registry.dispatch(ClickEvent(object_id="obj1"))
        await asyncio.sleep(0.01)
        assert results == []

    @pytest.mark.anyio
    async def test_unregister_all_for_object(self):
        results = []

        async def handler(event):
            results.append(1)

        registry = InteractionHandlerRegistry()
        registry.register("obj1", InteractionEventType.CLICK, handler)
        registry.register("obj1", InteractionEventType.SCROLL, handler)
        registry.unregister("obj1")  # remove all for obj1
        await registry.dispatch(ClickEvent(object_id="obj1"))
        await asyncio.sleep(0.01)
        assert results == []


class TestUtilityFunctions:
    def test_apply_delta_transform(self):
        transform = (1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)
        result = apply_delta_transform((10, 20), transform)
        assert result == (10, 20, 0)

    def test_apply_delta_transform_scaled(self):
        transform = (2, 0, 0, 0, 0, 3, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)
        result = apply_delta_transform((10, 10), transform)
        assert result == (20, 30, 0)

    def test_apply_delta_transform_wrong_size(self):
        with pytest.raises(ValueError):
            apply_delta_transform((1, 2), (1, 2, 3))

    def test_extract_camera_directions(self):
        transform = (1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)
        right, up, forward = extract_camera_directions(transform)
        assert right == (1, 0, 0)
        assert up == (0, 1, 0)
        assert forward == (0, 0, 1)


class TestEnums:
    def test_mouse_button_from_js_code(self):
        assert MouseButton.from_js_code(0) == MouseButton.LEFT
        assert MouseButton.from_js_code(1) == MouseButton.MIDDLE
        assert MouseButton.from_js_code(2) == MouseButton.RIGHT
        with pytest.raises(ValueError):
            MouseButton.from_js_code(3)

    def test_mouse_button_to_js_code(self):
        assert MouseButton.LEFT.to_js_code() == 0
        assert MouseButton.MIDDLE.to_js_code() == 1
        assert MouseButton.RIGHT.to_js_code() == 2

    def test_event_type_values(self):
        assert InteractionEventType.CLICK.value == "click"
        assert InteractionEventType.DBLCLICK.value == "dblclick"
        assert InteractionEventType.DRAG.value == "drag"
        assert InteractionEventType.DRAG_START.value == "drag_start"
        assert InteractionEventType.DRAG_MOVE.value == "drag_move"
        assert InteractionEventType.DRAG_END.value == "drag_end"
        assert InteractionEventType.SCROLL.value == "scroll"

    def test_modifier_values(self):
        assert ModifierKey.CTRL.value == "ctrl"
        assert ModifierKey.SHIFT.value == "shift"
        assert ModifierKey.ALT.value == "alt"


# Need asyncio for the async tests
import asyncio  # noqa: E402