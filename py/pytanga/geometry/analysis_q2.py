# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Q2 (2D quadric / conic space) entity analysis."""

from __future__ import annotations

import numpy as np

from pytanga.quadric import from_coeffs

from .entities import Conic, Point

_DIM = 6


def _coeffs(mv, dim: int) -> tuple[float, ...]:
    """Read a grade-1 MV's coefficients in ``b1…bN`` order."""
    return tuple(float(mv[1 << i]) for i in range(dim))


def analyze_entity(mv):
    """Analyze an MV in the 2D quadric (conic) space.

    IPNS mode is handled by dualizing to OPNS first (same convention as the
    other ``analysis_*`` modules).  Grade 1 → ``Point`` (rank-1 embedding) and
    grade 5 → ``Conic``.
    """
    if not mv.algebra.opns:
        mv = mv.dual()
    return _analyze_entity_opns(mv)


def _analyze_entity_opns(mv):
    if mv.is_zero:
        raise ValueError("Zero MV does not represent a geometric entity")
    if mv.is_scalar:
        raise ValueError("Scalar MV does not represent a geometric entity")
    grades = mv.grades
    if len(grades) > 1:
        raise ValueError(f"Mixed-grade MV in Q2: grades={grades}")
    k = max(grades)
    if k == 1:
        return _point_from_embedding(mv)
    if k == 5:
        return _conic_from_blade(mv)
    raise NotImplementedError(f"grade {k} analysis in Q2 is implemented in Phase 4")


def _point_from_embedding(mv) -> Point:
    matrix = from_coeffs(_coeffs(mv, _DIM))
    if np.linalg.matrix_rank(matrix) != 1:
        raise ValueError("grade-1 OPNS blade is not a rank-1 point embedding")
    w = matrix[2, 2]
    if abs(w) < 1e-12:
        raise ValueError("point at infinity (zero homogeneous coordinate)")
    return Point(float(matrix[0, 2] / w), float(matrix[1, 2] / w), 0.0)


def _conic_from_blade(mv) -> Conic:
    return Conic(_coeffs(mv.undual(), _DIM))
