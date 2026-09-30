# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the per-pane ``InteractionSurface`` primitive."""

from __future__ import annotations

import asyncio
from typing import Any

from pytanga.geometry import Direction, Point
from pytanga.viz import (
    ClickEvent,
    DragEvent,
    InteractionEventType,
    InteractionSurface,
    PlanarMapper,
    SceneView,
)


class _FakeViz:
    def __init__(self) -> None:
        self._act_objects: dict[str, Any] = {}
        self.registered: list[tuple[str, InteractionEventType, Any]] = []

    def on_interaction(
        self,
        object_id: str,
        event_type: InteractionEventType,
        handler: Any,
        *,
        scene_name: str = "",
    ) -> None:
        self.registered.append((object_id, event_type, handler))


def _surface(**kwargs: Any) -> InteractionSurface:
    return InteractionSurface(PlanarMapper(), **kwargs)


class TestSerialization:
    def test_serialize_uses_mapper_plane(self) -> None:
        surface = _surface(on_drag=_noop_drag)
        data = surface.serialize()
        assert data["id"] == surface.id
        assert data["point"] == [0.0, 0.0, 0.0]
        assert data["normal"] == [0.0, 0.0, 1.0]
        events = {t["event_type"] for t in data["interaction"]["triggers"]}
        assert "drag" in events

    def test_serialize_includes_click_trigger_only_when_requested(self) -> None:
        drag_only = _surface(on_drag=_noop_drag).serialize()
        assert {t["event_type"] for t in drag_only["interaction"]["triggers"]} == {"drag"}

        with_click = _surface(on_drag=_noop_drag, on_click=_noop_click).serialize()
        assert {t["event_type"] for t in with_click["interaction"]["triggers"]} == {
            "drag",
            "click",
        }


class TestAnchors:
    def test_drag_anchor_intersects_plane(self) -> None:
        surface = _surface()
        hit = surface.drag_anchor(Point(2.0, 3.0, 5.0), Direction(0.0, 0.0, -1.0))
        assert hit == Point(2.0, 3.0, 0.0)

    def test_click_anchor_matches_drag_anchor(self) -> None:
        surface = _surface()
        anchor = surface.click_anchor(Point(2.0, 3.0, 5.0), Direction(0.0, 0.0, -1.0))
        assert anchor == Point(2.0, 3.0, 0.0)


class TestSceneViewSurface:
    def test_scene_view_serializes_surface_and_read_only(self) -> None:
        surface = _surface(on_drag=_noop_drag)
        view = SceneView("world", surface=surface, read_only=True)
        data = view._serialize()
        assert data["surface"]["id"] == surface.id
        assert data["surface"]["normal"] == [0.0, 0.0, 1.0]
        assert data["read_only"] is True

    def test_scene_view_omits_surface_and_read_only_by_default(self) -> None:
        data = SceneView("world")._serialize()
        assert "surface" not in data
        assert "read_only" not in data


class TestBinding:
    def test_bind_registers_act_object_and_handlers(self) -> None:
        surface = _surface(
            on_drag=_noop_drag, on_drag_start=_noop_event, on_click=_noop_click
        )
        fake = _FakeViz()
        surface._bind(fake)  # noqa: SLF001
        assert fake._act_objects[surface.id] is surface
        events = {event_type.value for _, event_type, _ in fake.registered}
        assert events == {"drag_move", "drag_start", "click"}

    def test_bind_is_idempotent(self) -> None:
        surface = _surface(on_drag=_noop_drag)
        fake = _FakeViz()
        surface._bind(fake)  # noqa: SLF001
        surface._bind(fake)  # noqa: SLF001
        assert len(fake.registered) == 1

    def test_dispatch_drag_calls_handler_with_surface(self) -> None:
        holder: dict[str, Any] = {}
        surface = _surface(on_drag=_noop_drag)
        surface._on_drag = _capture(holder)  # noqa: SLF001
        event = DragEvent(object_id=surface.id, world_position=Point(1.0, 2.0, 0.0))
        asyncio.run(surface._dispatch_drag(event))  # noqa: SLF001
        assert holder["event"] is event
        assert holder["surface"] is surface

    def test_dispatch_click_calls_handler_with_surface(self) -> None:
        holder: dict[str, Any] = {}
        surface = _surface()
        surface._on_click = _capture(holder)  # noqa: SLF001
        event = ClickEvent(object_id=surface.id, world_position=Point(1.0, 2.0, 0.0))
        asyncio.run(surface._dispatch_click(event))  # noqa: SLF001
        assert holder["event"] is event
        assert holder["surface"] is surface


async def _noop_drag(event: DragEvent, surface: InteractionSurface) -> bool:
    return True


async def _noop_event(event: DragEvent, surface: InteractionSurface) -> None:
    return None


async def _noop_click(event: ClickEvent, surface: InteractionSurface) -> None:
    return None


def _capture(holder: dict[str, Any]) -> Any:
    async def handler(event: Any, surface: InteractionSurface) -> None:
        holder["event"] = event
        holder["surface"] = surface

    return handler
