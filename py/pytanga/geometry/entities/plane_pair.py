# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Plane pair entity data classes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from ._util import _convert_mv, _is_mv
from .plane import Plane

if TYPE_CHECKING:
    from pytanga.algebra._mv import MV


def _to_plane(value: "Plane | MV") -> Plane:
    if isinstance(value, Plane):
        return value
    if _is_mv(value):
        return cast("Plane", _convert_mv("plane", value))
    raise TypeError(f"Expected Plane or MV, got {type(value).__name__}")


@dataclass(frozen=True)
class PlanePair:
    """Two intersecting planes (a degenerate quadric)."""

    plane1: Plane
    plane2: Plane

    def __init__(self, plane1: "Plane | MV", plane2: "Plane | MV") -> None:
        object.__setattr__(self, "plane1", _to_plane(plane1))
        object.__setattr__(self, "plane2", _to_plane(plane2))

    def __repr__(self) -> str:
        return f"PlanePair({self.plane1}, {self.plane2})"


@dataclass(frozen=True)
class ParallelPlanePair(PlanePair):
    """Two parallel planes (a degenerate quadric)."""

    def __repr__(self) -> str:
        return f"ParallelPlanePair({self.plane1}, {self.plane2})"
