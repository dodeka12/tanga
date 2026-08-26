# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Ellipsoid and ellipse visualization-only entity data classes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ._coerce import to_direction, to_float, to_point, to_triple
from .direction import Direction
from .point import Point

if TYPE_CHECKING:
    from pytanga.geometry.operators import Rotor


@dataclass(frozen=True)
class Ellipsoid:
    """A solid ellipsoid in 3D space, purely for visualization.

    Unlike the MV-backed entities in this package, an :class:`Ellipsoid` has
    **no** multivector representation — it cannot be passed to
    :func:`~pytanga.geometry.create` or produced by
    :func:`~pytanga.geometry.analyze`.  It exists only as a rendering hint for
    the visualizer.

    Parameters
    ----------
    center:
        Center of the ellipsoid (default ``(0, 0, 0)``).
    radii:
        Per-axis radii ``(rx, ry, rz)`` along the local axes (default
        ``(1, 1, 1)``).
    rotation:
        Optional :class:`~pytanga.geometry.Rotor` orienting the ellipsoid.
        ``None`` means axis-aligned.
    """

    center: Point
    radii: tuple[float, float, float]
    rotation: Rotor | None = None

    def __init__(self, center=None, radii=None, rotation=None):
        center = Point(0.0, 0.0, 0.0) if center is None else to_point(center)
        radii = (1.0, 1.0, 1.0) if radii is None else to_triple(radii)

        object.__setattr__(self, "center", center)
        object.__setattr__(self, "radii", radii)
        object.__setattr__(self, "rotation", rotation)

    def __repr__(self) -> str:
        return (
            f"Ellipsoid(c={self.center}, radii=({self.radii[0]:.2f}, "
            f"{self.radii[1]:.2f}, {self.radii[2]:.2f}), rot={self.rotation})"
        )


@dataclass(frozen=True)
class Ellipse:
    """A filled ellipse (a flat, elliptical slab) in 3D space, purely for visualization.

    Unlike the MV-backed entities in this package, an :class:`Ellipse` has **no**
    multivector representation — it exists only as a rendering hint for the
    visualizer.

    The ellipse lies in the plane perpendicular to ``normal``, centered on
    ``center``, with semi-axis radii ``radius_u`` / ``radius_v``.  ``normal``
    defaults to ``Direction(0, 0, 1)`` (the positive z-axis), the natural choice
    for 2D use cases where the ellipse lies in the xy-plane.  The slab thickness
    is a style knob (``EllipseStyle.thickness``), not a geometric field.

    Parameters
    ----------
    center:
        Center of the ellipse (default ``(0, 0, 0)``).
    radius_u:
        First semi-axis radius (default ``1.0``).
    radius_v:
        Second semi-axis radius (default ``0.5``).
    normal:
        Normal direction of the ellipse plane (default ``+z``).
    """

    center: Point
    radius_u: float
    radius_v: float
    normal: Direction | None = None

    def __init__(self, center=None, radius_u=None, radius_v=None, normal=None):
        center = Point(0.0, 0.0, 0.0) if center is None else to_point(center)
        radius_u = 1.0 if radius_u is None else to_float(radius_u)
        radius_v = 0.5 if radius_v is None else to_float(radius_v)
        normal = (
            Direction(0.0, 0.0, 1.0) if normal is None else to_direction(normal)
        )

        object.__setattr__(self, "center", center)
        object.__setattr__(self, "radius_u", radius_u)
        object.__setattr__(self, "radius_v", radius_v)
        object.__setattr__(self, "normal", normal)

    def __repr__(self) -> str:
        return (
            f"Ellipse(c={self.center}, ru={self.radius_u:.2f}, "
            f"rv={self.radius_v:.2f}, n={self.normal})"
        )
