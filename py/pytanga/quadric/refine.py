# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Refine raw Conic / Quadric3D entities into specific geometric entities.

This is quadric-specific math (Perwass's conic-space analysis): classify the
symmetric matrix, extract its center/axes/eigenvalues, and build the concrete
2D/3D entity.  The resulting entities come from
:mod:`pytanga.geometry.entities`, imported lazily to avoid a circular import
(``pytanga.geometry.entities.conic`` imports ``pytanga.quadric`` for the
coefficient maps).
"""

from __future__ import annotations

import numpy as np

_entities = None


def _E():
    """Lazily import and cache :mod:`pytanga.geometry.entities`."""
    global _entities
    if _entities is None:
        from pytanga.geometry import entities as _entities

    return _entities


def _fprime(matrix, center_xyz) -> float:
    """Centered constant ``f' = c + bᵀ·center`` of the affine block form."""
    n = matrix.shape[0] - 1
    b = matrix[:n, n]
    c = np.asarray(center_xyz, dtype=float)
    return float(matrix[n, n] + b @ c)


def _line_from_homogeneous(abc):
    """Convert a homogeneous line ``(a, b, c)`` (``a x + b y + c = 0``) to a Line."""
    E = _E()
    a, b, c = (float(x) for x in abc)
    norm = float(np.hypot(a, b))
    if norm < 1e-12:
        raise ValueError("degenerate line (zero normal)")
    nx, ny = a / norm, b / norm
    cn = c / norm
    return E.Line(E.Point(-cn * nx, -cn * ny, 0.0), E.Direction(ny, -nx, 0.0))


def _plane_from_homogeneous(abcd):
    """Convert a homogeneous plane ``(a, b, c, d)`` (``a x + b y + c z + d = 0``)
    to a Plane."""
    E = _E()
    a, b, c, d = (float(x) for x in abcd)
    norm = float(np.sqrt(a * a + b * b + c * c))
    if norm < 1e-12:
        raise ValueError("degenerate plane (zero normal)")
    nx, ny, nz = a / norm, b / norm, c / norm
    dn = d / norm
    return E.Plane(
        E.Point(-dn * nx, -dn * ny, -dn * nz), E.Direction(nx, ny, nz)
    )


def refine_conic(conic):
    E = _E()
    kind = conic.kind
    if kind is E.EConicKind.circle:
        return E.Circle(conic.center, conic.rho)
    if kind is E.EConicKind.ellipse:
        return _ellipse_from_conic(conic)
    if kind is E.EConicKind.hyperbola:
        return _hyperbola_from_conic(conic)
    if kind is E.EConicKind.parabola:
        return _parabola_from_conic(conic)
    if kind is E.EConicKind.line:
        return _double_line_from_conic(conic)
    if kind is E.EConicKind.line_pair:
        return _line_pair_from_conic(conic)
    if kind is E.EConicKind.parallel_line_pair:
        return _parallel_line_pair_from_conic(conic)
    raise ValueError(f"conic of kind {kind.value!r} has no real entity")


def _ellipse_from_conic(conic):
    # Perwass's conic analysis: the principal directions are the eigenvectors
    # of the quadratic part and the semi-axis along each direction is
    # sqrt(-f'/lambda_i) — keep the eigenvalue/eigenvector pairing so the
    # ellipse's rotation is preserved.
    E = _E()
    lam = np.asarray(conic.eigenvalues, dtype=float)  # ascending
    dirs = conic.principal_directions  # paired with lam (ascending)
    fp = _fprime(conic.matrix, (conic.center.x, conic.center.y))
    ru = float(np.sqrt(abs(fp) / abs(lam[0])))
    rv = float(np.sqrt(abs(fp) / abs(lam[1])))
    return E.Ellipse(conic.center, ru, rv, dir_u=dirs[0], dir_v=dirs[1])


def _hyperbola_from_conic(conic):
    E = _E()
    lam = np.asarray(conic.eigenvalues, dtype=float)  # ascending: [neg, pos]
    fp = _fprime(conic.matrix, (conic.center.x, conic.center.y))
    lam_neg, lam_pos = lam[0], lam[1]
    d_neg, d_pos = conic.principal_directions
    r_pos = float(np.sqrt(abs(fp) / abs(lam_pos)))
    r_neg = float(np.sqrt(abs(fp) / abs(lam_neg)))
    if fp < 0:
        return E.Hyperbola(conic.center, d_pos, d_neg, r_pos, r_neg)
    return E.Hyperbola(conic.center, d_neg, d_pos, r_neg, r_pos)


def _parabola_from_conic(conic):
    E = _E()
    q = conic._quadratic
    b = conic.matrix[:2, 2]
    f = conic.matrix[2, 2]
    evals, evecs = np.linalg.eigh(q)
    idx = int(np.argmax(np.abs(evals)))  # the single non-zero eigenvalue
    lam = float(evals[idx])
    u = evecs[:, idx]  # non-zero eigenvector (transverse direction)
    d = np.array([-u[1], u[0]], dtype=float)  # axis direction (null space of q)
    d /= np.linalg.norm(d)

    bd = float(b @ d)
    if abs(bd) < 1e-12:
        raise ValueError("parabola extraction failed (degenerate linear part)")
    bu = float(b @ u)
    p = -bd / lam

    t_v = -bu / lam
    s_v = -(f - bu * bu / lam) / (2.0 * bd)
    vertex_xy = s_v * d + t_v * u

    if p < 0:
        d = -d
        p = -p
    return E.Parabola(
        E.Point(float(vertex_xy[0]), float(vertex_xy[1]), 0.0),
        E.Direction(float(d[0]), float(d[1]), 0.0),
        float(p),
    )


def _double_line_from_conic(conic):
    E = _E()
    evals, evecs = np.linalg.eigh(conic.matrix)
    abc = evecs[:, -1]  # eigenvector of the largest (non-zero) eigenvalue
    return _line_from_homogeneous(abc)


def _line_pair_from_conic(conic):
    E = _E()
    evals, evecs = np.linalg.eigh(conic.matrix)  # ascending: [neg, 0, pos]
    v_pos = evecs[:, -1]
    v_neg = evecs[:, 0]
    a = float(np.sqrt(max(0.0, evals[-1]))) * v_pos
    b = float(np.sqrt(max(0.0, -evals[0]))) * v_neg
    return E.LinePair(_line_from_homogeneous(a + b), _line_from_homogeneous(a - b))


def _parallel_line_pair_from_conic(conic):
    E = _E()
    q = conic._quadratic
    b = conic.matrix[:2, 2]
    f = conic.matrix[2, 2]
    evals, evecs = np.linalg.eigh(q)  # ascending: [0, lam]
    lam = float(evals[1])
    v = evecs[:, 1]  # non-zero eigenvector (unit)
    beta = float(b @ v)
    shift = beta / lam
    offset = float(np.sqrt(max(0.0, beta * beta / (lam * lam) - f / lam)))
    d1 = -shift + offset
    d2 = -shift - offset
    return E.ParallelLinePair(
        _line_from_homogeneous((v[0], v[1], -d1)),
        _line_from_homogeneous((v[0], v[1], -d2)),
    )



def refine_quadric(quadric):
    E = _E()
    kind = quadric.kind
    if kind is E.EQuadricKind.sphere:
        return E.Sphere(quadric.center, quadric.rho)
    if kind is E.EQuadricKind.ellipsoid:
        return _ellipsoid_from_quadric(quadric)
    if kind in (E.EQuadricKind.elliptic_cylinder, E.EQuadricKind.hyperbolic_cylinder):
        return _cylinder_from_quadric(quadric)
    if kind is E.EQuadricKind.cone:
        return _cone_from_quadric(quadric)
    if kind is E.EQuadricKind.plane:
        return _plane_from_quadric(quadric)
    if kind is E.EQuadricKind.plane_pair:
        return _plane_pair_from_quadric(quadric)
    if kind is E.EQuadricKind.parallel_plane_pair:
        return _parallel_plane_pair_from_quadric(quadric)
    raise ValueError(f"quadric of kind {kind.value!r} has no specific entity")


def _ellipsoid_from_quadric(quadric):
    E = _E()
    lam = np.asarray(quadric.eigenvalues, dtype=float)  # ascending
    fp = _fprime(
        quadric.matrix, (quadric.center.x, quadric.center.y, quadric.center.z)
    )
    # Semi-axes in descending order; rotation is left as None (axis-aligned
    # principal frame — a rotated ellipsoid keeps the same radii magnitudes).
    radii = tuple(
        sorted((float(np.sqrt(abs(fp) / abs(lam_i))) for lam_i in lam), reverse=True)
    )
    return E.Ellipsoid(quadric.center, radii)


def _cylinder_from_quadric(quadric):
    E = _E()
    q = quadric._quadratic
    b = quadric.matrix[:3, 3]
    evals, evecs = np.linalg.eigh(q)
    zero_idx = int(np.argmin(np.abs(evals)))  # the zero eigenvalue
    axis = evecs[:, zero_idx]
    lam1, lam2 = (float(evals[i]) for i in range(3) if i != zero_idx)
    c = np.linalg.lstsq(q, -b, rcond=None)[0]
    fp = float(quadric.matrix[3, 3] + b @ c)
    lam_mean = (lam1 + lam2) / 2.0
    radius = float(np.sqrt(max(0.0, -fp / lam_mean)))
    return E.Cylinder(
        E.Point(float(c[0]), float(c[1]), float(c[2])),
        E.Direction(float(axis[0]), float(axis[1]), float(axis[2])),
        length=1.0,
        radius=radius,
        align_center=0.5,
    )


def _cone_from_quadric(quadric):
    E = _E()
    matrix = quadric.matrix
    q = quadric._quadratic
    # Apex = the (dehomogenized) null vector of the full 4×4 matrix.
    _, _, vh = np.linalg.svd(matrix)
    null = vh[-1]
    w = float(null[3])
    if abs(w) < 1e-12:
        raise ValueError("cone apex at infinity")
    vertex = E.Point(float(null[0] / w), float(null[1] / w), float(null[2] / w))

    evals, evecs = np.linalg.eigh(q)  # ascending
    scale = max(1.0, float(np.max(np.abs(evals))))
    if abs(evals[0] - evals[1]) < 1e-10 * scale:
        lam_single, v_single, lam_rep = float(evals[2]), evecs[:, 2], float(evals[0])
    else:
        lam_single, v_single, lam_rep = float(evals[0]), evecs[:, 0], float(evals[1])
    half_angle = float(np.arctan(np.sqrt(abs(lam_single) / abs(lam_rep))))
    return E.Cone(
        vertex,
        E.Direction(float(v_single[0]), float(v_single[1]), float(v_single[2])),
        half_angle,
    )


def _plane_from_quadric(quadric):
    E = _E()
    matrix = quadric.matrix
    a = 2.0 * float(matrix[0, 3])
    b = 2.0 * float(matrix[1, 3])
    c = 2.0 * float(matrix[2, 3])
    d = float(matrix[3, 3])
    norm = float(np.sqrt(a * a + b * b + c * c))
    if norm < 1e-12:
        raise ValueError("degenerate plane (zero normal)")
    nx, ny, nz = a / norm, b / norm, c / norm
    dn = d / norm
    return E.Plane(
        E.Point(-dn * nx, -dn * ny, -dn * nz),
        E.Direction(nx, ny, nz),
    )


def _plane_pair_from_quadric(quadric):
    # Perwass's degenerate-quadric analysis (ConicIntersect.tex §"Analysis of
    # Conics", extended to 3D): a rank-2 quadric is a plane pair, and its two
    # homogeneous plane vectors are √λ₊·v₊ ± √(−λ₋)·v₋ from the eigen-decomposition
    # (mirroring _line_pair_from_conic).
    E = _E()
    evals, evecs = np.linalg.eigh(quadric.matrix)  # ascending: [neg, 0, 0, pos]
    v_pos = evecs[:, -1]
    v_neg = evecs[:, 0]
    a = float(np.sqrt(max(0.0, evals[-1]))) * v_pos
    b = float(np.sqrt(max(0.0, -evals[0]))) * v_neg
    return E.PlanePair(
        _plane_from_homogeneous(a + b),
        _plane_from_homogeneous(a - b),
    )


def _parallel_plane_pair_from_quadric(quadric):
    # Two parallel planes: the 3×3 quadratic part has rank 1 (a single non-zero
    # eigenvalue), mirroring _parallel_line_pair_from_conic.
    E = _E()
    q = quadric._quadratic
    b = quadric.matrix[:3, 3]
    f = quadric.matrix[3, 3]
    evals, evecs = np.linalg.eigh(q)  # ascending; the single non-zero eigenvalue
    idx = int(np.argmax(np.abs(evals)))  # may be negative (matrix sign is arbitrary)
    lam = float(evals[idx])
    v = evecs[:, idx]  # non-zero eigenvector (unit)
    beta = float(b @ v)
    shift = beta / lam
    offset = float(np.sqrt(max(0.0, beta * beta / (lam * lam) - f / lam)))
    d1 = -shift + offset
    d2 = -shift - offset
    return E.ParallelPlanePair(
        _plane_from_homogeneous((v[0], v[1], v[2], -d1)),
        _plane_from_homogeneous((v[0], v[1], v[2], -d2)),
    )

