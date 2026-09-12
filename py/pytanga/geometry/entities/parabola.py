# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Parabola entity data class."""

from __future__ import annotations

from dataclasses import dataclass

from ._coerce import to_direction, to_float, to_point
from .direction import Direction
from .point import Point


@dataclass(frozen=True)
class Parabola:
    """A 2D parabola given by its vertex, axis direction and focal parameter.

    ``p`` is the focal parameter (half the latus rectum); in the vertex frame
    the parabola is ``y² = 2 p x`` along ``direction``.
    """

    vertex: Point
    direction: Direction
    p: float

    def __init__(self, vertex, direction, p):
        object.__setattr__(self, "vertex", to_point(vertex))
        object.__setattr__(self, "direction", to_direction(direction))
        object.__setattr__(self, "p", to_float(p))

    def __repr__(self) -> str:
        return f"Parabola(v={self.vertex}, dir={self.direction}, p={self.p:.2f})"
