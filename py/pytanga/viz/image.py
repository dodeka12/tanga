# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Image value types and the optional PIL bridge for the Tanga viewer.

This module is pure data + validation (no server/rendering imports) so it stays
unit-testable in isolation, mirroring ``camera.py``.  It defines the dtype and
channel model that the image view consumes, plus :func:`pil_to_numpy` for the
optional PIL → numpy conversion (lazy import).
"""

from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from enum import IntEnum
from typing import Any

import numpy as np

from ._image_io import read_exr, read_hdr, register_loading_progress_handler

__all__ = [
    "ImageDType",
    "EImageCodec",
    "ImageData",
    "ImageChannelMode",
    "default_mode",
    "default_value_range",
    "pil_to_numpy",
    "read_exr",
    "read_hdr",
    "register_loading_progress_handler",
]


class ImageDType(IntEnum):
    """Supported image storage dtypes and their wire codes (0/1/2)."""

    UINT8 = 0
    UINT16 = 1
    FLOAT32 = 2

    @classmethod
    def from_code(cls, code: int) -> "ImageDType":
        """Convert a wire code (0/1/2) back to an enum member."""
        try:
            return cls(code)
        except ValueError as exc:
            raise ValueError(f"Unknown image dtype code: {code!r}") from exc

    def to_internal_format(self) -> str:
        """Map to the GL texture internal-format hint the frontend uses."""
        return {
            ImageDType.UINT8: "uint8",
            ImageDType.UINT16: "uint16",
            ImageDType.FLOAT32: "float32",
        }[self]

    @property
    def numpy_dtype(self) -> np.dtype:
        """The matching numpy dtype."""
        return {
            ImageDType.UINT8: np.dtype("uint8"),
            ImageDType.UINT16: np.dtype("uint16"),
            ImageDType.FLOAT32: np.dtype("float32"),
        }[self]

    @classmethod
    def from_numpy(cls, arr: np.ndarray) -> "ImageDType":
        """Infer the enum member from an array's dtype."""
        mapping = {
            np.dtype("uint8"): cls.UINT8,
            np.dtype("uint16"): cls.UINT16,
            np.dtype("float32"): cls.FLOAT32,
        }
        try:
            return mapping[arr.dtype]
        except KeyError as exc:
            raise ValueError(
                "Unsupported numpy dtype "
                f"{arr.dtype!r}; expected uint8, uint16, or float32"
            ) from exc


class EImageCodec(IntEnum):
    """Wire codecs for the binary image frame (``codec`` byte 0/1/2)."""

    RAW = 0
    JPEG = 1
    ZLIB = 2

    @classmethod
    def from_code(cls, code: int) -> "EImageCodec":
        """Convert a wire code (0/1/2) back to an enum member."""
        try:
            return cls(code)
        except ValueError as exc:
            raise ValueError(f"Unknown image codec: {code!r}") from exc


class ImageChannelMode(IntEnum):
    """How a 1/3/4-channel image is mapped to display colour (``u_mode``)."""

    GRAY = 0
    RGB = 1
    MAGNITUDE = 2
    ALPHA = 3


def default_mode(channels: int) -> int:
    """Default channel mode for a channel count (1 → gray, 3/4 → RGB)."""
    if channels == 1:
        return int(ImageChannelMode.GRAY)
    return int(ImageChannelMode.RGB)


def default_value_range(dtype: ImageDType) -> tuple[float, float]:
    """Default ``[min, max]`` used to normalize the raw value into ``[0, 1]``.

    ``uint8``/``float32`` default to the identity range ``[0, 1]``; ``uint16``
    defaults to ``[0, 65535]``.  A caller with a ``float32`` array of arbitrary
    range should override these with the data's own min/max.
    """
    if dtype is ImageDType.UINT16:
        return (0.0, 65535.0)
    return (0.0, 1.0)


