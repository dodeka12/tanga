# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Flat point (homogeneous point) entity data class."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from ._coerce import to_float, to_point
from ._util import _convert_mv
from .point import Point

if TYPE_CHECKING:
    from pytanga.algebra._mv import MV


@dataclass(frozen=True)
class HPoint:
    """A flat point — finite point with homogeneous weight (N3-only)."""

    point: Point
    weight: float = 1.0

    def __init__(self, point: "Point | MV", weight: "float | MV" = 1.0) -> None:
        try:
            point = to_point(point)
        except TypeError:
            h = _convert_mv("hpoint", cast("MV", point))
            object.__setattr__(self, "point", h.point)
            object.__setattr__(self, "weight", h.weight)
            return

        object.__setattr__(self, "point", point)
        object.__setattr__(self, "weight", to_float(weight))

    def __repr__(self) -> str:
        return f"HPoint({self.point}, w={self.weight:.2f})"
