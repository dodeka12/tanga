# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for active scene objects (:class:`ActSceneObject` / :class:`ActPoint`)."""

import pytest

from pytanga.geometry import Point
from pytanga.viz._act_style import ActPointStyle
from pytanga.viz._active import ActPoint
from pytanga.viz._interaction import (
    DragEvent,
    DragMode,
    InteractionEventType,
    MouseButton,
)
from pytanga.viz.visualizer import Visualizer


class _FakeStyles:
    """Minimal stand-in for ``VizSceneHandle.styles``."""

    def __init__(self) -> None:
        self.act_point = ActPointStyle()


class _FakeSceneConfig:
    """Minimal stand-in for ``SceneConfig.space_dim``."""

    def __init__(self, space_dim: int | None) -> None:
        self.space_dim = space_dim


class _FakeScene:
    """Minimal stand-in for ``VizSceneHandle.scene``."""

    def __init__(self, space_dim: int | None) -> None:
        self.config = _FakeSceneConfig(space_dim)


class _FakeSceneHandle:
    """Records the interaction calls :class:`ActPoint` makes via its handle."""

    def __init__(self, space_dim: int | None = None) -> None:
        self.styles = _FakeStyles()
        self.scene = _FakeScene(space_dim)
        self.configs: list[tuple[str, object]] = []
        self.handlers: dict[InteractionEventType, object] = {}
        self.updates: list[tuple[str, Point]] = []
        self.flushes = 0

    def set_interaction(self, object_id: str, config: object) -> None:
        self.configs.append((object_id, config))

    def on_interaction(
        self, object_id: str, event_type: InteractionEventType, handler: object
    ) -> None:
        self.handlers[event_type] = handler

    def update_entity(self, object_id: str, entity: Point) -> None:
        self.updates.append((object_id, entity))

    def flush(self) -> None:
        self.flushes += 1


def _init_point(**kwargs) -> tuple[ActPoint, _FakeSceneHandle]:
    """Create and initialise an :class:`ActPoint` with a fake handle."""
    handle = _FakeSceneHandle()
    ap = ActPoint(1, 2, 3, **kwargs)
    ap._init(handle, "pt1")
    return ap, handle


def _init_point_2d(**kwargs) -> tuple[ActPoint, _FakeSceneHandle]:
    """Create and initialise an :class:`ActPoint` in a 2D scene."""
    handle = _FakeSceneHandle(space_dim=2)
    ap = ActPoint(1, 2, 3, **kwargs)
    ap._init(handle, "pt1")
    return ap, handle


def _coords(p: Point) -> tuple[float, float, float]:
    return (p.x, p.y, p.z)


class TestInteractionRegistration:
    def test_registers_drag_move_by_default(self):
        ap, handle = _init_point()
        assert InteractionEventType.DRAG_MOVE in handle.handlers
        assert InteractionEventType.DRAG_START not in handle.handlers
        assert InteractionEventType.DRAG_END not in handle.handlers

    def test_registers_start_and_end_when_provided(self):
        async def on_start(event, ap):
            pass

        async def on_end(event, ap):
            pass

        ap, handle = _init_point(on_drag_start=on_start, on_drag_end=on_end)
        assert InteractionEventType.DRAG_MOVE in handle.handlers
        assert InteractionEventType.DRAG_START in handle.handlers
        assert InteractionEventType.DRAG_END in handle.handlers

    def test_registers_only_start_when_only_start_provided(self):
        async def on_start(event, ap):
            pass

        ap, handle = _init_point(on_drag_start=on_start)
        assert InteractionEventType.DRAG_START in handle.handlers
        assert InteractionEventType.DRAG_END not in handle.handlers

    def test_sets_interaction_config(self):
        ap, handle = _init_point()
        assert len(handle.configs) == 1
        assert handle.configs[0][0] == "pt1"


class TestDragPhases:
    @pytest.mark.anyio
    async def test_drag_start_handler_receives_event_and_point(self):
        calls = []

        async def on_start(event, ap):
            calls.append((event, ap))

        ap, handle = _init_point(on_drag_start=on_start)
        event = DragEvent(object_id="pt1", event_type=InteractionEventType.DRAG_START)
        await handle.handlers[InteractionEventType.DRAG_START](event)
        assert len(calls) == 1
        assert calls[0][0] is event
        assert calls[0][1] is ap

    @pytest.mark.anyio
    async def test_drag_end_handler_receives_event_and_point(self):
        calls = []

        async def on_end(event, ap):
            calls.append((event, ap))

        ap, handle = _init_point(on_drag_end=on_end)
        event = DragEvent(object_id="pt1", event_type=InteractionEventType.DRAG_END)
        await handle.handlers[InteractionEventType.DRAG_END](event)
        assert len(calls) == 1
        assert calls[0][0] is event
        assert calls[0][1] is ap

    @pytest.mark.anyio
    async def test_drag_start_does_not_move_point(self):
        async def on_start(event, ap):
            pass

        ap, handle = _init_point(on_drag_start=on_start)
        before = _coords(ap.point)
        event = DragEvent(
            object_id="pt1",
            event_type=InteractionEventType.DRAG_START,
            world_position=Point(9, 9, 9),
        )
        await handle.handlers[InteractionEventType.DRAG_START](event)
        assert _coords(ap.point) == before
        assert handle.updates == []
        assert handle.flushes == 0

    @pytest.mark.anyio
    async def test_drag_move_moves_point_and_flushes(self):
        ap, handle = _init_point()
        event = DragEvent(
            object_id="pt1",
            event_type=InteractionEventType.DRAG_MOVE,
            world_position=Point(4, 5, 6),
        )
        await handle.handlers[InteractionEventType.DRAG_MOVE](event)
        assert _coords(ap.point) == (4, 5, 6)
        assert len(handle.updates) == 1
        assert handle.updates[0][0] == "pt1"
        assert _coords(handle.updates[0][1]) == (4, 5, 6)
        assert handle.flushes == 1

    @pytest.mark.anyio
    async def test_custom_move_handler_can_suppress_default(self):
        async def handler(event, ap):
            return True

        ap, handle = _init_point(handler=handler)
        event = DragEvent(
            object_id="pt1",
            event_type=InteractionEventType.DRAG_MOVE,
            world_position=Point(7, 8, 9),
        )
        await handle.handlers[InteractionEventType.DRAG_MOVE](event)
        assert _coords(ap.point) == (1, 2, 3)
        assert handle.updates == []
        assert handle.flushes == 0


