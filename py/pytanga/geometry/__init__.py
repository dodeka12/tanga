# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Geometric entity and operator data classes plus analysis functions.

Provides algebra-independent data classes for geometric entities
(e.g. Point, Line, Plane) and operators (e.g. Rotor, Translator),
plus analysis functions to extract geometric meaning from
multivectors/blades.
"""

from ._geometry import (
    Geometry,
)
from .analysis import (
    analyze,
    analyze_entity,
    analyze_operator,
)
from .create import (
    create,
    create_entity,
    create_operator,
)
from .mask import (
    create_var,
    mask_for,
)
from .refine import (
    refine,
    refine_entity,
)
from .random import (
    Distribution,
    Normal,
    RndDirection,
    RndEntity,
    RndPoint,
    Uniform,
)
from .entities import (
    Arc,
    Box,
    Circle,
    Cone,
    Conic,
    Cylinder,
    Direction,
    Disk,
    EConicKind,
    EQuadricKind,
    Ellipse,
    Ellipsoid,
    Entity,
    HDirection,
    HPoint,
    Hyperbola,
    ImagCircle,
    ImagPointPair,
    ImagSphere,
    Line,
    LinePair,
    ParallelLinePair,
    Parabola,
    PartialDisk,
    Plane,
    Point,
    PointPair,
    PointSet,
    Quadric2D,
    Quadric3D,
    RegularPolygon,
    Space,
    Sphere,
    regular_polygon,
)
from .operators import (
    Dilator,
    GeneralRotor,
    Inversion,
    Motor,
    Operator,
    Reflection,
    ReflectionLine,
    ReflectionPlane,
    ReflectionPoint,
    Rotor,
    Translator,
    TripleReflection,
)

__all__ = [
    # Entities
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
    "regular_polygon",
    # Operators
    "Dilator",
    "GeneralRotor",
    "Inversion",
    "Motor",
    "Operator",
    "Reflection",
    "ReflectionLine",
    "ReflectionPlane",
    "ReflectionPoint",
    "Rotor",
    "Translator",
    "TripleReflection",
    # Geometry facade
    "Geometry",
    # Analysis
    "analyze",
    "analyze_entity",
    "analyze_operator",
    # Creation
    "create",
    "create_entity",
    "create_operator",
    # Variable / blade-mask helpers
    "create_var",
    "mask_for",
    # Refinement
    "refine",
    "refine_entity",
    # Random generation
    "Distribution",
    "Normal",
    "RndDirection",
    "RndEntity",
    "RndPoint",
    "Uniform",
]
