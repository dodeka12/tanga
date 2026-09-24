# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the image pyramid (`_image_pyramid.py`) and its server route."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import numpy as np
import pytest
from aiohttp import web

from pytanga.viz._image_pyramid import ImagePyramid
from pytanga.viz.image import ImageData
from pytanga.viz.server import VizServer
from pytanga.viz.views._helpers import _image_meta


class TestGeometry:
    def test_levels_and_dimensions(self) -> None:
        p = ImagePyramid("i", np.zeros((100, 200), dtype=np.uint8), tile_size=256)
        assert p.levels == 9  # ceil(log2(200)) + 1
        assert p.dimensions(0) == (100, 200)
        assert p.dimensions(1) == (50, 100)
        assert p.grid(0) == (1, 1)

    def test_grid_edge_tiles(self) -> None:
        p = ImagePyramid("i", np.zeros((300, 300), dtype=np.uint8), tile_size=256)
        assert p.grid(0) == (2, 2)  # ceil(300 / 256)

    def test_dimensions_out_of_range(self) -> None:
        p = ImagePyramid("i", np.zeros((10, 10), dtype=np.uint8), tile_size=256)
        with pytest.raises(ValueError, match="out of range"):
            p.dimensions(p.levels)


class TestTiles:
    def test_jpeg_tile(self) -> None:
        p = ImagePyramid("i", np.zeros((64, 64, 3), dtype=np.uint8), tile_size=32)
        data = p.get_tile(0, 0, 0, "jpeg")
        assert data is not None
        assert data[:2] == b"\xff\xd8"  # JPEG SOI marker

    def test_raw_tile_is_lossless(self) -> None:
        arr = np.arange(64, dtype=np.uint16).reshape(8, 8)
        p = ImagePyramid("i", arr, tile_size=4)
        data = p.get_tile(0, 1, 1, "raw")
        assert data == arr[4:8, 4:8].tobytes()

    def test_png_tile(self) -> None:
        p = ImagePyramid("i", np.zeros((32, 32), dtype=np.uint16), tile_size=16)
        data = p.get_tile(0, 0, 0, "png")
        assert data is not None
        assert data[:8] == b"\x89PNG\r\n\x1a\n"

    def test_out_of_range_tile_returns_none(self) -> None:
        p = ImagePyramid("i", np.zeros((32, 32), dtype=np.uint8), tile_size=16)
        assert p.get_tile(0, 5, 5) is None
        assert p.get_tile(p.levels, 0, 0) is None

    def test_unknown_format_raises(self) -> None:
        p = ImagePyramid("i", np.zeros((16, 16), dtype=np.uint8))
        with pytest.raises(ValueError, match="unknown tile format"):
            p.get_tile(0, 0, 0, "bmp")


class TestLru:
    def test_cache_caps_at_bound(self) -> None:
        p = ImagePyramid("j", np.zeros((1024, 1024), dtype=np.uint8), tile_size=32)
        # 32 × 32 = 1024 tiles; request 320 distinct ones → LRU caps at 256.
        for x in range(32):
            for y in range(10):
                p.get_tile(0, x, y, "raw")
        assert len(p._cache) <= 256

    def test_cache_returns_identical_bytes(self) -> None:
        p = ImagePyramid("i", np.zeros((32, 32, 3), dtype=np.uint8), tile_size=32)
        a = p.get_tile(0, 0, 0)
        b = p.get_tile(0, 0, 0)
        assert a == b


class TestTiledSerialization:
    def test_image_data_tiled_meta(self) -> None:
        p = ImagePyramid("n", np.zeros((64, 64, 3), dtype=np.uint8), tile_size=32)
        img = ImageData("n", tiled=p)
        assert img.source == "tiled"
        meta = _image_meta(img)
        assert meta["source"] == "tiled"
        assert meta["tile_size"] == 32
        assert meta["levels"] == p.levels
        assert (meta["width"], meta["height"]) == (64, 64)

    def test_image_data_tiled_conflicts_with_data(self) -> None:
        p = ImagePyramid("n", np.zeros((64, 64), dtype=np.uint8))
        with pytest.raises(ValueError, match="exactly one"):
            ImageData("n", tiled=p, data=np.zeros((2, 2), dtype=np.uint8))

    def test_tiled_meta_requires_tiled_source(self) -> None:
        with pytest.raises(ValueError, match="no tiled source"):
            ImageData("n", data=np.zeros((2, 2), dtype=np.uint8)).tiled_meta


class TestServerRoute:
    def test_serves_jpeg_tile(self) -> None:
        server = VizServer()
        server.register_image_pyramid(
            "i", ImagePyramid("i", np.zeros((64, 64, 3), dtype=np.uint8), tile_size=32)
        )
        req = SimpleNamespace(
            match_info={"image_id": "i", "level": "0", "x": "0", "y": "0"}, query={}
        )
        resp = asyncio.run(server._image_tile_handler(req))  # type: ignore[arg-type]
        assert isinstance(resp, web.Response)
        assert resp.status == 200
        assert resp.content_type == "image/jpeg"
        assert resp.body[:2] == b"\xff\xd8"

    def test_unknown_image_400(self) -> None:
        server = VizServer()
        req = SimpleNamespace(
            match_info={"image_id": "nope", "level": "0", "x": "0", "y": "0"}, query={}
        )
        with pytest.raises(web.HTTPBadRequest):
            asyncio.run(server._image_tile_handler(req))  # type: ignore[arg-type]

    def test_out_of_range_404(self) -> None:
        server = VizServer()
        server.register_image_pyramid(
            "i", ImagePyramid("i", np.zeros((64, 64, 3), dtype=np.uint8), tile_size=32)
        )
        req = SimpleNamespace(
            match_info={"image_id": "i", "level": "0", "x": "99", "y": "99"}, query={}
        )
        with pytest.raises(web.HTTPNotFound):
            asyncio.run(server._image_tile_handler(req))  # type: ignore[arg-type]
