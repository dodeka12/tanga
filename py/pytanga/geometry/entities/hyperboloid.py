# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Hyperboloid entity data class."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ._coerce import to_point, to_triple
from .point import Point

if TYPE_CHECKING:
    from pytanga.algebra._mv import MV


@dataclass(frozen=True)
class Hyperboloid:
    """A hyperboloid in 3D space, axis-aligned along the z-axis.

    ``center`` is the center, ``semi_axes`` the per-axis semi-axes
    ``(a, b, c)`` (``a, b`` in the transverse plane, ``c`` along the z-axis),
    and ``sheets`` is ``1`` (one-sheeted: ``x²/a² + y²/b² − z²/c² = 1``) or ``2``
    (two-sheeted: ``x²/a² + y²/b² − z²/c² = −1``).
    """

    center: Point
    semi_axes: tuple[float, float, float]
    sheets: int = 1

    def __init__(
        self,
        center: "Point | MV",
        semi_axes: "tuple[float, float, float] | list[float]",
        sheets: int = 1,
    ) -> None:
        if sheets not in (1, 2):
            raise ValueError(f"sheets must be 1 or 2, got {sheets}")
        object.__setattr__(self, "center", to_point(center))
        object.__setattr__(self, "semi_axes", to_triple(semi_axes))
        object.__setattr__(self, "sheets", int(sheets))

    def __repr__(self) -> str:
        return (
            f"Hyperboloid(c={self.center}, axes={self.semi_axes}, "
            f"sheets={self.sheets})"
        )
