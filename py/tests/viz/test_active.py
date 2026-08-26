# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for active scene objects (:class:`ActSceneObject` / :class:`ActPoint`)."""

import pytest

from pytanga.geometry import Point
from pytanga.viz._act_style import ActPointStyle
from pytanga.viz._active import ActPoint
from pytanga.viz._interaction import DragEvent, InteractionEventType
from pytanga.viz.visualizer import Visualizer


class _FakeStyles:
    """Minimal stand-in for ``VizSceneHandle.styles``."""

    def __init__(self) -> None:
        self.act_point = ActPointStyle()


class _FakeSceneHandle:
    """Records the interaction calls :class:`ActPoint` makes via its handle."""

    def __init__(self) -> None:
        self.styles = _FakeStyles()
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
