# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Algebra-independent geometric entity data classes.

These data classes represent geometric entities in Euclidean 3D space.
They are pure data containers with no dependency on pytanga.algebra,
pytanga.MV, or pytanga.basis. Algebra-specific conversion between MVs
and these entity classes is handled by the analysis and create modules.

Entity constructors accept a single multivector argument and convert it
via the matching typed analyzer, raising if the MV has the wrong
structure.  The analyzer is resolved through a registry populated by
:mod:`pytanga.geometry.analysis`, so this module has no import-time
dependency on ``analysis``.
"""

from __future__ import annotations

from ._coerce import (
    to_direction,
    to_float,
    to_point,
)
from ._util import (
    _is_mv,
    register_analyzer,
)
from .arc import Arc
from .box import Box
from .circle import Circle, ImagCircle
from .cone import Cone
from pytanga.quadric import Conic, EConicKind, EQuadricKind, Quadric2D, Quadric3D
from .cylinder import Cylinder
from pytanga.entity import Direction
from .disk import Disk, PartialDisk
from .ellipsoid import Ellipse, Ellipsoid
from .frustum import Frustum
from .hdirection import HDirection
from .hpoint import HPoint
from .hyperbola import Hyperbola
from .hyperboloid import Hyperboloid
from .line import Line
from .line_pair import LinePair, ParallelLinePair
from .plane import Plane
from .plane_conic import Curve, PlaneConic, PlaneConicPair
from .plane_pair import PlanePair, ParallelPlanePair
from .parabola import Parabola
from .paraboloid import Paraboloid
from pytanga.entity import Point
from .point_pair import ImagPointPair, PointPair
from .point_set import PointSet
from .polygon import RegularPolygon, regular_polygon
from .rectangle import Rectangle2D
from .space import Space
from .sphere import ImagSphere, Sphere

# Union type for all entities
Entity = (
    Point
    | Direction
    | HPoint
    | HDirection
    | PointPair
    | ImagPointPair
    | Line
    | Plane
    | Circle
    | ImagCircle
    | Sphere
    | ImagSphere
    | Space
    | Conic
    | Quadric3D
    | Hyperbola
    | Parabola
    | LinePair
    | ParallelLinePair
    | PlanePair
    | ParallelPlanePair
    | PlaneConic
    | PlaneConicPair
    | Curve
    | Cone
    | Hyperboloid
    | Paraboloid
    | PointSet
)

__all__ = [
    "Arc",
    "Box",
    "Circle",
    "Cone",
    "Conic",
    "Cylinder",
    "Direction",
    "Disk",
    "EConicKind",
    "EQuadricKind",
    "Ellipse",
    "Ellipsoid",
    "Entity",
    "Frustum",
    "HDirection",
    "HPoint",
    "Hyperbola",
    "Hyperboloid",
    "ImagCircle",
    "ImagPointPair",
    "ImagSphere",
    "Line",
    "LinePair",
    "ParallelLinePair",
    "Parabola",
    "Paraboloid",
    "PartialDisk",
    "Plane",
    "PlanePair",
    "ParallelPlanePair",
    "PlaneConic",
    "PlaneConicPair",
    "Curve",
    "Point",
    "PointPair",
    "PointSet",
    "Quadric2D",
    "Quadric3D",
    "Rectangle2D",
    "RegularPolygon",
    "Space",
    "Sphere",
    "_is_mv",
    "register_analyzer",
    "regular_polygon",
    "to_direction",
    "to_float",
    "to_point",
]
