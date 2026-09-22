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
    Frustum,
    PartialDisk,
    Point,
    Rectangle2D,
    RegularPolygon,
)
from pytanga.geometry.operators import GeneralRotor, Operator as GeoOperator, Rotor
from pytanga.geometry.transform import (  # noqa: F401  (re-export)
    TransformInput,
    TransformOperator,
    TransformRotation,
    Triple,
    _as_euler,
    _as_vec3,
)

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
    Frustum,
    PartialDisk,
    Rectangle2D,
    RegularPolygon,
]


# ── SDF / transform argument types ─────────────────────────

#: A 3-vector: a Point/Direction entity or a ``(x, y, z)`` 3-sequence.
Vec3: TypeAlias = Point | Direction | tuple[float, float, float]

#: Axis-angle rotation (SDF primitives): a Rotor/GeneralRotor or an
#: ``(axis, angle)`` pair.
Rotation: TypeAlias = Rotor | GeneralRotor | tuple[tuple[float, float, float], float]
