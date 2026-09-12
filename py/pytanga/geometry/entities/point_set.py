# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""PointSet entity data class."""

from __future__ import annotations

from dataclasses import dataclass

from ._coerce import to_point
from .point import Point


@dataclass(frozen=True)
class PointSet:
    """A finite collection of points (single / pair / triplet / … / n-tuple).

    ``kind`` is an optional descriptive tag (``single``, ``pair``,
    ``triplet``, ``quadruplet``, ``n_tuple``) used by the visualizer.
    """

    points: tuple[Point, ...]
    kind: str | None = None

    def __init__(self, points, kind=None):
        object.__setattr__(self, "points", tuple(to_point(p) for p in points))
        object.__setattr__(self, "kind", kind)

    def __len__(self) -> int:
        return len(self.points)

    def __iter__(self):
        return iter(self.points)

    def __getitem__(self, index):
        return self.points[index]

    def __repr__(self) -> str:
        return f"PointSet({self.points})"
