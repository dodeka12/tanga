# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the depth-image data model (`depth_image.py`)."""

from __future__ import annotations

import numpy as np
import pytest

from pytanga.viz import (
    DepthColormap,
    DepthImage,
    DepthImageData,
    DepthImageMode,
    DepthImageStyle,
    EImageCodec,
)
from pytanga.viz._styles import _style_to_output
from pytanga.viz.depth_image import DEFAULT_MISSING_DEPTH, MAX_SELECTED_SEGMENTS


def _resolved(**overrides: object) -> dict[str, object]:
    """A fully-resolved style dict (canonical defaults + overrides)."""
    style: dict[str, object] = _style_to_output(None, "DepthImage")
    style.update(overrides)
    return style


class TestEnums:
    def test_modes(self) -> None:
        assert DepthImageMode.DEPTH == 0
        assert DepthImageMode.IMAGE == 1
        assert DepthImageMode.PLAIN == 2
        assert DepthImageMode.from_str("image") is DepthImageMode.IMAGE

    def test_colormaps(self) -> None:
        assert DepthColormap.VIRIDIS == 0
        assert DepthColormap.TURBO == 1
        assert DepthColormap.GRAY == 2
        assert DepthColormap.from_str("grayscale") is DepthColormap.GRAY


class TestDepthImageData:
    def test_depth_required(self) -> None:
        with pytest.raises(ValueError, match="depth is required"):
            DepthImageData(depth=None)  # type: ignore[arg-type]

    def test_nonfinite_depth_to_sentinel(self) -> None:
        arr = np.array([[1.0, np.nan], [np.inf, 0.5]], dtype=np.float32)
        data = DepthImageData(depth=arr)
        assert data.depth.dtype == np.float32
        assert data.depth[0, 1] == pytest.approx(DEFAULT_MISSING_DEPTH)
        assert data.depth[1, 0] == pytest.approx(DEFAULT_MISSING_DEPTH)
        assert data.depth[1, 1] == pytest.approx(0.5)

    def test_frame_falls_back_to_depth(self) -> None:
        data = DepthImageData(depth=np.zeros((5, 7), np.float32))
        assert data.frame == (7, 5)

    def test_frame_uses_image(self) -> None:
        data = DepthImageData(
            depth=np.zeros((5, 7), np.float32),
            image=np.zeros((20, 30, 3), np.uint8),
        )
        assert data.frame == (30, 20)

    def test_invalid_segmentation_ndim(self) -> None:
        with pytest.raises(ValueError, match="segmentation must be 2-D"):
            DepthImageData(
                depth=np.zeros((4, 4), np.float32),
                segmentation=np.zeros((4, 4, 1), np.uint8),
            )

    def test_segmentation_ids(self) -> None:
        data = DepthImageData(
            depth=np.zeros((4, 4), np.float32),
            segmentation=np.array([[0, 2], [1, 2]], np.uint8),
        )
        assert data.segmentation_ids() == [0, 1, 2]

    def test_segmentation_preserves_uint8(self) -> None:
        data = DepthImageData(
            depth=np.zeros((4, 4), np.float32),
            segmentation=np.array([[0, 2], [1, 2]], np.uint8),
        )
        assert data.segmentation.dtype == np.uint8
        assert data.segmentation[0, 1] == 2


