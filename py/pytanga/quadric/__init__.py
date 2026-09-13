# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pytanga.quadric — projective quadric spaces (conics in 2D, quadrics in 3D).

The core (Euclidean-rescaled bases, point embedding, symmetric-matrix ↔
coefficient maps, and conic/quadric construction from points) is pure math
with no ``geometry`` or ``viz`` dependencies.  :func:`refine` (classifying a
conic/quadric and extracting its specific entity) is quadric math too, but it
builds :mod:`pytanga.geometry.entities` objects — imported lazily.
"""

from ._analysis import analyze_entity, analyze_operator, analyze_rotor
from ._basis import BasisQ2, BasisQ3
from ._build import (
    conic_from_points,
    conic_from_points_svd,
    line_from_points,
    quadric_from_points,
    quadric_from_points_svd,
)
from ._create import (
    create_circle,
    create_cone,
    create_conic,
    create_cylinder,
    create_ellipse,
    create_ellipsoid,
    create_entity,
    create_hyperbola,
    create_line,
    create_line_pair,
    create_parabola,
    create_parallel_line_pair,
    create_plane,
    create_point,
    create_quadric,
    create_rotor,
    create_sphere,
)
from ._embedding import embed_point
from ._intersection import intersect_quadrics, intersect_three_quadrics
from ._mapping import from_coeffs, to_coeffs
from ._pointset import two_conic_intersection
from .conic import Conic, EConicKind, EQuadricKind, Quadric2D, Quadric3D
from .refine import refine_conic, refine_quadric

__all__ = [
    "analyze_entity",
    "analyze_operator",
    "analyze_rotor",
    "BasisQ2",
    "BasisQ3",
    "Conic",
    "EConicKind",
    "EQuadricKind",
    "Quadric2D",
    "Quadric3D",
    "conic_from_points",
    "conic_from_points_svd",
    "create_circle",
    "create_cone",
    "create_conic",
    "create_cylinder",
    "create_ellipse",
    "create_ellipsoid",
    "create_entity",
    "create_hyperbola",
    "create_line",
    "create_line_pair",
    "create_parabola",
    "create_parallel_line_pair",
    "create_plane",
    "create_point",
    "create_quadric",
    "create_rotor",
    "create_sphere",
    "embed_point",
    "from_coeffs",
    "intersect_quadrics",
    "intersect_three_quadrics",
    "line_from_points",
    "quadric_from_points",
    "quadric_from_points_svd",
    "refine_conic",
    "refine_quadric",
    "to_coeffs",
    "two_conic_intersection",
]
