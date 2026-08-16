# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Homogeneous direction (point at infinity) entity data class."""

from __future__ import annotations

from dataclasses import dataclass

from ._coerce import to_direction
from ._util import _convert_mv
from .direction import Direction


@dataclass(frozen=True)
class HDirection:
    """A homogeneous direction (point at infinity).

    Represented by ``d∧e∞`` in the conformal model, where *d* is a
    Euclidean direction vector.  Useful as a reflection operator
    (reflect in a point at infinity → maps to e∞).

    Supported algebras: N3/N2 (needs e∞)
    """

    direction: Direction

    def __init__(self, direction):
        try:
            direction = to_direction(direction)
        except TypeError:
            hd = _convert_mv("hdirection", direction)
            object.__setattr__(self, "direction", hd.direction)
            return

        object.__setattr__(self, "direction", direction)

    def __repr__(self) -> str:
        return f"HDirection(dir={self.direction})"