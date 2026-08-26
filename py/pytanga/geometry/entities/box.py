# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Box visualization-only entity data class."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ._coerce import to_point, to_triple
from .point import Point

if TYPE_CHECKING:
    from pytanga.geometry.operators import Rotor


@dataclass(frozen=True)
class Box:
    """A solid box in 3D space, purely for visualization.

    Unlike the MV-backed entities in this package, a :class:`Box` has **no**
    multivector representation — it cannot be passed to
    :func:`~pytanga.geometry.create` or produced by
    :func:`~pytanga.geometry.analyze`.  It exists only as a rendering hint for
    the visualizer.

    Parameters
    ----------
    center:
        Center of the box (default ``(0, 0, 0)``).
    size:
        Full side lengths ``(sx, sy, sz)`` along the local axes (default
        ``(1, 1, 1)``).  Half-extents are ``size / 2``.
    rotation:
        Optional :class:`~pytanga.geometry.Rotor` orienting the box.  ``None``
        means axis-aligned.
    """

    center: Point
    size: tuple[float, float, float]
    rotation: Rotor | None = None

    def __init__(self, center=None, size=None, rotation=None):
        center = Point(0.0, 0.0, 0.0) if center is None else to_point(center)
        size = (1.0, 1.0, 1.0) if size is None else to_triple(size)

        object.__setattr__(self, "center", center)
        object.__setattr__(self, "size", size)
        object.__setattr__(self, "rotation", rotation)

    def __repr__(self) -> str:
        return (
            f"Box(c={self.center}, size=({self.size[0]:.2f}, "
            f"{self.size[1]:.2f}, {self.size[2]:.2f}), rot={self.rotation})"
        )
