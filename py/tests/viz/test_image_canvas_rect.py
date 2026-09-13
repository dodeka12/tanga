# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for `ImageCanvas.draw_rectangle` (drag-to-create rectangle)."""

from __future__ import annotations

import asyncio
from typing import Any

import numpy as np

from pytanga.geometry import Point
from pytanga.viz import (
    ActRectangle2D,
    DragEvent,
    ImageCanvas,
    ImageData,
    InteractionEventType,
    Visualizer,
)


class _FakeTransport:
    def __init__(self) -> None:
        self.handlers: dict[tuple[str, str], Any] = {}

    def register(
        self,
        object_id: str,
        handler: Any,
        *,
        event: str = "change",
        origin: Any = None,
    ) -> None:
        self.handlers[(object_id, event)] = handler

    def send(self, message: dict) -> None:
        pass

    def send_bytes(self, payload: bytes) -> None:
        pass


def _canvas() -> tuple[Visualizer, ImageCanvas, _FakeTransport]:
    viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
    fake = _FakeTransport()
    viz._transport = fake  # type: ignore[attr-defined]
    viz._interaction_host._transport = fake  # type: ignore[attr-defined]
    canvas = ImageCanvas(viz)
    canvas.set_image(ImageData("img1", data=np.zeros((10, 20), dtype=np.uint8)))
    return viz, canvas, fake


class TestDrawRectangle:
    def test_draw_rectangle_flow(self) -> None:
        _, canvas, fake = _canvas()
        image_id = canvas.image_view.id
        done: list[ActRectangle2D] = []

        canvas.draw_rectangle(on_done=done.append)

        assert (image_id, "drag_start") in fake.handlers
        assert (image_id, "drag_move") in fake.handlers
        assert (image_id, "drag_end") in fake.handlers

        on_start = fake.handlers[(image_id, "drag_start")]
        on_move = fake.handlers[(image_id, "drag_move")]
        on_end = fake.handlers[(image_id, "drag_end")]

        asyncio.run(on_start(DragEvent(world_position=Point(2.0, 3.0, 0.0))))
        asyncio.run(on_move(DragEvent(world_position=Point(12.0, 7.0, 0.0))))
        asyncio.run(on_end(DragEvent(world_position=Point(12.0, 7.0, 0.0))))

        assert len(done) == 1
        rect = done[0]
        assert rect.entity.center.x == 7.0
        assert rect.entity.center.y == 5.0
        assert rect.entity.size == (10.0, 4.0)

    def test_draw_rectangle_enables_drag_trigger(self) -> None:
        viz, canvas, _ = _canvas()
        image_id = canvas.image_view.id

        # No drag handlers → the plane registers no triggers.
        assert canvas.act_plane.interaction_config.triggers == []

        canvas.draw_rectangle()

        cfg = viz._interaction_host._interaction_configs[canvas.scene_name][image_id]
        assert any(t.event_type is InteractionEventType.DRAG for t in cfg.triggers)

    def test_draw_rectangle_restores_plane_config(self) -> None:
        viz, canvas, _ = _canvas()
        image_id = canvas.image_view.id

        cancel = canvas.draw_rectangle()
        cancel()

        cfg = viz._interaction_host._interaction_configs[canvas.scene_name][image_id]
        assert cfg.triggers == []
