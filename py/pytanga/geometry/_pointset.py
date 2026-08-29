# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Point-set analysis (OPNS point joins) and 2D two-conic intersection."""

from __future__ import annotations

import numpy as np

from pytanga.quadric import from_coeffs

from .entities import Point, PointSet

_TOL = 1e-10


def _coeffs(mv, dim: int) -> tuple[float, ...]:
    """Read a grade-1 MV's coefficients in ``b1…bN`` order."""
    return tuple(float(mv[1 << i]) for i in range(dim))


def point_from_embedding(mv, dim: int) -> Point:
    """Recover a finite point from a rank-1 grade-1 embedding MV."""
    matrix = from_coeffs(_coeffs(mv, dim))
    if np.linalg.matrix_rank(matrix) != 1:
        raise ValueError("not a rank-1 point embedding")
    w = matrix[-1, -1]
    if abs(w) < 1e-12:
        raise ValueError("point at infinity (zero homogeneous coordinate)")
    if dim == 6:
        return Point(float(matrix[0, 2] / w), float(matrix[1, 2] / w), 0.0)
    return Point(
        float(matrix[0, 3] / w),
        float(matrix[1, 3] / w),
        float(matrix[2, 3] / w),
    )


def _kind_for(n: int) -> str:
    return {1: "single", 2: "pair", 3: "triplet", 4: "quadruplet"}.get(n, "n_tuple")


def pointset_from_blade(mv) -> PointSet:
    """Recover the points of a simple blade (OPNS join) as a ``PointSet``."""
    factors = mv.blade_factorize()
    dim = mv.algebra.dim
    k = len(factors)
    if k == 2:
        points = _points_from_two_point_join(factors, dim)
    elif dim == 6 and k in (3, 4):
        points = _points_from_join_via_conics(factors)
    else:
        raise NotImplementedError(
            f"point recovery for a {k}-point join in dim {dim} is not supported"
        )
    return PointSet(points, kind=_kind_for(len(points)))


def _point_from_rank1_matrix(m: np.ndarray, dim: int) -> Point | None:
    """Dehomogenize a rank-1 symmetric matrix into its point (or None if ideal)."""
    u, _, _ = np.linalg.svd(m)
    v = u[:, 0]  # top singular vector = homogeneous point (up to scale)
    w = v[-1]
    if abs(w) < 1e-12:
        return None
    if dim == 6:
        return Point(float(v[0] / w), float(v[1] / w), 0.0)
    return Point(float(v[0] / w), float(v[1] / w), float(v[2] / w))


def _solve_binary_quadratic(a, b, c, tol=1e-10) -> list[tuple[float, float]]:
    """Real projective roots ``(alpha, beta)`` of ``a α² + b αβ + c β² = 0``."""
    sols: list[tuple[float, float]] = []
    if abs(a) > tol:
        for t in np.roots([a, b, c]):
            if abs(t.imag) < tol:
                sols.append((float(t.real), 1.0))
    else:
        sols.append((1.0, 0.0))  # β = 0 root
        if abs(b) > tol:
            sols.append((-c / b, 1.0))
    return sols


def _points_from_two_point_join(factors, dim: int) -> list[Point]:
    """Recover the two points of a 2D pencil (join of two points)."""
    m1 = from_coeffs(_coeffs(factors[0], dim))
    m2 = from_coeffs(_coeffs(factors[1], dim))
    # Rank-1 elements of the pencil α m1 + β m2 are where the top-left 2×2
    # minor vanishes (a binary quadratic in (α, β)).
    a = float(m1[0, 0] * m1[1, 1] - m1[0, 1] * m1[1, 0])
    b = float(
        m1[0, 0] * m2[1, 1]
        + m2[0, 0] * m1[1, 1]
        - m1[0, 1] * m2[1, 0]
        - m2[0, 1] * m1[1, 0]
    )
    c = float(m2[0, 0] * m2[1, 1] - m2[0, 1] * m2[1, 0])

    points: list[Point] = []
    for alpha, beta in _solve_binary_quadratic(a, b, c):
        m = alpha * m1 + beta * m2
        if np.linalg.matrix_rank(m) > 1:
            continue
        p = _point_from_rank1_matrix(m, dim)
        if p is not None:
            points.append(p)
    return points


def _symmetric_basis_3() -> list[np.ndarray]:
    basis: list[np.ndarray] = []
    for i in range(3):
        for j in range(i, 3):
            e = np.zeros((3, 3))
            e[i, j] = e[j, i] = 1.0
            basis.append(e)
    return basis


