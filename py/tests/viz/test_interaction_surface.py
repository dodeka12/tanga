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
    Visualizer,
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


class _FakeTransport:
    def __init__(self) -> None:
        self.registered: list[tuple[str, str]] = []

    def send(self, message: dict) -> None:  # noqa: ARG002
        pass

    def send_bytes(self, payload: bytes) -> None:  # noqa: ARG002
        pass

    def unregister(self, control_id: str) -> None:  # noqa: ARG002
        pass

    def register(
        self,
        object_id: str,
        handler: object,  # noqa: ARG002
        *,
        event: str = "change",
        origin: object = None,  # noqa: ARG002
    ) -> None:
        self.registered.append((object_id, event))


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


class TestVisualizerBinding:
    def test_bind_surfaces_binds_scene_view_surface(self) -> None:
        viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
        fake = _FakeTransport()
        viz._transport = fake  # type: ignore[attr-defined]
        viz._interaction_host._transport = fake  # type: ignore[attr-defined]

        surface = _surface(on_drag=_noop_drag)
        view = SceneView("", surface=surface)

        viz._bind_surfaces(view)  # noqa: SLF001

        assert viz._act_objects[surface.id] is surface
        events = {event for oid, event in fake.registered if oid == surface.id}
        assert events == {"drag_move"}


class TestClickAnchorResolution:
    _IDENTITY = [
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ]

    def test_surface_click_resolves_from_event_ray(self) -> None:
        class _RecordingServer:
            def __init__(self) -> None:
                self.sent = []

            async def push_raw_to_browser(self, browser_id, data):  # noqa: ANN001, ANN202
                self.sent.append((browser_id, data))

        async def _run():  # noqa: ANN202
            viz = Visualizer(add_default_axes=False, add_default_grid=False)
            viz._server = _RecordingServer()

            received: list[Point] = []

            async def on_click(event, surface):  # noqa: ANN001, ANN202
                received.append(event.world_position)

            surface = InteractionSurface(PlanarMapper(), on_click=on_click)
            surface._bind(viz)  # noqa: SLF001

            # The event ray hits the z=0 plane at (2, 3, 0).  The pre-fix
            # `pixel_ray(screen_position)` reconstruction would instead resolve
            # to (0, 0, 0) from the identity camera — the event ray must win.
            await viz._dispatch_interaction_event(
                "interaction:click",
                {
                    "type": "interaction:click",
                    "event_type": "click",
                    "object_id": surface.id,
                    "browser_id": "b1",
                    "screen_position": [400.0, 300.0],
                    "world_position": [0.0, 0.0, 0.15],
                    "world_normal": [0.0, 0.0, 1.0],
                    "ray_origin": [2.0, 3.0, 5.0],
                    "ray_direction": [0.0, 0.0, -1.0],
                    "camera": {
                        "view": TestClickAnchorResolution._IDENTITY,
                        "view_inv": TestClickAnchorResolution._IDENTITY,
                        "proj": TestClickAnchorResolution._IDENTITY,
                        "proj_inv": TestClickAnchorResolution._IDENTITY,
                        "viewport_width": 800,
                        "viewport_height": 600,
                        "space_dim": 3,
                    },
                },
            )

            await asyncio.sleep(0)
            assert received == [Point(2.0, 3.0, 0.0)]

        asyncio.run(_run())


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
