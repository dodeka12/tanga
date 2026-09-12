# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Plane-conic, plane-conic-pair, and curve entity data classes."""

from __future__ import annotations

from dataclasses import dataclass

from pytanga.quadric import Conic

from ._coerce import to_point
from ._util import _convert_mv, _is_mv
from .plane import Plane
from .point import Point


def _to_plane(value) -> Plane:
    if isinstance(value, Plane):
        return value
    if _is_mv(value):
        return _convert_mv("plane", value)
    raise TypeError(f"Expected Plane or MV, got {type(value).__name__}")


def _to_conic(value) -> Conic:
    if isinstance(value, Conic):
        return value
    return Conic(value)


def _to_plane_conic(value) -> "PlaneConic":
    if isinstance(value, PlaneConic):
        return value
    plane, conic = value
    return PlaneConic(plane, conic)


@dataclass(frozen=True)
class PlaneConic:
    """A conic lying in a 3D plane.

    ``conic`` is the 2D :class:`~pytanga.quadric.Conic` expressed in the plane's
    canonical local 2D frame ``(u, v)`` (see
    ``pytanga.quadric._intersection._plane_frame``).
    """

    plane: Plane
    conic: Conic

    def __init__(self, plane, conic):
        object.__setattr__(self, "plane", _to_plane(plane))
        object.__setattr__(self, "conic", _to_conic(conic))

    def __repr__(self) -> str:
        return f"PlaneConic({self.plane}, {self.conic})"


@dataclass(frozen=True)
class PlaneConicPair:
    """Two plane-conics (a quadric intersection via a plane-pair member)."""

    conic1: PlaneConic
    conic2: PlaneConic

    def __init__(self, conic1, conic2):
        object.__setattr__(self, "conic1", _to_plane_conic(conic1))
        object.__setattr__(self, "conic2", _to_plane_conic(conic2))

    def __repr__(self) -> str:
        return f"PlaneConicPair({self.conic1}, {self.conic2})"


@dataclass(frozen=True)
class Curve:
    """A sampled space curve (one polyline per connected component)."""

    paths: tuple[tuple[Point, ...], ...]

    def __init__(self, paths):
        object.__setattr__(
            self,
            "paths",
            tuple(tuple(to_point(p) for p in path) for path in paths),
        )

    def __len__(self) -> int:
        return len(self.paths)

    def __iter__(self):
        return iter(self.paths)

    def __repr__(self) -> str:
        return f"Curve({self.paths})"