class TestDragModeConstraint:
    def test_drag_mode_sets_primary_trigger(self):
        ap, handle = _init_point(drag_mode=DragMode.XY_PLANE)
        config = handle.configs[0][1]
        assert len(config.triggers) == 1
        trigger = config.triggers[0]
        assert trigger.event_type == InteractionEventType.DRAG
        assert trigger.mouse_button == MouseButton.LEFT
        assert trigger.drag_mode == DragMode.XY_PLANE
        assert trigger.modifiers == frozenset()

    def test_drag_mode_omits_modifier_triggers(self):
        ap, handle = _init_point(drag_mode=DragMode.XY_PLANE)
        config = handle.configs[0][1]
        modes = {t.drag_mode for t in config.triggers}
        assert modes == {DragMode.XY_PLANE}
        assert all(t.modifiers == frozenset() for t in config.triggers)

    def test_drag_mode_none_keeps_four_default_triggers(self):
        ap, handle = _init_point()
        config = handle.configs[0][1]
        assert len(config.triggers) == 4
        modes = {t.drag_mode for t in config.triggers}
        assert modes == {
            DragMode.VIEW_PLANE,
            DragMode.XY_PLANE,
            DragMode.XZ_PLANE,
            DragMode.YZ_PLANE,
        }
        # Unmodified trigger remains view-plane.
        unmodified = [
            t for t in config.triggers if t.modifiers == frozenset()
        ]
        assert len(unmodified) == 1
        assert unmodified[0].drag_mode == DragMode.VIEW_PLANE

    def test_drag_mode_serializes_for_frontend(self):
        ap, handle = _init_point(drag_mode=DragMode.XY_PLANE)
        config = handle.configs[0][1]
        d = config.to_dict()
        assert len(d["triggers"]) == 1
        assert d["triggers"][0]["drag_mode"] == "xy_plane"
        assert d["triggers"][0]["modifiers"] == []

    def test_drag_mode_keeps_lifecycle_handlers(self):
        async def on_start(event, ap):
            pass

        async def on_end(event, ap):
            pass

        async def handler(event, ap):
            return False

        ap, handle = _init_point(
            drag_mode=DragMode.XY_PLANE,
            handler=handler,
            on_drag_start=on_start,
            on_drag_end=on_end,
        )
        assert InteractionEventType.DRAG_MOVE in handle.handlers
        assert InteractionEventType.DRAG_START in handle.handlers
        assert InteractionEventType.DRAG_END in handle.handlers

    def test_2d_defaults_to_xy_plane(self):
        ap, handle = _init_point_2d()
        config = handle.configs[0][1]
        assert len(config.triggers) == 1
        trigger = config.triggers[0]
        assert trigger.event_type == InteractionEventType.DRAG
        assert trigger.mouse_button == MouseButton.LEFT
        assert trigger.drag_mode == DragMode.XY_PLANE
        assert trigger.modifiers == frozenset()

    def test_explicit_drag_mode_overrides_2d_default(self):
        ap, handle = _init_point_2d(drag_mode=DragMode.VIEW_PLANE)
        config = handle.configs[0][1]
        assert len(config.triggers) == 1
        assert config.triggers[0].drag_mode == DragMode.VIEW_PLANE

    def test_3d_keeps_four_default_triggers(self):
        handle = _FakeSceneHandle(space_dim=3)
        ap = ActPoint(1, 2, 3)
        ap._init(handle, "pt1")
        config = handle.configs[0][1]
        assert len(config.triggers) == 4
        modes = {t.drag_mode for t in config.triggers}
        assert modes == {
            DragMode.VIEW_PLANE,
            DragMode.XY_PLANE,
            DragMode.XZ_PLANE,
            DragMode.YZ_PLANE,
        }


class TestActPointLabel:
    def test_add_with_label(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        ap = ActPoint(1, 2, 3)
        eid = viz.add(ap, label="P")
        assert viz.get_label_ids(eid)  # a label is attached to the point

        # Removing the point also removes its attached label.
        viz.remove(eid)
        viz._scene.flush()
        assert viz._scene.entity_count == 0