@dataclass
class ImageData:
    """A single image: a numpy pixel buffer, a URL, or an on-demand tile pyramid.

    ``data`` and ``url`` are mutually exclusive.  When ``data`` is given,
    ``width``/``height``/``channels``/``dtype`` default to values derived from
    the array; when ``url`` is given they are all required.

    A ``data`` array whose longest side exceeds ``tile_max_dim`` or whose byte
    size exceeds ``tile_max_bytes`` is automatically converted into a lazily
    built tile pyramid (``tiled``), so very large images are fetched on demand
    by the frontend instead of being sent in one frame.  Pass
    ``tile_max_dim=None`` and ``tile_max_bytes=None`` (or an explicit
    ``tiled``) to opt out.
    """

    id: str
    data: np.ndarray | None = None
    url: str | None = None
    width: int | None = None
    height: int | None = None
    channels: int | None = None
    dtype: ImageDType | None = None
    codec: EImageCodec | None = None
    jpeg_quality: int | None = None
    tiled: Any | None = None
    tile_max_dim: int | None = 4096
    tile_max_bytes: int | None = 32 * 1024 * 1024
    tile_size: int = 256

    def __post_init__(self) -> None:
        self._maybe_auto_tile()

        if self.tiled is not None:
            if self.data is not None or self.url is not None:
                raise ValueError(
                    "ImageData needs exactly one of `data`, `url`, or `tiled`"
                )
            pyramid = self.tiled
            self.width = int(pyramid.data.shape[1])
            self.height = int(pyramid.data.shape[0])
            self.channels = int(pyramid.channels)
            self.dtype = pyramid.dtype
            return

        if (self.data is None) == (self.url is None):
            raise ValueError("ImageData needs exactly one of `data`, `url`, or `tiled`")

        if self.data is not None:
            self._validate_array()
        elif None in (self.width, self.height, self.channels, self.dtype):
            raise ValueError(
                "`width`, `height`, `channels`, and `dtype` are required "
                "when `url` is given instead of `data`"
            )

    def _maybe_auto_tile(self) -> None:
        """Replace a large pixel buffer with a lazily built tile pyramid.

        Runs only when ``data`` (not an explicit ``tiled``) is provided and its
        longest side or byte size exceeds the configured thresholds.  The
        pyramid keeps a reference to the same array, so no pixels are copied
        until a tile is requested.
        """
        if self.data is None or self.tiled is not None:
            return
        if self.data.ndim not in (2, 3):
            return  # invalid array — let _validate_array raise the proper error
        if self.data.ndim == 3 and self.data.shape[2] not in (1, 3, 4):
            return  # invalid channel count — let _validate_array raise
        height, width = self.data.shape[0], self.data.shape[1]
        if self.tile_max_dim is not None and max(height, width) > self.tile_max_dim:
            should_tile = True
        elif self.tile_max_bytes is not None and self.data.nbytes > self.tile_max_bytes:
            should_tile = True
        else:
            should_tile = False
        if not should_tile:
            return
        from ._image_pyramid import ImagePyramid

        self.tiled = ImagePyramid(self.id, self.data, tile_size=self.tile_size)
        self.data = None

    def _validate_array(self) -> None:
        """Derive and check metadata from the pixel buffer (and force C-order)."""
        arr = self.data
        assert arr is not None  # guarded by __post_init__

        dtype = ImageDType.from_numpy(arr)

        if arr.ndim == 2:
            channels = 1
        elif arr.ndim == 3:
            channels = int(arr.shape[2])
        else:
            raise ValueError(
                f"Expected a 2-D (H×W) or 3-D (H×W×C) array, got ndim={arr.ndim}"
            )

        if channels not in (1, 3, 4):
            raise ValueError(f"ImageData supports 1, 3, or 4 channels, got {channels}")

        height = int(arr.shape[0])
        width = int(arr.shape[1])

        for provided, derived, name in (
            (self.dtype, dtype, "dtype"),
            (self.channels, channels, "channels"),
            (self.width, width, "width"),
            (self.height, height, "height"),
        ):
            if provided is not None and provided != derived:
                raise ValueError(
                    f"ImageData {name}={provided!r} does not match the array "
                    f"({derived!r})"
                )

        self.dtype = dtype
        self.channels = channels
        self.width = width
        self.height = height

        if not arr.flags["C_CONTIGUOUS"]:
            arr = np.ascontiguousarray(arr)
        self.data = arr

    @property
    def source(self) -> str:
        """``"data"``/``"url"``/``"tiled"`` depending on the backing source."""
        if self.tiled is not None:
            return "tiled"
        return "url" if self.url is not None else "data"

    @property
    def tiled_meta(self) -> dict[str, Any]:
        """Return the serialized ``source: "tiled"`` metadata (raises if not tiled)."""
        if self.tiled is None:
            raise ValueError("ImageData has no tiled source")
        return self.tiled.meta()

    @property
    def supports_jpeg(self) -> bool:
        """``True`` when the image can be lossily encoded as JPEG.

        JPEG is 8-bit and has no alpha, so only ``uint8`` images with 1 or 3
        channels qualify.  Everything else falls back to a lossless codec.
        """
        return self.dtype is ImageDType.UINT8 and self.channels in (1, 3)

    def to_bytes(self) -> bytes:
        """Return the C-contiguous pixel buffer (raises for URL images)."""
        if self.data is None:
            raise ValueError("URL images have no pixel buffer")
        return self.data.tobytes()

    def to_base64(self) -> str:
        """Return the pixel buffer as base64 (for HTML export embedding)."""
        return base64.b64encode(self.to_bytes()).decode("ascii")

    def to_jpeg_data_url(self, quality: int = 85) -> str:
        """Return the image as a ``data:image/jpeg;base64,…`` URL (lazy Pillow).

        Only ``uint8`` images with 1 or 3 channels qualify.  Raises
        :class:`ImportError` when Pillow is unavailable and :class:`ValueError`
        for other dtypes/channel counts.
        """
        if not self.supports_jpeg:
            raise ValueError(
                "JPEG export requires a uint8 image with 1 or 3 channels, "
                f"got dtype={self.dtype!r}, channels={self.channels!r}"
            )
        if self.data is None:
            raise ValueError("URL images have no pixel buffer")
        try:
            from PIL import Image
        except ImportError as exc:
            raise ImportError(
                "JPEG encoding requires Pillow; install it (e.g. `pip install pillow`)"
            ) from exc

        mode = "L" if self.data.ndim == 2 else "RGB"
        image = Image.fromarray(self.data, mode=mode)
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=quality)
        return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode(
            "ascii"
        )


