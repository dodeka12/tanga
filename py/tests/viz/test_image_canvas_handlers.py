# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for `ImageCanvas` interaction wiring (image-plane handlers)."""

from __future__ import annotations

import asyncio
from typing import Any

import numpy as np

from pytanga.geometry import Point
from pytanga.viz import (
    DragEvent,
    ImageCanvas,
    ImageData,
    InteractionEventType,
    Visualizer,
)


class _FakeTransport:
    def __init__(self) -> None:
        self.json_messages: list[dict] = []
        self.binary_frames: list[bytes] = []
        self.registered: list[tuple] = []

    def send(self, message: dict) -> None:
        self.json_messages.append(message)

    def send_bytes(self, payload: bytes) -> None:
        self.binary_frames.append(payload)

    def register(
        self,
        object_id: str,
        handler: object,
        *,
        event: str = "change",
        origin: object = None,
    ) -> None:  # noqa: ANN001
        self.registered.append((object_id, event))


def _canvas(on_drag: Any = None) -> tuple[Visualizer, ImageCanvas]:
    viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
    fake = _FakeTransport()
    viz._transport = fake  # type: ignore[attr-defined]
    viz._interaction_host._transport = fake  # type: ignore[attr-defined]
    return viz, ImageCanvas(viz, on_drag=on_drag)


class TestInteractionRegistration:
    def test_surface_registered(self) -> None:
        async def on_drag(event: DragEvent, canvas: ImageCanvas) -> bool:
            return True

        viz, canvas = _canvas(on_drag=on_drag)
        canvas.set_image(ImageData("img1", data=np.zeros((4, 6), dtype=np.uint8)))
        viz._bind_surfaces(canvas.scene_view())  # noqa: SLF001
        assert viz._act_objects[canvas.surface.id] is canvas.surface
        events = {event for _, event in canvas._transport.registered}
        assert InteractionEventType.DRAG_MOVE.value in events

    def test_set_enabled_toggles_surface(self) -> None:
        viz, canvas = _canvas()
        canvas.set_image(ImageData("img1", data=np.zeros((4, 6), dtype=np.uint8)))

        canvas.set_enabled(False)
        assert canvas.surface._interaction_config().enabled is False

        canvas.set_enabled(True)
        assert canvas.surface._interaction_config().enabled is True


class TestDragHandler:
    def test_handler_receives_pixel_position_and_sets_uniform(self) -> None:
        holder: dict[str, object] = {}

        async def on_drag(event: DragEvent, canvas: ImageCanvas) -> bool:
            canvas.set_uniform("u_brightness", 0.5)
            holder["pos"] = (event.world_position.x, event.world_position.y)
            return True

        viz, canvas = _canvas(on_drag=on_drag)
        canvas.set_image(ImageData("img1", data=np.zeros((10, 20), dtype=np.uint8)))

        asyncio.run(
            canvas.surface._dispatch_drag(
                DragEvent(world_position=Point(7.0, 3.0, 0.0))
            )
        )

        assert holder["pos"] == (7.0, 3.0)
        assert canvas.image_view.uniforms["u_brightness"] == 0.5
        assert canvas._transport.json_messages[-1]["type"] == "image_update"
        assert canvas._transport.json_messages[-1]["uniforms"] == {"u_brightness": 0.5}
