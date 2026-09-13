# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Integration tests for `ImageCanvas` server-side sync (`_image_view.py`)."""

from __future__ import annotations

import numpy as np

from pytanga.viz import ImageCanvas, ImageData, Visualizer
from pytanga.viz._image_wire import decode_image_frame


class _FakeTransport:
    """Records JSON and binary sends instead of touching a real socket."""

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


def _canvas() -> tuple[Visualizer, ImageCanvas]:
    viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
    fake = _FakeTransport()
    viz._transport = fake  # type: ignore[attr-defined]
    viz._interaction_host._transport = fake  # type: ignore[attr-defined]
    return viz, ImageCanvas(viz)


class TestSync:
    def test_set_image_sends_one_binary_frame(self) -> None:
        _, canvas = _canvas()
        canvas.set_image(ImageData("img1", data=np.zeros((3, 4, 3), dtype=np.uint8)))
        assert len(canvas._transport.binary_frames) == 1
        decoded = decode_image_frame(canvas._transport.binary_frames[0])
        assert decoded["id"] == "img1"
        assert decoded["channels"] == 3

    def test_set_uniform_sends_json_only(self) -> None:
        _, canvas = _canvas()
        canvas.set_image(ImageData("img1", data=np.zeros((3, 4), dtype=np.uint8)))
        before = len(canvas._transport.binary_frames)
        canvas.set_uniform("u_brightness", 0.5)
        assert len(canvas._transport.binary_frames) == before
        msg = canvas._transport.json_messages[-1]
        assert msg["type"] == "image_update"
        assert msg["uniforms"] == {"u_brightness": 0.5}

    def test_overlay_add_sends_no_binary(self) -> None:
        from pytanga.geometry import Point

        _, canvas = _canvas()
        canvas.set_image(ImageData("img1", data=np.zeros((3, 4), dtype=np.uint8)))
        before = len(canvas._transport.binary_frames)
        canvas.add(Point(1.0, 2.0, 0.0))
        assert len(canvas._transport.binary_frames) == before

    def test_image_entity_in_scene_state(self) -> None:
        _, canvas = _canvas()
        canvas.set_image(ImageData("img1", data=np.zeros((3, 4, 3), dtype=np.uint8)))
        state = canvas.handle.scene.full_state()
        image_entities = [e for e in state if e.get("kind") == "image"]
        assert len(image_entities) == 1
        assert image_entities[0]["id"] == canvas.image_view.id

    def test_scene_image_frames(self) -> None:
        _, canvas = _canvas()
        canvas.set_image(ImageData("img1", data=np.zeros((3, 4, 3), dtype=np.uint8)))
        frames = canvas.handle.scene.image_frames()
        assert len(frames) == 1
        image_id, frame = frames[0]
        assert image_id == "img1"
        decoded = decode_image_frame(frame)
        assert decoded["channels"] == 3
        assert decoded["width"] == 4 and decoded["height"] == 3
