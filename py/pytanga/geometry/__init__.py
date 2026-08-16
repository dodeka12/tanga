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
from .random import (
    Distribution,
    Normal,
    RndDirection,
    RndEntity,
    RndPoint,
    Uniform,
)
from .entities import (
    Circle,
    Direction,
    Entity,
    HDirection,
    HPoint,
    ImagCircle,
    ImagPointPair,
    ImagSphere,
    Line,
    Plane,
    Point,
    PointPair,
    Space,
    Sphere,
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
    "Circle",
    "Direction",
    "Entity",
    "HDirection",
    "HPoint",
    "ImagCircle",
    "ImagPointPair",
    "ImagSphere",
    "Line",
    "Plane",
    "Point",
    "PointPair",
    "Space",
    "Sphere",
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
    # Random generation
    "Distribution",
    "Normal",
    "RndDirection",
    "RndEntity",
    "RndPoint",
    "Uniform",
]
