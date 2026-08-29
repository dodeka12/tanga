# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Line pair entity data classes."""

from __future__ import annotations

from dataclasses import dataclass

from ._util import _convert_mv, _is_mv
from .line import Line


def _to_line(value) -> Line:
    if isinstance(value, Line):
        return value
    if _is_mv(value):
        return _convert_mv("line", value)
    raise TypeError(f"Expected Line or MV, got {type(value).__name__}")


@dataclass(frozen=True)
class LinePair:
    """Two intersecting lines (a degenerate conic)."""

    line1: Line
    line2: Line

    def __init__(self, line1, line2):
        object.__setattr__(self, "line1", _to_line(line1))
        object.__setattr__(self, "line2", _to_line(line2))

    def __repr__(self) -> str:
        return f"LinePair({self.line1}, {self.line2})"


@dataclass(frozen=True)
class ParallelLinePair(LinePair):
    """Two parallel lines (a degenerate conic)."""

    def __repr__(self) -> str:
        return f"ParallelLinePair({self.line1}, {self.line2})"
