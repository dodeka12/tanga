# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Sphere entity data classes."""

from __future__ import annotations

from dataclasses import dataclass

from ._coerce import to_float, to_point
from ._util import _convert_mv
from .point import Point


@dataclass(frozen=True)
class Sphere:
    """A sphere in 3D space.

    For imaginary spheres (N3-only, ``S = A + ½ρ² e∞``), set
    ``is_imaginary=True``.  Imaginary spheres have ``S² = −ρ²``
    (negative squared norm — no real points).

    Can also be constructed from a single multivector (converted via
    :func:`~pytanga.geometry.analysis.analyze_sphere`).
    """

    center: Point
    radius: float
    is_imaginary: bool = False

    def __init__(self, center, radius=None, is_imaginary=False):
        try:
            center = to_point(center)
        except TypeError:
            sphere = _convert_mv("sphere", center)
            object.__setattr__(self, "center", sphere.center)
            object.__setattr__(self, "radius", sphere.radius)
            object.__setattr__(self, "is_imaginary", sphere.is_imaginary)
            return

        object.__setattr__(self, "center", center)
        object.__setattr__(self, "radius", to_float(radius))
        object.__setattr__(self, "is_imaginary", is_imaginary)

    def __repr__(self) -> str:
        prefix = "Imag" if self.is_imaginary else ""
        return f"{prefix}Sphere(c={self.center}, r={self.radius:.2f})"


@dataclass(frozen=True)
class ImagSphere(Sphere):
    """An imaginary sphere in 3D space.

    Inherits all fields from :class:`Sphere` with ``is_imaginary=True``.
    Can be used as a class-based key in :attr:`Visualizer.styles`
    (e.g. ``viz.styles[ImagSphere]``).
    """

    is_imaginary: bool = True