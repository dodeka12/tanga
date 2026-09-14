# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the export asset store (`_animation_recording.py`)."""

from __future__ import annotations

import base64

import numpy as np

from pytanga.viz import ImageCanvas, ImageData, ImageDType, Visualizer
from pytanga.viz.export._animation_recording import AnimationRecording


class _FakeTransport:
    def send(self, message: dict) -> None: ...

    def send_bytes(self, payload: bytes) -> None: ...

    def register(self, object_id: str, handler: object, *, event: str = "change", origin: object = None) -> None:  # noqa: ANN001
        ...


def _canvas() -> tuple[Visualizer, ImageCanvas]:
    viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
    fake = _FakeTransport()
    viz._transport = fake  # type: ignore[attr-defined]
    viz._interaction_host._transport = fake  # type: ignore[attr-defined]
    return viz, ImageCanvas(viz)


class TestAssetStore:
    def test_data_image_captured_as_base64(self) -> None:
        _, canvas = _canvas()
        arr = np.arange(12, dtype=np.uint8).reshape(3, 4)
        canvas.set_image(ImageData("img1", data=arr))
        rec = AnimationRecording(canvas.handle.scene)
        rec.capture_frame()

        asset = rec.assets["img1"]
        assert asset["source"] == "data"
        assert asset["width"] == 4 and asset["height"] == 3 and asset["channels"] == 1
        assert asset["data"] == base64.b64encode(arr.tobytes()).decode("ascii")

    def test_url_image_captured_as_url(self) -> None:
        _, canvas = _canvas()
        canvas.set_image(
            ImageData("u", url="http://x", width=4, height=3, channels=3,
                      dtype=ImageDType.UINT8)
        )
        rec = AnimationRecording(canvas.handle.scene)
        rec.capture_frame()

        asset = rec.assets["u"]
        assert asset["source"] == "url"
        assert asset["url"] == "http://x"
        assert "data" not in asset

    def test_assets_captured_once_then_include_images(self) -> None:
        _, canvas = _canvas()
        canvas.set_image(ImageData("img1", data=np.zeros((2, 2), dtype=np.uint8)))
        rec = AnimationRecording(canvas.handle.scene)
        rec.capture_frame()
        first = rec.assets["img1"]["data"]

        # Re-capture without the flag → assets unchanged.
        rec.capture_frame()
        assert rec.assets["img1"]["data"] == first

        # Replace the image and re-capture with the flag → assets updated.
        canvas.set_image(ImageData("img1", data=np.ones((2, 2), dtype=np.uint8)))
        rec.capture_frame(include_images=True)
        assert rec.assets["img1"]["data"] != first

    def test_to_dict_includes_assets(self) -> None:
        _, canvas = _canvas()
        canvas.set_image(ImageData("img1", data=np.zeros((2, 2), dtype=np.uint8)))
        rec = AnimationRecording(canvas.handle.scene)
        rec.capture_frame()
        assert "assets" in rec.to_dict()
