# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Type aliases for the Tanga 3D viewer."""

from __future__ import annotations

from typing import Any, TypeAlias, Union

from pytanga.geometry.entities import (
    Arc,
    Box,
    Cylinder,
    Direction,
    Disk,
    Ellipse,
    Ellipsoid,
    Entity as GeoEntity,
    PartialDisk,
    Point,
    RegularPolygon,
)
from pytanga.geometry.operators import GeneralRotor, Operator as GeoOperator, Rotor

from . import _transforms as _T
from ._point_path import PointPath
from ._scene_objects import Axes2D, Axes3D, Axis, Grid

# Any type that can be passed to Visualizer.add()
# Note: "Any" covers the MV case — _resolve() uses duck-typing via
# pytanga.geometry.analyze() rather than isinstance checks.
VizInputType: TypeAlias = Union[
    GeoEntity, GeoOperator, PointPath, Axis, Grid, Axes2D, Axes3D, Cylinder, Arc, Any
]

# A scene-level entity — a GeoEntity, GeoOperator, or a viz-level drawable
# like PointPath / Axis / Grid / Cylinder / Arc that the serializer and
# frontend know how to render.
SceneEntity: TypeAlias = Union[
    GeoEntity,
    GeoOperator,
    PointPath,
    Axis,
    Grid,
    Axes2D,
    Axes3D,
    Cylinder,
    Arc,
    Box,
    Disk,
    Ellipse,
    Ellipsoid,
    PartialDisk,
    RegularPolygon,
]


# ── SDF / transform argument types ─────────────────────────

#: A 3-vector: a Point/Direction entity or a ``(x, y, z)`` 3-sequence.
Vec3: TypeAlias = Point | Direction | tuple[float, float, float]

#: A 3-tuple of floats (scale components, or an Euler-angle triple).
Triple: TypeAlias = tuple[float, float, float]

#: Axis-angle rotation (SDF primitives): a Rotor/GeneralRotor or an
#: ``(axis, angle)`` pair.
Rotation: TypeAlias = Rotor | GeneralRotor | tuple[tuple[float, float, float], float]

#: A scene/member-transform rotation: an Euler ``(rx, ry, rz)`` triple, or a
#: Rotor (converted to Euler internally).
TransformRotation: TypeAlias = Rotor | Triple

#: An operator dataclass that :func:`pytanga.viz._transforms.operator_to_matrix`
#: can convert to a 4×4 matrix (Rotor/GeneralRotor/Translator/Motor/Dilator).
TransformOperator: TypeAlias = _T.TransformOperator


def _as_vec3(value: Any) -> tuple[float, float, float]:
    """Best-effort convert *value* to a 3-vector of floats.

    Accepts objects with ``x``/``y``/``z`` attributes (``Point``,
    ``Direction``, …) or any 3-sequence.
    """
    if hasattr(value, "x") and hasattr(value, "y") and hasattr(value, "z"):
        return (float(value.x), float(value.y), float(value.z))
    seq = tuple(value)
    if len(seq) != 3:
        raise ValueError(f"Expected a 3-vector, got {value!r}")
    return (float(seq[0]), float(seq[1]), float(seq[2]))


def _as_euler(value: Any) -> tuple[float, float, float]:
    """Coerce a rotation to an Euler ``(rx, ry, rz)`` triple (order ``"XYZ"``).

    Accepts a Rotor (axis-angle, converted to Euler) or an Euler triple. A
    GeneralRotor with a displaced rotation centre cannot be represented as a
    plain transform rotation and raises.
    """
    angle = getattr(value, "angle", None)
    axis = getattr(value, "axis", None)
    if angle is not None and axis is not None:
        origin = getattr(value, "origin", None)
        if origin is not None:
            ox, oy, oz = _as_vec3(origin)
            if abs(ox) > 1e-12 or abs(oy) > 1e-12 or abs(oz) > 1e-12:
                raise TypeError(
                    "A rotation with a displaced origin (GeneralRotor) cannot be "
                    "used as a transform rotation; pass a Rotor or an Euler triple"
                )
        _, euler, _ = _T.to_trs(_T.rotation_matrix(axis, float(angle)))
        return euler
    return _as_vec3(value)

