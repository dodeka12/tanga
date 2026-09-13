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
from dataclasses import dataclass
from enum import IntEnum

import numpy as np

__all__ = [
    "ImageDType",
    "ImageData",
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


@dataclass
class ImageData:
    """A single image: a numpy pixel buffer or a URL, with its metadata.

    ``data`` and ``url`` are mutually exclusive.  When ``data`` is given,
    ``width``/``height``/``channels``/``dtype`` default to values derived from
    the array; when ``url`` is given they are all required.
    """

    id: str
    data: np.ndarray | None = None
    url: str | None = None
    width: int | None = None
    height: int | None = None
    channels: int | None = None
    dtype: ImageDType | None = None

    def __post_init__(self) -> None:
        if (self.data is None) == (self.url is None):
            raise ValueError("ImageData needs exactly one of `data` or `url`")

        if self.data is not None:
            self._validate_array()
        elif None in (self.width, self.height, self.channels, self.dtype):
            raise ValueError(
                "`width`, `height`, `channels`, and `dtype` are required "
                "when `url` is given instead of `data`"
            )

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
        """``"data"`` when pixel data is embedded, ``"url"`` when loaded."""
        return "url" if self.url is not None else "data"

    def to_bytes(self) -> bytes:
        """Return the C-contiguous pixel buffer (raises for URL images)."""
        if self.data is None:
            raise ValueError("URL images have no pixel buffer")
        return self.data.tobytes()

    def to_base64(self) -> str:
        """Return the pixel buffer as base64 (for HTML export embedding)."""
        return base64.b64encode(self.to_bytes()).decode("ascii")
