# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for `ImageCanvas` interaction wiring (image-plane handlers)."""

from __future__ import annotations

import asyncio

import numpy as np

from pytanga.geometry import Point
from pytanga.viz import DragEvent, ImageCanvas, ImageData, InteractionEventType, Visualizer


class _FakeTransport:
    def __init__(self) -> None:
        self.json_messages: list[dict] = []
        self.binary_frames: list[bytes] = []
        self.registered: list[tuple] = []

    def send(self, message: dict) -> None:
        self.json_messages.append(message)

    def send_bytes(self, payload: bytes) -> None:
        self.binary_frames.append(payload)

    def register(self, object_id: str, handler: object, *, event: str = "change", origin: object = None) -> None:  # noqa: ANN001
        self.registered.append((object_id, event))


def _canvas(on_drag: object = None) -> tuple[Visualizer, ImageCanvas]:
    viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
    fake = _FakeTransport()
    viz._transport = fake  # type: ignore[attr-defined]
    viz._interaction_host._transport = fake  # type: ignore[attr-defined]
    return viz, ImageCanvas(viz, on_drag=on_drag)


class TestInteractionRegistration:
    def test_plane_registered_interactive(self) -> None:
        viz, canvas = _canvas()
        canvas.set_image(ImageData("img1", data=np.zeros((4, 6), dtype=np.uint8)))
        image_id = canvas.image_view.id
        assert viz._act_objects[image_id] is canvas.act_plane
        assert image_id in canvas.handle.scene._interaction_configs
        events = {event for _, event in canvas._transport.registered}
        assert InteractionEventType.DRAG_MOVE.value in events


class TestDragHandler:
    def test_handler_receives_pixel_position_and_sets_uniform(self) -> None:
        holder: dict = {}

        async def on_drag(event: DragEvent, ap: object) -> bool:  # noqa: ANN001
            holder["canvas"].set_uniform("u_brightness", 0.5)
            holder["pos"] = (event.world_position.x, event.world_position.y)
            return True

        viz, canvas = _canvas(on_drag=on_drag)
        holder["canvas"] = canvas
        canvas.set_image(ImageData("img1", data=np.zeros((10, 20), dtype=np.uint8)))

        asyncio.run(canvas.act_plane._on_drag(DragEvent(world_position=Point(7.0, 3.0, 0.0))))

        assert holder["pos"] == (7.0, 3.0)
        assert canvas.image_view.uniforms["u_brightness"] == 0.5
        assert canvas._transport.json_messages[-1]["type"] == "image_update"
        assert canvas._transport.json_messages[-1]["uniforms"] == {"u_brightness": 0.5}
