# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Type aliases for the Tanga 3D viewer."""

from __future__ import annotations

from typing import Any, TypeAlias, Union

from pytanga.geometry.entities import Arc, Cylinder, Entity as GeoEntity
from pytanga.geometry.operators import Operator as GeoOperator

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
    GeoEntity, GeoOperator, PointPath, Axis, Grid, Axes2D, Axes3D, Cylinder, Arc
]
