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
from .conic import Conic, EConicKind, EQuadricKind, Quadric2D, Quadric3D
from .cylinder import Cylinder
from .direction import Direction
from .disk import Disk, PartialDisk
from .ellipsoid import Ellipse, Ellipsoid
from .hdirection import HDirection
from .hpoint import HPoint
from .hyperbola import Hyperbola
from .line import Line
from .line_pair import LinePair, ParallelLinePair
from .plane import Plane
from .parabola import Parabola
from .point import Point
from .point_pair import ImagPointPair, PointPair
from .point_set import PointSet
from .polygon import RegularPolygon, regular_polygon
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
)

__all__ = [
    "Arc",
    "Box",
    "Circle",
    "Conic",
    "Cylinder",
    "Direction",
    "Disk",
    "EConicKind",
    "EQuadricKind",
    "Ellipse",
    "Ellipsoid",
    "Entity",
    "HDirection",
    "HPoint",
    "Hyperbola",
    "ImagCircle",
    "ImagPointPair",
    "ImagSphere",
    "Line",
    "LinePair",
    "ParallelLinePair",
    "Parabola",
    "PartialDisk",
    "Plane",
    "Point",
    "PointPair",
    "PointSet",
    "Quadric2D",
    "Quadric3D",
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
