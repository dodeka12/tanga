# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Paraboloid entity data class."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ._coerce import to_float, to_point
from .point import Point

if TYPE_CHECKING:
    from pytanga.algebra._mv import MV


@dataclass(frozen=True)
class Paraboloid:
    """A paraboloid in 3D space, opening along the z-axis.

    ``vertex`` is the vertex, ``semi_axes`` the focal semi-parameters
    ``(a, b)`` of ``z = x²/a² ± y²/b²``, and ``is_hyperbolic`` selects the sign
    (``False`` = elliptic ``+``, ``True`` = hyperbolic/saddle ``−``).
    """

    vertex: Point
    semi_axes: tuple[float, float]
    is_hyperbolic: bool = False

    def __init__(
        self,
        vertex: "Point | MV",
        semi_axes: "tuple[float, float] | list[float]",
        is_hyperbolic: bool = False,
    ) -> None:
        if not (isinstance(semi_axes, (tuple, list)) and len(semi_axes) == 2):
            raise TypeError(
                f"Expected a 2-sequence of floats, got {type(semi_axes).__name__}"
            )
        object.__setattr__(self, "vertex", to_point(vertex))
        object.__setattr__(self, "semi_axes", (to_float(semi_axes[0]), to_float(semi_axes[1])))
        object.__setattr__(self, "is_hyperbolic", bool(is_hyperbolic))

    def __repr__(self) -> str:
        kind = "hyperbolic" if self.is_hyperbolic else "elliptic"
        return f"Paraboloid(v={self.vertex}, axes={self.semi_axes}, {kind})"
