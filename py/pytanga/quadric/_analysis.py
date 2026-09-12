# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Q2 (2D conic) / Q3 (3D quadric) space entity analysis — MV → entity.

Pure quadric math: grade dispatch to ``Conic`` / ``Quadric3D`` / ``Point`` /
``PointSet``.  Point recovery helpers live in :mod:`pytanga.quadric._pointset`.
"""

from __future__ import annotations

import math

import numpy as np

from ._intersection import intersect_quadrics
from ._mapping import from_coeffs
from ._pointset import point_from_embedding, pointset_from_blade
from .conic import Conic, Quadric3D


def _coeffs(mv, dim: int) -> tuple[float, ...]:
    """Read a grade-1 MV's coefficients in ``b1…bN`` order."""
    return tuple(float(mv[1 << i]) for i in range(dim))


def _quadric_intersection_from_blade(mv):
    """Analyze an IPNS grade-2 blade as the intersection of two quadrics.

    The bivector is the pencil ``span{Q1, Q2}``; factor it into two (arbitrary)
    generators and let :func:`intersect_quadrics` re-derive the degenerate
    members (so the factorization basis does not matter).
    """
    factors = mv.blade_factorize()
    if len(factors) != 2:
        raise ValueError(f"expected a 2-blade, got {len(factors)} factors")
    q1 = from_coeffs(_coeffs(factors[0], 10))
    q2 = from_coeffs(_coeffs(factors[1], 10))
    return intersect_quadrics(q1, q2)


def analyze_entity(mv):
    """Analyze an MV in the 2D (Q2) or 3D (Q3) quadric space.

    Q2: IPNS is dualized to OPNS first; grade 1 → ``Point``, grades 2/3/4 →
    ``PointSet``, grade 5 → ``Conic``.

    Q3: OPNS grade 1 → ``Point``, grades 2..7 → ``PointSet``, grade 8 → the
    degenerate quadric intersection (the dual grade-2 pencil → ``PlaneConicPair``
    / ``Curve``), grade 9 → ``Quadric3D``.  IPNS grade 1 → ``Quadric3D``, grade
    2 → the quadric intersection, grade 9 → ``Point``; other grades are deferred.

    Coefficients below the algebra precision are pruned first, so numerical
    residue from versor products (e.g. a rotated quadric carrying ~1e-12 in
    lower grades) does not misclassify as a mixed-grade MV.
    """
    mv = mv.prune()
    if mv.algebra.dim == 6:
        return _analyze_q2(mv)
    return _analyze_q3(mv)


def _analyze_q2(mv):
    if not mv.algebra.opns:
        mv = mv.dual()
    return _analyze_q2_opns(mv)


def _analyze_q2_opns(mv):
    if mv.is_zero:
        raise ValueError("Zero MV does not represent a geometric entity")
    if mv.is_scalar:
        raise ValueError("Scalar MV does not represent a geometric entity")
    grades = mv.grades
    if len(grades) > 1:
        raise ValueError(f"Mixed-grade MV in Q2: grades={grades}")
    k = max(grades)
    if k == 1:
        return point_from_embedding(mv, mv.algebra.dim)
    if k in (2, 3, 4):
        return pointset_from_blade(mv)
    if k == 5:
        return _conic_from_blade(mv)
    raise NotImplementedError(f"grade {k} analysis in Q2 is not supported")


def _analyze_q3(mv):
    if mv.algebra.opns:
        return _analyze_q3_opns(mv)
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
    if k == 2:
        return _quadric_intersection_from_blade(mv)
    if k == 9:
        return point_from_embedding(mv.dual(), mv.algebra.dim)
    raise NotImplementedError(
        f"q3 IPNS grade {k} (quadric intersection) analysis is deferred"
    )


