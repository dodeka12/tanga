# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Coordinate-frame (axis-convention) types.

A :class:`CoordinateFrame` names where a child frame's ``+x``/``+y``/``+z`` axes
point in the parent (right-handed) frame, and exposes the 4×4 change-of-basis
matrix via :meth:`CoordinateFrame.to_matrix` (so it satisfies ``MatrixProvider``
and can be passed to ``set_transform``).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from pytanga.entity.direction import Direction

__all__ = ["CoordinateFrame", "OpenCVFrame"]


def _v(d: Direction) -> np.ndarray:
    return np.array([d.x, d.y, d.z], dtype=float)


@dataclass(frozen=True)
class CoordinateFrame:
    """Axis convention: where ``+x``/``+y``/``+z`` point in the parent frame."""

    x: Direction
    y: Direction
    z: Direction

    def to_matrix(self) -> np.ndarray:
        """Return the 4×4 homogeneous change-of-basis (columns = ``x``/``y``/``z``)."""
        m = np.eye(4)
        m[0:3, 0] = _v(self.x)
        m[0:3, 1] = _v(self.y)
        m[0:3, 2] = _v(self.z)
        return m

    def handedness(self) -> int:
        """Return ``+1`` (right-handed) or ``-1`` (left-handed)."""
        basis = np.column_stack([_v(self.x), _v(self.y), _v(self.z)])
        return 1 if float(np.linalg.det(basis)) > 0.0 else -1


class OpenCVFrame(CoordinateFrame):
    """The OpenCV camera convention: x right, y down, z forward.

    A proper 180° rotation about ``+x`` relative to the standard x-right /
    y-up / z-toward-viewer frame (det = +1), so it preserves handedness.
    """

    def __init__(self) -> None:
        super().__init__(
            x=Direction(1.0, 0.0, 0.0),
            y=Direction(0.0, -1.0, 0.0),
            z=Direction(0.0, 0.0, -1.0),
        )