def _points_from_join_via_conics(factors) -> list[Point]:
    """Recover 3 or 4 join points (2D) via the orthogonal conic complement."""
    ms = [from_coeffs(_coeffs(f, 6)) for f in factors]
    k = len(ms)
    basis = _symmetric_basis_3()
    gram = np.array([[float(np.trace(b @ m)) for m in ms] for b in basis])  # 6×k
    _, _, vh = np.linalg.svd(gram.T)  # gram.T is k×6
    comp = vh[k:]  # (6-k)×6 rows = coefficient vectors in the basis
    conics = [sum(c[i] * basis[i] for i in range(6)) for c in comp]

    # Use generic (non-singular) combinations of the complement conics so the
    # pencil intersection is well-conditioned.
    rng = np.random.default_rng(0)
    g1 = sum(rng.normal() * c for c in conics)
    g2 = sum(rng.normal() * c for c in conics)
    points = list(two_conic_intersection(g1, g2))
    for conic in conics:
        points = [p for p in points if abs(_quad_value(conic, p)) < 1e-8]
    return points


def _quad_value(n: np.ndarray, p: Point) -> float:
    ph = np.array([p.x, p.y, 1.0])
    return float(ph @ n @ ph)


def _line_pair_from_matrix(c: np.ndarray) -> list[np.ndarray]:
    """Factor a degenerate conic matrix into 1 or 2 homogeneous lines.

    ``c`` must be rank 1 (double line) or rank 2 (intersecting line pair).
    Each returned line is a 3-vector ``(a, b, c)`` with ``a x + b y + c = 0``.
    """
    r = int(np.linalg.matrix_rank(c))
    evals, evecs = np.linalg.eigh(c)
    if r == 2:
        v_pos = evecs[:, -1] * float(np.sqrt(max(0.0, evals[-1])))
        v_neg = evecs[:, 0] * float(np.sqrt(max(0.0, -evals[0])))
        return [v_pos + v_neg, v_pos - v_neg]
    if r == 1:
        idx = int(np.argmax(np.abs(evals)))
        return [evecs[:, idx]]
    return []


def _intersect_line_conic(line: np.ndarray, a: np.ndarray) -> list[Point]:
    """Intersect the line ``(a, b, c)`` with the conic matrix ``A``."""
    la, lb, lc = (float(x) for x in line)
    norm2 = la * la + lb * lb
    if norm2 < 1e-12:
        return []
    p0 = np.array([-lc * la / norm2, -lc * lb / norm2, 1.0])
    d = np.array([lb, -la, 0.0])
    c2 = float(d @ a @ d)
    c1 = 2.0 * float(d @ a @ p0)
    c0 = float(p0 @ a @ p0)

    roots: list[float] = []
    if abs(c2) < 1e-12:
        if abs(c1) >= 1e-12:
            roots.append(-c0 / c1)
    else:
        disc = c1 * c1 - 4.0 * c2 * c0
        if disc >= -1e-12:
            s = float(np.sqrt(max(0.0, disc)))
            roots.append((-c1 - s) / (2.0 * c2))
            roots.append((-c1 + s) / (2.0 * c2))

    return [Point(float(p0[0] + t * d[0]), float(p0[1] + t * d[1]), 0.0) for t in roots]


def _dedupe(points: list[Point], tol: float = 1e-3) -> list[Point]:
    out: list[Point] = []
    for p in points:
        if not any(np.hypot(p.x - q.x, p.y - q.y) < tol for q in out):
            out.append(p)
    return out


def two_conic_intersection(A, B) -> PointSet:
    """Intersect two conic matrices via the thesis pencil method.

    ``M = B⁻¹ A``; each real eigenvalue ``λ`` yields the degenerate conic
    ``C = A − λB``, which factors into (real) lines; intersecting those lines
    with ``A`` recovers the intersection points.
    """
    A = np.asarray(A, dtype=float)
    B = np.asarray(B, dtype=float)
    if abs(float(np.linalg.det(B))) < 1e-12:
        if abs(float(np.linalg.det(A))) < 1e-12:
            return PointSet([], kind="n_tuple")
        A, B = B, A  # intersection is symmetric; ensure B is invertible
    m = np.linalg.solve(B, A)
    points: list[Point] = []
    for lam in np.linalg.eigvals(m):
        if abs(lam.imag) > 1e-9:
            continue
        c = A - float(lam.real) * B
        for line in _line_pair_from_matrix(c):
            points.extend(_intersect_line_conic(line, A))
    points = _dedupe(points)
    return PointSet(points, kind=_kind_for(len(points)))
