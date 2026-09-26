# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Image pyramid — serve a large image as on-demand level/tile regions.

A pyramid tiles a single numpy image (``uint8``/``uint16``/``float32``, 1/3/4
channels) into square tiles at decreasing resolutions (level 0 = full
resolution; each level halves dimensions).  :meth:`ImagePyramid.get_tile`
encodes a requested region on demand.  Pure data + optional Pillow, no server
imports, mirroring ``image.py``/``camera.py``.
"""

from __future__ import annotations

import io
import threading
from collections import OrderedDict
from typing import Any

import numpy as np

from ._image_wire import encode_zlib_raw
from .image import ImageDType

#: Tile ``format`` → HTTP ``Content-Type``.
FORMAT_CONTENT_TYPE: dict[str, str] = {
    "jpeg": "image/jpeg",
    "png": "image/png",
    "raw": "application/octet-stream",
    "zlib": "application/octet-stream",
}


def format_content_type(format: str) -> str:
    """Return the HTTP ``Content-Type`` for a tile ``format``."""
    return FORMAT_CONTENT_TYPE[format]


#: Bounded size of the per-pyramid encoded-tile LRU.
_DEFAULT_CACHE_SIZE = 256


def _encode_jpeg(tile: np.ndarray) -> bytes:
    if tile.dtype != np.dtype("uint8") or tile.ndim not in (2, 3) or (
        tile.ndim == 3 and tile.shape[2] != 3
    ):
        raise ValueError(
            f"jpeg format requires uint8 1/3-channel tiles, got "
            f"dtype={tile.dtype!r}, shape={tile.shape}"
        )
    try:
        from PIL import Image
    except ImportError as exc:
        raise ImportError("JPEG tile encoding requires Pillow") from exc
    mode = "L" if tile.ndim == 2 else "RGB"
    image = Image.fromarray(np.ascontiguousarray(tile), mode=mode)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    return buffer.getvalue()


def _encode_png(tile: np.ndarray) -> bytes:
    try:
        from PIL import Image
    except ImportError as exc:
        raise ImportError("PNG tile encoding requires Pillow") from exc
    arr = np.ascontiguousarray(tile)

    # PNG has no float32 or multi-channel uint16 mode, so normalize those to
    # 8-bit using the default value range (float32 → [0, 1], uint16 → [0, 65535])
    # — matching `ImageDType.default_value_range` — before encoding.
    if arr.dtype == np.dtype("float32"):
        arr = (np.clip(arr, 0.0, 1.0) * 255.0).astype(np.uint8)
    elif arr.dtype == np.dtype("uint16") and arr.ndim == 3 and arr.shape[2] != 1:
        arr = (arr.astype(np.float32) * (255.0 / 65535.0)).astype(np.uint8)

    if arr.ndim == 2:
        mode = None if arr.dtype == np.dtype("uint16") else "L"
    elif arr.ndim == 3:
        channels = arr.shape[2]
        if arr.dtype == np.dtype("uint16"):
            if channels != 1:
                raise ValueError("PNG format supports only single-channel uint16 tiles")
            mode = None
            arr = arr[:, :, 0]
        else:
            mode = {1: "L", 3: "RGB", 4: "RGBA"}[channels]
            if channels == 1:
                arr = arr[:, :, 0]
    else:
        raise ValueError(f"unexpected tile ndim {arr.ndim}")
    image = Image.fromarray(arr) if mode is None else Image.fromarray(arr, mode=mode)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


class ImagePyramid:
    """A lazily-built tile pyramid over a single large numpy image.

    Level 0 is the full-resolution image; each level halves the dimensions.
    Tiles are square (``tile_size``, default 256) with edge tiles clipped.
    """

    def __init__(self, image_id: str, data: np.ndarray, *, tile_size: int = 256) -> None:
        if data.ndim not in (2, 3):
            raise ValueError(f"expected a 2-D or 3-D array, got ndim={data.ndim}")
        if data.ndim == 3 and data.shape[2] not in (1, 3, 4):
            raise ValueError(
                f"expected 1, 3, or 4 channels, got {data.shape[2]}"
            )
        if tile_size <= 0:
            raise ValueError("tile_size must be positive")
        self.image_id = image_id
        self.data = np.ascontiguousarray(data)
        self.tile_size = int(tile_size)
        self.dtype = ImageDType.from_numpy(self.data)
        self.channels = 1 if self.data.ndim == 2 else int(self.data.shape[2])
        self._cache: OrderedDict[tuple[int, int, int, str], bytes] = OrderedDict()
        self._lock = threading.Lock()

    def meta(self) -> dict[str, Any]:
        """Return the serialized ``source: "tiled"`` metadata for the frontend."""
        return {
            "id": self.image_id,
            "width": self.data.shape[1],
            "height": self.data.shape[0],
            "tile_size": self.tile_size,
            "levels": self.levels,
            "dtype": self.dtype.value,
            "channels": self.channels,
            "source": "tiled",
        }

    # -- geometry -------------------------------------------------

    @property
    def levels(self) -> int:
        """Number of pyramid levels (level 0 = full resolution)."""
        height, width = self.data.shape[0], self.data.shape[1]
        return int(np.ceil(np.log2(max(height, width)))) + 1

    def dimensions(self, level: int) -> tuple[int, int]:
        """Return ``(height, width)`` at *level*."""
        if level < 0 or level >= self.levels:
            raise ValueError(f"level {level} out of range [0, {self.levels - 1}]")
        scale = 2**level
        return (
            int(np.ceil(self.data.shape[0] / scale)),
            int(np.ceil(self.data.shape[1] / scale)),
        )

    def grid(self, level: int) -> tuple[int, int]:
        """Return ``(rows, cols)`` of tiles at *level*."""
        height, width = self.dimensions(level)
        return (
            int(np.ceil(height / self.tile_size)),
            int(np.ceil(width / self.tile_size)),
        )

    # -- tiles ----------------------------------------------------

    def get_tile(self, level: int, x: int, y: int, format: str = "jpeg") -> bytes | None:
        """Return the encoded tile bytes, or ``None`` if the tile is out of range."""
        if format not in FORMAT_CONTENT_TYPE:
            raise ValueError(f"unknown tile format {format!r}")
        if level < 0 or level >= self.levels:
            return None
        rows, cols = self.grid(level)
        if x < 0 or y < 0 or x >= cols or y >= rows:
            return None

        key = (level, x, y, format)
        with self._lock:
            cached = self._cache.get(key)
            if cached is not None:
                self._cache.move_to_end(key)
                return cached

        encoded = self._encode(self._extract_tile(level, x, y), format)
        with self._lock:
            self._cache[key] = encoded
            self._cache.move_to_end(key)
            while len(self._cache) > _DEFAULT_CACHE_SIZE:
                self._cache.popitem(last=False)
        return encoded

    def _extract_tile(self, level: int, x: int, y: int) -> np.ndarray:
        scale = 2**level
        downsampled = self.data[::scale, ::scale]
        row0 = y * self.tile_size
        col0 = x * self.tile_size
        return downsampled[row0 : row0 + self.tile_size, col0 : col0 + self.tile_size]

    def _encode(self, tile: np.ndarray, format: str) -> bytes:
        if format == "raw":
            return np.ascontiguousarray(tile).tobytes()
        if format == "zlib":
            return encode_zlib_raw(tile)
        if format == "png":
            return _encode_png(tile)
        return _encode_jpeg(tile)
