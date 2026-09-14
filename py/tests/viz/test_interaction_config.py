# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for interaction config serialization, deserialization, and utilities."""

import pytest
from pytanga.viz._interaction import (
    ClickEvent,
    DragEvent,
    InteractionConfig,
    InteractionEvent,
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
from pytanga.viz import ControlEvent


class TestInteractionTrigger:
    def test_to_dict_minimal(self):  # noqa: ANN201
        t = InteractionTrigger(event_type=InteractionEventType.CLICK)
        d = t.to_dict()
        assert d == {"event_type": "click", "modifiers": []}

    def test_to_dict_full(self):  # noqa: ANN201
        t = InteractionTrigger(
            event_type=InteractionEventType.DRAG,
            mouse_button=MouseButton.LEFT,
            modifiers=frozenset({ModifierKey.CTRL, ModifierKey.SHIFT}),
        )
        d = t.to_dict()
        assert d["event_type"] == "drag"
        assert d["mouse_button"] == "left"
        assert set(d["modifiers"]) == {"ctrl", "shift"}

    def test_from_dict(self):  # noqa: ANN201
        d = {"event_type": "drag", "mouse_button": "right", "modifiers": ["alt"]}
        t = InteractionTrigger.from_dict(d)
        assert t.event_type == InteractionEventType.DRAG
        assert t.mouse_button == MouseButton.RIGHT
        assert t.modifiers == frozenset({ModifierKey.ALT})

    def test_from_dict_no_button(self):  # noqa: ANN201
        d = {"event_type": "scroll", "modifiers": []}
        t = InteractionTrigger.from_dict(d)
        assert t.mouse_button is None


class TestInteractionConfig:
    def test_to_dict(self):  # noqa: ANN201
        ic = InteractionConfig(
            enabled=True,
            triggers=[InteractionTrigger(event_type=InteractionEventType.DRAG)],
            throttle_ms=30,
        )
        d = ic.to_dict()
        assert d["enabled"] is True
        assert len(d["triggers"]) == 1
        assert d["throttle_ms"] == 30

    def test_to_dict_disabled(self):  # noqa: ANN201
        ic = InteractionConfig(enabled=False)
        d = ic.to_dict()
        assert d["enabled"] is False
        assert d["triggers"] == []
        assert d["throttle_ms"] == 50

    def test_to_dict_hover_fields(self):  # noqa: ANN201
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

    def test_to_dict_hover_fields_omitted_when_none(self):  # noqa: ANN201
        ic = InteractionConfig(enabled=True)
        d = ic.to_dict()
        assert "hover_emissive" not in d
        assert "hover_scale" not in d
        assert "hover_opacity" not in d

    def test_to_dict_cursor_fields(self):  # noqa: ANN201
        ic = InteractionConfig(enabled=True, hover_cursor="crosshair", cursor="grabbing")
        d = ic.to_dict()
        assert d["hover_cursor"] == "crosshair"
        assert d["cursor"] == "grabbing"

    def test_to_dict_cursor_fields_omitted_when_none(self):  # noqa: ANN201
        ic = InteractionConfig(enabled=True)
        d = ic.to_dict()
        assert "hover_cursor" not in d
        assert "cursor" not in d


class TestParseEvent:
    def test_parse_click(self):  # noqa: ANN201
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

    def test_parse_drag_move(self):  # noqa: ANN201
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

    def test_parse_drag_move_ray_fields(self):  # noqa: ANN201
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

    def test_parse_drag_move_ray_defaults(self):  # noqa: ANN201
        data = {
            "type": "interaction:drag_move",
            "event_type": "drag_move",
            "object_id": "x",
        }
        event = _parse_event(data)
        assert isinstance(event, DragEvent)
        assert event.ray_origin == Point(0.0, 0.0, 0.0)
        assert event.ray_direction == Direction(0.0, 0.0, 0.0)

    def test_parse_scroll(self):  # noqa: ANN201
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

    def test_parse_unknown_event_type(self):  # noqa: ANN201
        with pytest.raises(ValueError):
            _parse_event({"type": "interaction:foo", "event_type": "bogus"})

    def test_parse_missing_event_type(self):  # noqa: ANN201
        with pytest.raises(ValueError):
            _parse_event({"type": "interaction:click"})


class TestCoalesceDragEvents:
    def test_single_event(self):  # noqa: ANN201
        e = DragEvent(delta_pixels=(1, 0), screen_position=(100, 200))
        result = _coalesce_drag_events([e])
        assert result.delta_pixels == (1, 0)

    def test_two_events(self):  # noqa: ANN201
        e1 = DragEvent(delta_pixels=(1, 0), screen_position=(100, 200))
        e2 = DragEvent(delta_pixels=(2, 3), screen_position=(105, 208))
        result = _coalesce_drag_events([e1, e2])
        assert result.delta_pixels == (3, 3)
        assert result.screen_position == (105, 208)

    def test_modifiers_from_last(self):  # noqa: ANN201
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

    def test_empty_raises(self):  # noqa: ANN201
        with pytest.raises(ValueError):
            _coalesce_drag_events([])

    def test_preserves_ray(self):  # noqa: ANN201
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
    async def test_register_and_dispatch(self):  # noqa: ANN201
        results = []

        async def handler(event):  # noqa: ANN001, ANN202
            results.append(event.object_id)

        registry = InteractionHandlerRegistry()
        registry.register("obj1", InteractionEventType.CLICK, handler)
        await registry.dispatch(ClickEvent(object_id="obj1"))
        await asyncio.sleep(0.01)
        assert results == ["obj1"]

    @pytest.mark.anyio
    async def test_unregister(self):  # noqa: ANN201
        results = []

        async def handler(event):  # noqa: ANN001, ANN202
            results.append(1)

        registry = InteractionHandlerRegistry()
        registry.register("obj1", InteractionEventType.CLICK, handler)
        registry.unregister("obj1", InteractionEventType.CLICK)
        await registry.dispatch(ClickEvent(object_id="obj1"))
        await asyncio.sleep(0.01)
        assert results == []

    @pytest.mark.anyio
    async def test_clear(self):  # noqa: ANN201
        results = []

        async def handler(event):  # noqa: ANN001, ANN202
            results.append(1)

        registry = InteractionHandlerRegistry()
        registry.register("obj1", InteractionEventType.CLICK, handler)
        registry.clear()
        await registry.dispatch(ClickEvent(object_id="obj1"))
        await asyncio.sleep(0.01)
        assert results == []

    @pytest.mark.anyio
    async def test_unregister_all_for_object(self):  # noqa: ANN201
        results = []

        async def handler(event):  # noqa: ANN001, ANN202
            results.append(1)

        registry = InteractionHandlerRegistry()
        registry.register("obj1", InteractionEventType.CLICK, handler)
        registry.register("obj1", InteractionEventType.SCROLL, handler)
        registry.unregister("obj1")  # remove all for obj1
        await registry.dispatch(ClickEvent(object_id="obj1"))
        await asyncio.sleep(0.01)
        assert results == []

    def test_delegates_to_shared_registry(self):  # noqa: ANN201
        from pytanga.viz._controls import ControlHandlerRegistry

        shared = ControlHandlerRegistry()
        registry = InteractionHandlerRegistry(shared)

        async def handler(event):  # noqa: ANN001, ANN202
            pass

        registry.register("obj1", InteractionEventType.CLICK, handler)
        assert shared.get("obj1", "click") is handler
        assert registry.get("obj1", InteractionEventType.CLICK) is handler

        registry.unregister("obj1", InteractionEventType.CLICK)
        assert shared.get("obj1", "click") is None


class TestUtilityFunctions:
    def test_apply_delta_transform(self):  # noqa: ANN201
        transform = (1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)
        result = apply_delta_transform((10, 20), transform)
        assert result == (10, 20, 0)

    def test_apply_delta_transform_scaled(self):  # noqa: ANN201
        transform = (2, 0, 0, 0, 0, 3, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)
        result = apply_delta_transform((10, 10), transform)
        assert result == (20, 30, 0)

    def test_apply_delta_transform_wrong_size(self):  # noqa: ANN201
        with pytest.raises(ValueError):
            apply_delta_transform((1, 2), (1, 2, 3))

    def test_extract_camera_directions(self):  # noqa: ANN201
        transform = (1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)
        right, up, forward = extract_camera_directions(transform)
        assert right == (1, 0, 0)
        assert up == (0, 1, 0)
        assert forward == (0, 0, 1)


class TestEnums:
    def test_mouse_button_from_js_code(self):  # noqa: ANN201
        assert MouseButton.from_js_code(0) == MouseButton.LEFT
        assert MouseButton.from_js_code(1) == MouseButton.MIDDLE
        assert MouseButton.from_js_code(2) == MouseButton.RIGHT
        with pytest.raises(ValueError):
            MouseButton.from_js_code(3)

    def test_mouse_button_to_js_code(self):  # noqa: ANN201
        assert MouseButton.LEFT.to_js_code() == 0
        assert MouseButton.MIDDLE.to_js_code() == 1
        assert MouseButton.RIGHT.to_js_code() == 2

    def test_event_type_values(self):  # noqa: ANN201
        assert InteractionEventType.CLICK.value == "click"
        assert InteractionEventType.DBLCLICK.value == "dblclick"
        assert InteractionEventType.DRAG.value == "drag"
        assert InteractionEventType.DRAG_START.value == "drag_start"
        assert InteractionEventType.DRAG_MOVE.value == "drag_move"
        assert InteractionEventType.DRAG_END.value == "drag_end"
        assert InteractionEventType.SCROLL.value == "scroll"

    def test_modifier_values(self):  # noqa: ANN201
        assert ModifierKey.CTRL.value == "ctrl"
        assert ModifierKey.SHIFT.value == "shift"
        assert ModifierKey.ALT.value == "alt"


class TestEventHierarchy:
    """All events derive from the one public :class:`ControlEvent`."""

    def test_interaction_events_subclass_control_event(self):  # noqa: ANN201
        for cls in (InteractionEvent, ClickEvent, DragEvent, ScrollEvent):
            assert issubclass(cls, ControlEvent)

    def test_control_event_is_the_public_one(self):  # noqa: ANN201
        import pytanga.viz._controls as controls
        import pytanga.viz._interaction as interaction

        assert ControlEvent is controls.ControlEvent
        # ``_interaction`` re-exports that very class instead of declaring a
        # second class with the same name (which is what it used to do).
        assert interaction.ControlEvent is controls.ControlEvent
        assert interaction.ControlEvent.__module__ == "pytanga.viz._controls"

    def test_interaction_event_inherits_browser_id(self):  # noqa: ANN201
        from pytanga.viz import InteractionEvent as PublicInteractionEvent

        assert PublicInteractionEvent is InteractionEvent
        ev = ClickEvent(object_id="obj1", browser_id="b1")
        assert ev.object_id == "obj1"
        assert ev.browser_id == "b1"  # inherited from ControlEvent
        assert ev.camera is None

    def test_control_event_fields_are_shared(self):  # noqa: ANN201
        from pytanga.viz import ControlEvent as PublicControlEvent

        ev = PublicControlEvent(browser_id="b1")
        assert ev.browser_id == "b1"


# Need asyncio for the async tests
import asyncio  # noqa: E402
