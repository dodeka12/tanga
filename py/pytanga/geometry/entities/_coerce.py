# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass


from typing import cast

from pytanga.entity import Direction, Point
from pytanga.entity._util import _convert_mv, _is_mv, _scalar


def to_point(value: object) -> Point:
    """Ensure *value* is a Point, converting from MV if needed."""

    if _is_mv(value):
        return cast("Point", _convert_mv("point", value))
    if isinstance(value, Point):
        return value
    raise TypeError(f"Expected Point or MV, got {type(value).__name__}")


def to_direction(value: object) -> "Direction":
    """Ensure *value* is a Direction, converting from MV if needed."""

    if _is_mv(value):
        return cast("Direction", _convert_mv("direction", value))
    if isinstance(value, Direction):
        return value
    raise TypeError(f"Expected Direction or MV, got {type(value).__name__}")


def to_float(value: object) -> float:
    """Ensure *value* is a float, converting from scalar MV if needed."""
    if _is_mv(value):
        return float(_scalar(value))
    if isinstance(value, (int, float)):
        return float(value)
    raise TypeError(f"Expected float or scalar MV, got {type(value).__name__}")


def to_triple(value: object) -> tuple[float, float, float]:
    """Ensure *value* is a 3-tuple of floats (coercing scalar MVs per component)."""
    if isinstance(value, (tuple, list)) and len(value) == 3:
        return (to_float(value[0]), to_float(value[1]), to_float(value[2]))
    raise TypeError(f"Expected a 3-sequence of floats, got {type(value).__name__}")
