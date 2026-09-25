# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the MJPEG camera stream (`_camera_stream.py`) and its route."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import numpy as np
import pytest
from aiohttp import web

from pytanga.viz._camera_stream import CameraStream
from pytanga.viz.image import ImageData
from pytanga.viz.server import VizServer


class TestCameraStream:
    def test_publish_updates_latest_jpeg(self) -> None:
        stream = CameraStream("cam")
        stream.publish(np.zeros((4, 4, 3), dtype=np.uint8))
        latest = stream.latest()
        assert latest is not None
        assert latest[:2] == b"\xff\xd8"  # JPEG SOI marker

    def test_publish_accepts_image_data(self) -> None:
        stream = CameraStream("cam")
        stream.publish(ImageData("cam", data=np.zeros((4, 4, 3), dtype=np.uint8)))
        assert stream.latest() is not None

    def test_publish_replaces_previous_frame(self) -> None:
        stream = CameraStream("cam")
        stream.publish(np.zeros((4, 4, 3), dtype=np.uint8))
        first = stream.latest()
        stream.publish(np.full((4, 4, 3), 255, dtype=np.uint8))
        assert stream.latest() is not None
        assert stream.latest() != first

    def test_publish_rejects_non_array(self) -> None:
        stream = CameraStream("cam")
        with pytest.raises(TypeError, match="numpy array or ImageData"):
            stream.publish("not an image")

    def test_fps_must_be_positive(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            CameraStream("cam", fps=0)


class TestServerRoute:
    def test_unknown_stream_400(self) -> None:
        server = VizServer()
        req = SimpleNamespace(match_info={"stream_id": "nope"})
        with pytest.raises(web.HTTPBadRequest):
            asyncio.run(server._camera_stream_handler(req))  # type: ignore[arg-type]