def _analyze_q3_opns(mv):
    if mv.is_zero:
        raise ValueError("Zero MV does not represent a geometric entity")
    if mv.is_scalar:
        raise ValueError("Scalar MV does not represent a geometric entity")
    grades = mv.grades
    if len(grades) > 1:
        raise ValueError(f"Mixed-grade MV in Q3: grades={grades}")
    k = max(grades)
    if k == 1:
        return point_from_embedding(mv, mv.algebra.dim)
    if k == 8:
        # A grade-8 join (9 points spanning 8 dims — a degenerate set) is dual
        # to the grade-2 IPNS pencil of quadrics through those points.
        return _quadric_intersection_from_blade(mv.dual())
    if 2 <= k <= 7:
        return pointset_from_blade(mv)
    if k == 9:
        return _quadric_from_blade(mv)
    raise NotImplementedError(f"grade {k} analysis in Q3 is not supported")


def _conic_from_blade(mv) -> Conic:
    return Conic(_coeffs(mv.undual(), mv.algebra.dim))


def _quadric_from_blade(mv) -> Quadric3D:
    return Quadric3D(_coeffs(mv.undual(), mv.algebra.dim))


def analyze_rotor(mv):
    """Extract the rotation ``Rotor(angle, axis)`` encoded by a rotor MV.

    The rotation is recovered by sandwiching the **linear** basis blades
    (``b₁,b₂`` in Q2; ``b₁,b₂,b₃`` in Q3) and reading the coefficients into a
    rotation matrix — the other rotor factors commute with the linear blades,
    so only the linear factor contributes (see
    ``dev/notes/quadric-rotor-derivation.md``).

    A scalar MV is the identity versor, i.e. a rotor of angle zero.
    """
    if mv.is_scalar:
        from pytanga.entity import Direction
        from pytanga.geometry.operators import Rotor

        return Rotor(0.0, Direction(0.0, 0.0, 1.0))
    dim = mv.algebra.dim
    if dim == 6:
        m = np.zeros((2, 2))
        for i in range(2):
            bi = mv.algebra.multivector({1 << i: 1.0})
            rot = mv * bi * mv.rev()
            for j in range(2):
                m[i, j] = float(rot[1 << j])
        angle = math.atan2(m[0, 1], m[0, 0])
        from pytanga.entity import Direction
        from pytanga.geometry.operators import Rotor

        return Rotor(angle, Direction(0.0, 0.0, 1.0))
    if dim == 10:
        m = np.zeros((3, 3))
        for i in range(3):
            bi = mv.algebra.multivector({1 << i: 1.0})
            rot = mv * bi * mv.rev()
            for j in range(3):
                m[i, j] = float(rot[1 << j])
        angle = math.acos(max(-1.0, min(1.0, (float(np.trace(m)) - 1.0) / 2.0)))
        skew = (m.T - m) / 2.0
        ax = np.array([skew[2, 1], skew[0, 2], skew[1, 0]])
        n = float(np.linalg.norm(ax))
        if n < 1e-12:
            ax = np.array([0.0, 0.0, 1.0])
        else:
            ax = ax / n
        from pytanga.entity import Direction
        from pytanga.geometry.operators import Rotor

        return Rotor(angle, Direction(float(ax[0]), float(ax[1]), float(ax[2])))
    raise ValueError(f"unsupported quadric basis dimension: {dim}")


def analyze_operator(mv):
    """Analyze a quadric-space MV as a versor/operator.

    The quadric spaces support only the rotation rotor; returns a
    :class:`~pytanga.geometry.operators.Rotor`.  A scalar MV is the identity
    versor (a rotor of angle zero).  Raises ``ValueError`` for a zero MV or one
    with odd grades (not a versor).
    """
    if mv.is_zero:
        raise ValueError("Zero MV does not represent a quadric operator")
    if any(g % 2 != 0 for g in mv.grades):
        raise ValueError(
            f"MV grades {sorted(mv.grades)} are not even — not a quadric versor"
        )
    return analyze_rotor(mv)