def pil_to_numpy(img: Any, *, dtype: str = "uint8") -> np.ndarray:
    """Convert a PIL image to a numpy array, mapping modes to channels.

    PIL is imported lazily so ``pytanga`` never requires Pillow at import time;
    a clear :class:`ImportError` is raised when it is unavailable.

    Mode mapping: ``L``→1 channel, ``RGB``→3, ``RGBA``→4, ``I;16``→uint16,
    ``F``→float32.  *dtype* requests the output storage dtype (``"uint8"``,
    ``"uint16"``, or ``"float32"``); pixel values are preserved (no rescale).
    """
    try:
        import PIL  # noqa: F401  # availability check only
    except ImportError as exc:
        raise ImportError(
            "pil_to_numpy requires Pillow; install it (e.g. `pip install pillow`)"
        ) from exc

    target = np.dtype(dtype)
    if target not in (np.dtype("uint8"), np.dtype("uint16"), np.dtype("float32")):
        raise ValueError(
            f"Unsupported target dtype {dtype!r}; expected uint8/uint16/float32"
        )

    if img.mode == "I;16":
        arr = np.asarray(img, dtype=np.uint16)
    elif img.mode == "F":
        arr = np.asarray(img, dtype=np.float32)
    else:
        arr = np.asarray(img)
        if arr.dtype != target:
            arr = arr.astype(target)

    return arr
