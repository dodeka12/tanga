# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Image value types and the optional PIL bridge for the Tanga viewer.

This module is pure data + validation (no server/rendering imports) so it stays
unit-testable in isolation, mirroring ``camera.py``.  It defines the dtype and
channel model that the image view consumes, plus :func:`pil_to_numpy` for the
optional PIL → numpy conversion (lazy import).
"""

from __future__ import annotations

from enum import IntEnum

import numpy as np

__all__ = [
    "ImageDType",
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
