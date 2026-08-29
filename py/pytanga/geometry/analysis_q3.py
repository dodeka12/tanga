# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Q3 (3D quadric space) entity analysis."""

from __future__ import annotations

from ._pointset import point_from_embedding, pointset_from_blade
from .entities import Quadric3D

_DIM = 10


def _coeffs(mv, dim: int) -> tuple[float, ...]:
    """Read a grade-1 MV's coefficients in ``b1…bN`` order."""
    return tuple(float(mv[1 << i]) for i in range(dim))


def analyze_entity(mv):
    """Analyze an MV in the 3D quadric space.

    OPNS: grade 1 → ``Point`` (rank-1 embedding), grades 2..8 → ``PointSet``
    (point joins), grade 9 → ``Quadric3D``.  IPNS: only grade 1 (quadric) and
    grade 9 (point); other IPNS grades are deferred quadric intersections.
    """
    if mv.algebra.opns:
        return _analyze_entity_opns(mv)

    if mv.is_zero:
        raise ValueError("Zero MV does not represent a geometric entity")
    if mv.is_scalar:
        raise ValueError("Scalar MV does not represent a geometric entity")
    grades = mv.grades
    if len(grades) > 1:
        raise ValueError(f"Mixed-grade MV in Q3: grades={grades}")
    k = grades[0]
    if k == 1:
        return _quadric_from_blade(mv.dual())
    if k == 9:
        return point_from_embedding(mv.dual(), _DIM)
    raise NotImplementedError(
        f"q3 IPNS grade {k} (quadric intersection) analysis is deferred"
    )


def _analyze_entity_opns(mv):
    if mv.is_zero:
        raise ValueError("Zero MV does not represent a geometric entity")
    if mv.is_scalar:
        raise ValueError("Scalar MV does not represent a geometric entity")
    grades = mv.grades
    if len(grades) > 1:
        raise ValueError(f"Mixed-grade MV in Q3: grades={grades}")
    k = max(grades)
    if k == 1:
        return point_from_embedding(mv, _DIM)
    if 2 <= k <= 8:
        return pointset_from_blade(mv)
    if k == 9:
        return _quadric_from_blade(mv)
    raise NotImplementedError(f"grade {k} analysis in Q3 is not supported")


def _quadric_from_blade(mv) -> Quadric3D:
    return Quadric3D(_coeffs(mv.undual(), _DIM))
