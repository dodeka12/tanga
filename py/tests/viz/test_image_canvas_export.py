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


class TestHtmlExport:
    def test_snapshot_embeds_jpeg_image_frames(self) -> None:
        viz, canvas = _canvas()
        canvas.set_image(ImageData("img1", data=np.zeros((4, 4, 3), dtype=np.uint8)))
        html = viz._render_snapshot_html(canvas.scene_name)  # type: ignore[attr-defined]
        assert "storeImageFrame" in html
        assert '"image_assets"' in html
        assert '"codec": "jpeg"' in html

    def test_figure_embeds_raw_image_frames(self) -> None:
        viz, canvas = _canvas()
        canvas.set_image(ImageData("img1", data=np.zeros((4, 4), dtype=np.uint16)))
        html = viz._render_figure_html(canvas.scene_name)  # type: ignore[attr-defined]
        assert "storeImageFrame" in html
        assert '"image_assets"' in html
        assert '"codec": "raw"' in html

    def test_frame_assets_records_per_frame_images(self) -> None:
        _, canvas = _canvas()
        canvas.set_image(ImageData("img1", data=np.zeros((2, 2, 3), dtype=np.uint8)))
        rec = AnimationRecording(canvas.handle.scene)
        rec.capture_frame()
        first = rec.frame_assets[0]
        assert first and first[0]["id"] == "img1"

        # Change the image and re-capture with include_images=True.
        canvas.set_image(ImageData("img1", data=np.full((2, 2, 3), 255, dtype=np.uint8)))
        rec.capture_frame(include_images=True)
        assert rec.frame_assets[1] != first

    def test_animated_export_embeds_per_frame_assets(self) -> None:
        viz, canvas = _canvas()
        canvas.set_image(ImageData("img1", data=np.zeros((4, 4, 3), dtype=np.uint8)))
        rec = AnimationRecording(canvas.handle.scene)
        rec.capture_frame()
        html = viz._render_snapshot_html(canvas.scene_name, animation=rec)  # type: ignore[attr-defined]
        assert '"frame_assets"' in html
        assert "animData.frame_assets" in html


class TestAssetStore:
    def test_data_image_captured_as_base64(self) -> None:
        # uint16 is not JPEG-eligible, so it keeps the lossless raw-base64 path.
        _, canvas = _canvas()
        arr = np.arange(12, dtype=np.uint16).reshape(3, 4)
        canvas.set_image(ImageData("img1", data=arr))
        rec = AnimationRecording(canvas.handle.scene)
        rec.capture_frame()

        asset = rec.assets["img1"]
        assert asset["source"] == "data"
        assert asset["width"] == 4 and asset["height"] == 3 and asset["channels"] == 1
        assert asset["data"] == base64.b64encode(arr.tobytes()).decode("ascii")

    def test_uint8_image_captured_as_jpeg_data_url(self) -> None:
        _, canvas = _canvas()
        arr = np.arange(24, dtype=np.uint8).reshape(2, 4, 3)
        canvas.set_image(ImageData("img1", data=arr))
        rec = AnimationRecording(canvas.handle.scene)
        rec.capture_frame()

        asset = rec.assets["img1"]
        assert asset["source"] == "url"
        assert asset["url"].startswith("data:image/jpeg;base64,")

    def test_uint8_rgba_image_captured_as_raw_base64(self) -> None:
        # 4 channels has no JPEG alpha support → lossless raw-base64 fallback.
        _, canvas = _canvas()
        arr = np.arange(32, dtype=np.uint8).reshape(2, 4, 4)
        canvas.set_image(ImageData("img1", data=arr))
        rec = AnimationRecording(canvas.handle.scene)
        rec.capture_frame()

        asset = rec.assets["img1"]
        assert asset["source"] == "data"
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
        canvas.set_image(ImageData("img1", data=np.zeros((2, 2), dtype=np.uint16)))
        rec = AnimationRecording(canvas.handle.scene)
        rec.capture_frame()
        first = rec.assets["img1"]["data"]

        # Re-capture without the flag → assets unchanged.
        rec.capture_frame()
        assert rec.assets["img1"]["data"] == first

        # Replace the image and re-capture with the flag → assets updated.
        canvas.set_image(ImageData("img1", data=np.ones((2, 2), dtype=np.uint16)))
        rec.capture_frame(include_images=True)
        assert rec.assets["img1"]["data"] != first

    def test_to_dict_includes_assets(self) -> None:
        _, canvas = _canvas()
        canvas.set_image(ImageData("img1", data=np.zeros((2, 2), dtype=np.uint8)))
        rec = AnimationRecording(canvas.handle.scene)
        rec.capture_frame()
        assert "assets" in rec.to_dict()