class TestDepthImageBuild:
    def test_mesh_and_depth_downscale(self) -> None:
        depth_img = DepthImage(DepthImageData(depth=np.zeros((10, 12), np.float32)))
        content, frames = depth_img._build(_resolved(), "d0")
        assert content["frame"] == {"width": 12, "height": 10}
        # Mesh resolution follows the depth resolution (one vertex per sample).
        assert content["mesh"]["segments_u"] == 11
        assert content["mesh"]["segments_v"] == 9
        # depth is transmitted at (segments_u + 1) × (segments_v + 1)
        assert content["depth"]["width"] == 12
        assert content["depth"]["height"] == 10
        assert frames[0].data is not None and frames[0].data.shape == (10, 12)

    def test_mesh_scale_cap(self) -> None:
        depth_img = DepthImage(DepthImageData(depth=np.zeros((40, 60), np.float32)))
        content, _ = depth_img._build(_resolved(mesh_scale=0.5, max_mesh_size=10), "d0")
        assert content["mesh"]["segments_u"] == 9
        assert content["mesh"]["segments_v"] == 6  # 40*0.5=20 → capped 20*(10/30)

    def test_image_downscale(self) -> None:
        depth_img = DepthImage(
            DepthImageData(
                depth=np.zeros((10, 12), np.float32),
                image=np.zeros((40, 60, 3), np.uint8),
            )
        )
        content, frames = depth_img._build(_resolved(image_scale=0.5), "d0")
        assert content["image"] is not None
        assert content["image"]["width"] == 30
        assert content["image"]["height"] == 20
        image_frame = frames[1]
        assert image_frame.data is not None and image_frame.data.shape == (20, 30, 3)

    def test_segmentation_follows_image_scale(self) -> None:
        depth_img = DepthImage(
            DepthImageData(
                depth=np.zeros((10, 12), np.float32),
                image=np.zeros((40, 60, 3), np.uint8),
                segmentation=np.zeros((40, 60), np.uint8),
            )
        )
        content, _ = depth_img._build(_resolved(image_scale=0.5), "d0")
        assert content["segmentation"]["width"] == 30
        assert content["segmentation"]["height"] == 20

    def test_codec_jpeg_falls_back_for_depth(self) -> None:
        depth_img = DepthImage(DepthImageData(depth=np.zeros((8, 8), np.float32)))
        _, frames = depth_img._build(_resolved(codec=EImageCodec.JPEG), "d0")
        assert frames[0].codec is EImageCodec.ZLIB

    def test_segmentation_uint8_is_lossless_by_default(self) -> None:
        depth_img = DepthImage(
            DepthImageData(
                depth=np.zeros((8, 8), np.float32),
                segmentation=np.zeros((8, 8), np.uint8),
            )
        )
        _, frames = depth_img._build(_resolved(), "d0")
        seg_frame = frames[-1]
        assert seg_frame.codec is EImageCodec.ZLIB

    def test_codec_jpeg_for_uint8_image(self) -> None:
        depth_img = DepthImage(
            DepthImageData(
                depth=np.zeros((8, 8), np.float32),
                image=np.zeros((8, 8, 3), np.uint8),
            )
        )
        _, frames = depth_img._build(_resolved(codec=EImageCodec.JPEG), "d0")
        assert frames[1].codec is EImageCodec.JPEG

    def test_custom_uniforms_and_segments(self) -> None:
        depth_img = DepthImage(
            DepthImageData(depth=np.zeros((8, 8), np.float32)),
            uniforms={"u_angle": 0.5},
            selected_segments=[1, 2],
        )
        content, _ = depth_img._build(_resolved(), "d0")
        uniforms = content["uniforms"]
        assert uniforms["u_angle"] == 0.5
        assert uniforms["u_seg_enabled"] == 1
        assert uniforms["u_num_selected"] == 2
        assert uniforms["u_selected_segments"][:2] == [1, 2]
        assert len(uniforms["u_selected_segments"]) == MAX_SELECTED_SEGMENTS


class TestDepthImageStyle:
    def test_to_dict(self) -> None:
        style = DepthImageStyle(
            mesh_scale=0.25,
            render_mode="image",
            codec=EImageCodec.ZLIB,
        )
        result = style.to_dict()
        assert result["style_type"] == "DepthImageStyle"
        assert result["mesh_scale"] == 0.25
        assert result["render_mode"] == "image"
        assert result["codec"] == int(EImageCodec.ZLIB)

    def test_canonical_defaults(self) -> None:
        merged = _style_to_output(None, "DepthImage")
        assert merged["render_mode"] == "depth"
        assert merged["colormap"] == "turbo"
        assert merged["mesh_scale"] == 1.0
        assert merged["max_mesh_size"] == 512
        assert merged["world_scale"] == 1.0
        assert merged["depth_min"] == 0.0
        assert merged["depth_max"] == 1.0
        assert merged["discard_missing"] is True
        assert merged["double_sided"] is True
