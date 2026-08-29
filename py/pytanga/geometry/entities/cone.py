# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Cone entity data class."""

from __future__ import annotations

from dataclasses import dataclass

from ._coerce import to_direction, to_float, to_point
from .direction import Direction
from .point import Point


@dataclass(frozen=True)
class Cone:
    """A (double) cone in 3D space.

    ``vertex`` is the apex, ``axis`` the symmetry direction (from the apex
    toward the opening), and ``half_angle`` the opening half-angle in radians.
    """

    vertex: Point
    axis: Direction
    half_angle: float

    def __init__(self, vertex, axis, half_angle):
        object.__setattr__(self, "vertex", to_point(vertex))
        object.__setattr__(self, "axis", to_direction(axis))
        object.__setattr__(self, "half_angle", to_float(half_angle))

    def __repr__(self) -> str:
        return (
            f"Cone(v={self.vertex}, axis={self.axis}, half_angle={self.half_angle:.4f})"
        )
