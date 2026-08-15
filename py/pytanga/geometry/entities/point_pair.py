# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Point pair entity data classes."""

from __future__ import annotations

from dataclasses import dataclass

from ._coerce import to_direction, to_float, to_point
from ._util import _convert_mv
from .direction import Direction
from .point import Point


@dataclass(frozen=True)
class PointPair:
    """A pair of points (CGA grade-2 entity).

    For imaginary point pairs (N3-only, dual of a real circle), set
    ``is_imaginary=True``.  They have no real Euclidean points
    satisfying ``X·PP = 0``.

    The optional reconstruction fields ``_center``, ``_direction``,
    and ``_separation`` store the data needed to reconstruct an
    imaginary point pair via ``create_imag_point_pair`` (needed
    because the dual-of-circle representation is not directly
    expressible from ``point_a``/``point_b`` alone).
    """

    point_a: Point
    point_b: Point
    is_imaginary: bool = False
    _center: Point | None = None
    _direction: Direction | None = None
    _separation: float | None = None

    def __init__(
        self,
        point_a,
        point_b=None,
        is_imaginary=False,
        _center=None,
        _direction=None,
        _separation=None,
    ):
        try:
            point_a = to_point(point_a)
        except TypeError:
            pp = _convert_mv("point_pair", point_a)
            object.__setattr__(self, "point_a", pp.point_a)
            object.__setattr__(self, "point_b", pp.point_b)
            object.__setattr__(self, "is_imaginary", pp.is_imaginary)
            object.__setattr__(self, "_center", pp._center)
            object.__setattr__(self, "_direction", pp._direction)
            object.__setattr__(self, "_separation", pp._separation)
            return

        object.__setattr__(self, "point_a", point_a)
        object.__setattr__(self, "point_b", to_point(point_b))
        object.__setattr__(self, "is_imaginary", is_imaginary)
        object.__setattr__(
            self, "_center", None if _center is None else to_point(_center)
        )
        object.__setattr__(
            self,
            "_direction",
            None if _direction is None else to_direction(_direction),
        )
        object.__setattr__(
            self,
            "_separation",
            None if _separation is None else to_float(_separation),
        )

    def __repr__(self) -> str:
        prefix = "Imag" if self.is_imaginary else ""
        return f"{prefix}PntPair({self.point_a}, {self.point_b})"


@dataclass(frozen=True)
class ImagPointPair(PointPair):
    """An imaginary point pair (N3/PGA3 only).

    Inherits all fields from :class:`PointPair` with ``is_imaginary=True``.
    Can be used as a class-based key in :attr:`Visualizer.default_styles`
    (e.g. ``viz.default_styles[ImagPointPair]``).
    """

    is_imaginary: bool = True