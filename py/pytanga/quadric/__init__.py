# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pytanga.quadric — projective quadric spaces (conics in 2D, quadrics in 3D).

Pure math only: the Euclidean-rescaled bases, point embedding, symmetric-matrix
↔ coefficient maps, and conic/quadric construction from points.  No ``geometry``
or ``viz`` dependencies.
"""

from ._basis import BasisQ2, BasisQ3
from ._build import (
    conic_from_points,
    conic_from_points_svd,
    line_from_points,
    quadric_from_points,
    quadric_from_points_svd,
)
from ._embedding import embed_point
from ._mapping import from_coeffs, to_coeffs

__all__ = [
    "BasisQ2",
    "BasisQ3",
    "conic_from_points",
    "conic_from_points_svd",
    "embed_point",
    "from_coeffs",
    "line_from_points",
    "quadric_from_points",
    "quadric_from_points_svd",
    "to_coeffs",
]
