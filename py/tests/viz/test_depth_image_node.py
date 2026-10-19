# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the ``VizDepthImage`` node and Scene integration."""

from __future__ import annotations

import numpy as np

from pytanga.viz import DepthImage, DepthImageData
from pytanga.viz._image_wire import decode_image_frame
from pytanga.viz._nodes import VizDepthImage
from pytanga.viz._styles import _style_to_output
from pytanga.viz.scene import Scene


class TestVizDepthImage:
    def test_serialize_envelope_and_content(self) -> None:
        payload = {
            "frame": {"width": 4, "height": 3},
            "mesh": {"segments_u": 4, "segments_v": 3},
        }
        node = VizDepthImage("d0", payload)
        serialized = node.serialize()
        assert serialized["id"] == "d0"
        assert serialized["kind"] == "depth_image"
        assert serialized["layer"] == "scene"
        assert serialized["parent_id"] is None
        assert serialized["frame"] == {"width": 4, "height": 3}
        assert "position" in serialized["transform"]
        assert serialized["visible"] is True

    def test_patch_full_and_visible(self) -> None:
        node = VizDepthImage("d0", {"mesh": {}})
        full = node.patch("full")
        assert full["aspect"] == "full"
        assert full["value"]["kind"] == "depth_image"
        node.set_visible(False)
        visible = node.patch("visible")
        assert visible["value"] == {"visible": False}


class TestSceneDepthImage:
    def test_add_and_flush(self) -> None:
        scene = Scene()
        payload = {
            "frame": {"width": 2, "height": 2},
            "depth": {
                "id": "d0.depth",
                "width": 3,
                "height": 3,
                "channels": 1,
                "dtype": 2,
                "source": "data",
            },
        }
        scene.add_depth_image("d0", payload)
        patches, removed = scene.flush()
        assert removed == []
        assert len(patches) == 1
        assert patches[0]["aspect"] == "full"
        assert patches[0]["value"]["kind"] == "depth_image"

    def test_depth_image_frames(self) -> None:
        depth_arr = np.arange(16, dtype=np.float32).reshape(4, 4)
        seg_arr = np.array([[0, 1], [2, 3]], dtype=np.uint16)
        depth = DepthImage(DepthImageData(depth=depth_arr, segmentation=seg_arr))
        content, frames = depth._build(_style_to_output(None, "DepthImage"), "d0")

        scene = Scene()
        scene.add_depth_image("d0", content, images=frames)

        ids = {fid for fid, _ in scene.depth_image_frames()}
        assert ids == {"d0.depth", "d0.seg"}
        for fid, frame in scene.depth_image_frames():
            decoded = decode_image_frame(frame)
            assert decoded["id"] == fid
            if fid == "d0.seg":
                assert decoded["channels"] == 1
                assert decoded["data"].shape == (2, 2)
