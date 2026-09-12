# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Homogeneous direction (point at infinity) entity data class."""

from __future__ import annotations

from dataclasses import dataclass

from ._util import _convert_mv, _is_mv
from .direction import Direction


@dataclass(frozen=True)
class HDirection:
    """A homogeneous direction (point at infinity).

    Represented by ``d∧e∞`` in the conformal model, where *d* is a
    Euclidean direction vector.  Useful as a reflection operator
    (reflect in a point at infinity → maps to e∞).

    Can be constructed from a :class:`Direction`, a multivector, or
    three components (``x, y, z``).

    Supported algebras: N3/N2 (needs e∞)
    """

    direction: Direction

    def __init__(self, direction=0.0, y=0.0, z=0.0):
        if _is_mv(direction):
            hd = _convert_mv("hdirection", direction)
            object.__setattr__(self, "direction", hd.direction)
            return

        if isinstance(direction, Direction):
            object.__setattr__(self, "direction", direction)
            return

        object.__setattr__(self, "direction", Direction(direction, y, z))

    def __repr__(self) -> str:
        return f"HDirection(dir={self.direction})"
