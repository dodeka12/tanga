# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass


from ._util import _convert_mv, _is_mv, _scalar
from .direction import Direction
from .point import Point


def to_point(value) -> Point:
    """Ensure *value* is a Point, converting from MV if needed."""

    if _is_mv(value):
        return _convert_mv("point", value)
    if isinstance(value, Point):
        return value
    raise TypeError(f"Expected Point or MV, got {type(value).__name__}")


def to_direction(value) -> "Direction":
    """Ensure *value* is a Direction, converting from MV if needed."""

    if _is_mv(value):
        return _convert_mv("direction", value)
    if isinstance(value, Direction):
        return value
    raise TypeError(f"Expected Direction or MV, got {type(value).__name__}")


def to_float(value) -> float:
    """Ensure *value* is a float, converting from scalar MV if needed."""
    if _is_mv(value):
        return float(_scalar(value))
    if isinstance(value, (int, float)):
        return float(value)
    raise TypeError(f"Expected float or scalar MV, got {type(value).__name__}")
