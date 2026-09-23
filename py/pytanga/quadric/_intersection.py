# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Intersection of two 3D quadrics via the pencil's degenerate members.

Pure numpy (no scipy).  ``_intersect_quadrics`` finds the degenerate members of
the pencil ``span{Q1, Q2}`` and either factors a plane-pair member into two
plane-conics or samples a cone member into a polyline.  Entities are imported
lazily to preserve the ``quadric → geometry.entities`` layering.
"""

from typing import TYPE_CHECKING, Protocol, cast

import numpy as np

from ._mapping import _to_coeffs
from .conic import Conic

if TYPE_CHECKING:
    from pytanga.geometry.entities import (
        Circle,
        Curve,
        Direction,
        Ellipse,
        Hyperbola,
        Line,
        LinePair,
        Parabola,
        ParallelLinePair,
        Plane,
        PlaneConic,
        PlaneConicPair,
        Point,
    )

    class _EntitiesModule(Protocol):
        """The lazily-imported :mod:`pytanga.geometry.entities` module."""

        Circle: type[Circle]
        Curve: type[Curve]
        Direction: type[Direction]
        Ellipse: type[Ellipse]
        Hyperbola: type[Hyperbola]
        Line: type[Line]
        LinePair: type[LinePair]
        Parabola: type[Parabola]
        ParallelLinePair: type[ParallelLinePair]
        Plane: type[Plane]
        PlaneConic: type[PlaneConic]
        PlaneConicPair: type[PlaneConicPair]
        Point: type[Point]


_TOL = 1e-9

_entities_module = None


def _entities() -> "_EntitiesModule":
    """Lazily import and cache :mod:`pytanga.geometry.entities`."""
    global _entities_module
    if _entities_module is None:
        from pytanga.geometry import entities as _entities_module

    return cast("_EntitiesModule", _entities_module)


def _rank(m: np.ndarray) -> int:
    return int(np.linalg.matrix_rank(np.asarray(m, dtype=float), tol=_TOL))


def _dedupe_members(members: list[np.ndarray]) -> list[np.ndarray]:
    """Normalize and deduplicate degenerate members (scale/sign invariant)."""
    out: list[np.ndarray] = []
    for m in members:
        n = m / max(float(np.linalg.norm(m)), 1e-300)
        dup = any(
            float(np.linalg.norm(n - s)) < 1e-6 or float(np.linalg.norm(n + s)) < 1e-6
            for s in out
        )
        if not dup:
            out.append(n)
    return out


def _is_through_origin(Q: np.ndarray, tol: float = 1e-8) -> bool:
    """True if the quadric passes through the origin (last row/col ≈ 0)."""
    return float(np.linalg.norm(Q[3, :])) < tol * float(np.linalg.norm(Q))


def _plane_pair_members_from_cubic(A: np.ndarray, B: np.ndarray) -> list[np.ndarray]:
    """Rank-2 (plane-pair) members of a pencil through the origin (``b = f = 0``).

    Such a pencil's members are ``[[q, 0], [0, 0]]``, so their rank is the rank of
    the 3×3 quadratic part ``q``.  The plane pairs are where ``q`` drops rank, i.e.
    the real projective roots of the homogeneous cubic ``det(α q₁ + β q₂) = 0``.
    """
    q1 = A[:3, :3]
    q2 = B[:3, :3]

    def det_at(alpha: float) -> float:
        return float(np.linalg.det(alpha * q1 + q2))

    coeffs = np.polyfit(
        [0.0, 1.0, 2.0, 3.0], [det_at(a) for a in (0.0, 1.0, 2.0, 3.0)], 3
    )
    members: list[np.ndarray] = []
    for root in np.roots(coeffs):
        if abs(root.imag) < 1e-9:
            members.append(float(root.real) * A + B)
    # The root at infinity (β = 0) is ``A`` itself when its quadratic part drops rank.
    if _rank(q1) <= 2:
        members.append(A)
    return members


def _degenerate_members(A: np.ndarray, B: np.ndarray) -> list[np.ndarray]:
    """Real degenerate members of the pencil ``span{A, B}`` (numpy-only).

    - If ``det(B) ≠ 0`` (else if ``det(A) ≠ 0``, swap): ``solve`` + ``eigvals``
      gives the finite real eigenvalues ``λ`` → members ``A − λB``.
    - Always append ``A`` and ``B`` themselves when ``rank ≤ 3`` (the ``λ = 0``
      and ``λ = ∞`` members), which surfaces the degenerate members for the
      both-singular case (e.g. the cube, where ``det ≡ 0``).
    - When both are singular *and* pass through the origin (a common null
      vector, e.g. the cube's pencil of cones), also recover the rank-2
      plane-pair members via the cubic on the quadratic parts.
    """
    A = np.asarray(A, dtype=float)
    B = np.asarray(B, dtype=float)
    members: list[np.ndarray] = []
    if abs(float(np.linalg.det(B))) >= 1e-12:
        m = np.linalg.solve(B, A)
        for lam in np.linalg.eigvals(m):
            if abs(lam.imag) < 1e-9:
                members.append(A - float(lam.real) * B)
    elif abs(float(np.linalg.det(A))) >= 1e-12:
        m = np.linalg.solve(A, B)
        for mu in np.linalg.eigvals(m):
            if abs(mu.imag) < 1e-9 and abs(mu.real) > 1e-12:
                members.append(A - (1.0 / float(mu.real)) * B)
    for m in (A, B):
        if _rank(m) <= 3:
            members.append(m)
    if (
        abs(float(np.linalg.det(A))) < 1e-12
        and abs(float(np.linalg.det(B))) < 1e-12
        and _is_through_origin(A)
        and _is_through_origin(B)
    ):
        members.extend(_plane_pair_members_from_cubic(A, B))
    return _dedupe_members(members)


def _plane_frame(n: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Canonical orthonormal 2D basis ``(u, v)`` for a plane with normal ``n``.

    ``u = normalize(n × e_z)`` (fallback ``e_x`` when ``n ∥ e_z``), ``v = n × u``.
    """
    n = np.asarray(n, dtype=float)
    n = n / np.linalg.norm(n)
    ez = np.array([0.0, 0.0, 1.0])
    u = np.cross(n, ez)
    if float(np.linalg.norm(u)) < 1e-12:
        u = np.array([1.0, 0.0, 0.0])
    u = u / np.linalg.norm(u)
    v = np.cross(n, u)
    return u, v


def _plane_conic_from_quadric(Q: np.ndarray, plane: "Plane") -> "PlaneConic":
    """Restrict quadric ``Q`` to ``plane``; return the 2D conic as a ``PlaneConic``.

    The conic is expressed in the plane's canonical local frame ``(u, v)`` via
    ``x = plane.point + s·u + t·v``.
    """
    E = _entities()
    n = np.array([plane.normal.x, plane.normal.y, plane.normal.z], dtype=float)
    p = np.array([plane.point.x, plane.point.y, plane.point.z], dtype=float)
    u, v = _plane_frame(n)
    M = np.zeros((4, 3))
    M[:3, 0] = u
    M[:3, 1] = v
    M[:3, 2] = p
    M[3, 2] = 1.0
    a = M.T @ np.asarray(Q, dtype=float) @ M
    return E.PlaneConic(plane, Conic(_to_coeffs(a)))


def _inertia(m: np.ndarray) -> tuple[int, int, int]:
    """Return ``(n_pos, n_neg, n_zero)`` of a symmetric matrix."""
    evals = np.linalg.eigvalsh(np.asarray(m, dtype=float))
    scale = max(1.0, float(np.max(np.abs(evals))))
    tol = 1e-10 * scale
    pos = int(np.sum(evals > tol))
    neg = int(np.sum(evals < -tol))
    return pos, neg, len(evals) - pos - neg


def _plane_vectors_from_matrix(C: np.ndarray) -> list[np.ndarray]:
    """Factor a rank-1 or rank-2 quadric into homogeneous plane vectors.

    Mirrors the eigen-decomposition in ``refine.py::_plane_pair_from_quadric``
    (same sign convention): a rank-2 indefinite member → two planes
    ``√λ₊·v₊ ± √(−λ₋)·v₋``; a rank-1 member → its single (double) plane.
    """
    evals, evecs = np.linalg.eigh(C)
    r = _rank(C)
    if r == 2:
        v_pos = evecs[:, -1] * float(np.sqrt(max(0.0, evals[-1])))
        v_neg = evecs[:, 0] * float(np.sqrt(max(0.0, -evals[0])))
        return [v_pos + v_neg, v_pos - v_neg]
    if r == 1:
        idx = int(np.argmax(np.abs(evals)))
        return [evecs[:, idx]]
    return []


def _plane_from_homogeneous(
    abcd: "np.ndarray | list[float] | tuple[float, ...]",
) -> "Plane":
    """Convert a homogeneous plane ``(a, b, c, d)`` to a ``Plane`` (mirror refine.py)."""
    E = _entities()
    a, b, c, d = (float(x) for x in abcd)
    norm = float(np.sqrt(a * a + b * b + c * c))
    if norm < 1e-12:
        raise ValueError("degenerate plane (zero normal)")
    nx, ny, nz = a / norm, b / norm, c / norm
    dn = d / norm
    return E.Plane(E.Point(-dn * nx, -dn * ny, -dn * nz), E.Direction(nx, ny, nz))


def _plane_from_linear_matrix(C: np.ndarray) -> "Plane":
    """Extract the single plane of a rank-2 ``rq = 0`` matrix ``[[0, n/2], [nᵀ/2, d]]``."""
    n = 2.0 * C[:3, 3]
    d = float(C[3, 3])
    return _plane_from_homogeneous((float(n[0]), float(n[1]), float(n[2]), d))


def _parallel_planes_from_matrix(C: np.ndarray) -> list[np.ndarray]:
    """Factor a rank-2 ``rq = 1`` (parallel plane pair) into two plane vectors.

    Mirrors ``refine.py::_parallel_plane_pair_from_quadric`` (completing the
    square; the sign of the single non-zero eigenvalue is handled by magnitude).
    """
    q = C[:3, :3]
    b = C[:3, 3]
    f = float(C[3, 3])
    evals, evecs = np.linalg.eigh(q)
    idx = int(np.argmax(np.abs(evals)))
    lam = float(evals[idx])
    v = evecs[:, idx]
    beta = float(b @ v)
    shift = beta / lam
    offset = float(np.sqrt(max(0.0, beta * beta / (lam * lam) - f / lam)))
    d1 = -shift + offset
    d2 = -shift - offset
    return [np.array([v[0], v[1], v[2], -d1]), np.array([v[0], v[1], v[2], -d2])]


def _as_quadric_matrix(x: "np.ndarray | list[list[float]] | Conic") -> np.ndarray:
    """Coerce a ``Quadric3D`` (or raw array) to its 4×4 matrix."""
    if hasattr(x, "matrix"):
        return np.asarray(x.matrix, dtype=float)
    return np.asarray(x, dtype=float)


def _is_proportional(a: np.ndarray, b: np.ndarray) -> bool:
    """True if normalized ``a`` is ``±b`` (scale/sign invariant)."""
    an = a / max(float(np.linalg.norm(a)), 1e-300)
    bn = b / max(float(np.linalg.norm(b)), 1e-300)
    return min(float(np.linalg.norm(an - bn)), float(np.linalg.norm(an + bn))) < 1e-6


def _intersect_quadrics(
    Q1: "np.ndarray | Conic",
    Q2: "np.ndarray | Conic",
    n: int = 200,
    extent: float = 5.0,
) -> "PlaneConicPair | Curve":
    """Intersect two 3D quadrics via the pencil's degenerate members.

    Returns a :class:`~pytanga.geometry.PlaneConicPair` when the pencil has a
    plane-pair (or plane) member, a sampled :class:`~pytanga.geometry.Curve`
    when it has a cone member, and raises ``NotImplementedError`` for the hard
    case (no real degenerate member).  ``n``/``extent`` control the cone-member
    sampling density and the ``[-extent, extent]³`` box.
    """
    E = _entities()
    Q1 = _as_quadric_matrix(Q1)
    Q2 = _as_quadric_matrix(Q2)

    cone: np.ndarray | None = None
    cone_companion: np.ndarray | None = None
    for C in _degenerate_members(Q1, Q2):
        r = _rank(C)
        rq = _rank(C[:3, :3])
        p, n_neg, _ = _inertia(C)
        # On a plane that factors ``C`` we have ``Q1 = λQ2``; intersect the plane
        # with the quadric that is *not* ``C`` itself (so it is not identically
        # zero on that plane).  Only the ``λ = 0`` endpoint (``C ∝ Q1``) needs ``Q2``.
        companion = Q2 if _is_proportional(C, Q1) else Q1

        if r == 2 and rq == 2 and p > 0 and n_neg > 0:  # intersecting plane pair
            planes = [_plane_from_homogeneous(h) for h in _plane_vectors_from_matrix(C)]
            return E.PlaneConicPair(
                _plane_conic_from_quadric(companion, planes[0]),
                _plane_conic_from_quadric(companion, planes[1]),
            )
        if r == 2 and rq == 1:  # parallel plane pair
            planes = [
                _plane_from_homogeneous(h) for h in _parallel_planes_from_matrix(C)
            ]
            return E.PlaneConicPair(
                _plane_conic_from_quadric(companion, planes[0]),
                _plane_conic_from_quadric(companion, planes[1]),
            )
        if r == 2 and rq == 0:  # single plane (linear form)
            pc = _plane_conic_from_quadric(companion, _plane_from_linear_matrix(C))
            return E.PlaneConicPair(pc, pc)
        if r == 1:  # double plane (skip the "plane at infinity" / empty case)
            h = _plane_vectors_from_matrix(C)[0]
            if float(np.linalg.norm(h[:3])) < 1e-12:
                continue
            plane = _plane_from_homogeneous(h)
            pc = _plane_conic_from_quadric(companion, plane)
            return E.PlaneConicPair(pc, pc)
        if (
            r == 3 and rq == 3 and p > 0 and n_neg > 0 and cone is None
        ):  # cone (sampled curve)
            cone, cone_companion = C, companion
        # rank 0 / definite rank-2 / rank-3 imaginary / cylinder (rq=2) → skip
    if cone is not None:
        return _sample_curve_from_cone(
            cone, cast("np.ndarray", cone_companion), n=n, extent=extent
        )
    raise NotImplementedError("no real degenerate member (elliptic hard case)")


def _quadratic_roots(a: float, b: float, c: float) -> list[float]:
    """Real roots of ``a t² + b t + c = 0`` (empty list when none)."""
    if abs(a) < 1e-12:
        if abs(b) < 1e-12:
            return []
        return [-c / b]
    disc = b * b - 4.0 * a * c
    if disc < -1e-12:
        return []
    s = float(np.sqrt(max(0.0, disc)))
    return [(-b - s) / (2.0 * a), (-b + s) / (2.0 * a)]


def _in_box(p: np.ndarray, extent: float) -> bool:
    """Whether the 3D point ``p`` lies inside the ``[-extent, extent]³`` box."""
    return bool(
        -extent <= float(p[0]) <= extent
        and -extent <= float(p[1]) <= extent
        and -extent <= float(p[2]) <= extent
    )


def _cone_vertex(C: np.ndarray) -> np.ndarray:
    """The 3D apex of a rank-3 cone matrix ``C`` (its null vector, dehomogenised)."""
    _, _, vh = np.linalg.svd(C)
    v = vh[-1]
    w = float(v[3])
    if abs(w) < 1e-12:
        raise NotImplementedError("cone with vertex at infinity")
    return v[:3] / w


def _sample_conic_2d(
    conic: "Conic", n: int = 200, extent: float = 5.0
) -> list[list[tuple[float, float]]]:
    """Sample a 2D ``Conic`` into ordered ``(s, t)`` polylines (numpy-only).

    Returns one polyline per connected component (a closed loop for ellipse/
    circle, two branches for a hyperbola, two segments for a line pair, …), so
    the frontend never draws a spurious chord between disconnected components.
    """
    E = _entities()
    try:
        entity = conic.refine()
    except (ValueError, NotImplementedError):
        return []

    if isinstance(entity, E.Circle):
        c, r = entity.center, entity.radius
        return [
            [
                (
                    c.x + r * np.cos(2.0 * np.pi * i / n),
                    c.y + r * np.sin(2.0 * np.pi * i / n),
                )
                for i in range(n)
            ]
        ]
    if isinstance(entity, E.Ellipse):
        c, ru, rv = entity.center, entity.radius_u, entity.radius_v
        ux, uy = (
            (entity.dir_u.x, entity.dir_u.y) if entity.dir_u is not None else (1.0, 0.0)
        )
        vx, vy = (
            (entity.dir_v.x, entity.dir_v.y) if entity.dir_v is not None else (0.0, 1.0)
        )
        return [
            [
                (
                    c.x
                    + ru * np.cos(2.0 * np.pi * i / n) * ux
                    + rv * np.sin(2.0 * np.pi * i / n) * vx,
                    c.y
                    + ru * np.cos(2.0 * np.pi * i / n) * uy
                    + rv * np.sin(2.0 * np.pi * i / n) * vy,
                )
                for i in range(n)
            ]
        ]
    if isinstance(entity, E.Hyperbola):
        c, a, b = entity.center, entity.a, entity.b
        d1x, d1y = entity.dir1.x, entity.dir1.y
        d2x, d2y = entity.dir2.x, entity.dir2.y
        t_max = 2.5  # cosh(2.5) ≈ 6.13
        half = max(2, n // 2)
        paths: list[list[tuple[float, float]]] = []
        for sign in (1.0, -1.0):
            path: list[tuple[float, float]] = []
            for i in range(half):
                t = -t_max + 2.0 * t_max * i / (half - 1)
                x, y = a * np.cosh(t), sign * b * np.sinh(t)
                path.append((c.x + x * d1x + y * d2x, c.y + x * d1y + y * d2y))
            paths.append(path)
        return paths
    if isinstance(entity, E.Parabola):
        v, d, p = entity.vertex, entity.direction, entity.p
        px, py = -d.y, d.x  # perpendicular to the axis direction
        return [
            [
                (
                    v.x + (t * t / (2.0 * p)) * d.x + t * px,
                    v.y + (t * t / (2.0 * p)) * d.y + t * py,
                )
                for t in (-extent + 2.0 * extent * i / (n - 1) for i in range(n))
            ]
        ]
    if isinstance(entity, E.Line):
        o, d = entity.origin, entity.direction
        nr = float(np.hypot(d.x, d.y)) or 1.0
        ux, uy = d.x / nr, d.y / nr
        return [
            [
                (o.x - extent * ux, o.y - extent * uy),
                (o.x + extent * ux, o.y + extent * uy),
            ]
        ]
    if isinstance(entity, (E.LinePair, E.ParallelLinePair)):
        paths: list[list[tuple[float, float]]] = []
        for line in (entity.line1, entity.line2):
            o, d = line.origin, line.direction
            nr = float(np.hypot(d.x, d.y)) or 1.0
            ux, uy = d.x / nr, d.y / nr
            paths.append(
                [
                    (float(o.x - extent * ux), float(o.y - extent * uy)),
                    (float(o.x + extent * ux), float(o.y + extent * uy)),
                ]
            )
        return paths
    return []


def _dedupe_points(pts: "list[np.ndarray]", tol: float = 1e-4) -> list[np.ndarray]:
    """Drop near-duplicate points in (approximately) O(n) via a spatial hash."""
    if len(pts) < 2:
        return pts
    arr = np.asarray(pts, dtype=float)
    inv = 1.0 / tol
    out: list[np.ndarray] = []
    seen: dict[tuple[int, int, int], list[np.ndarray]] = {}
    for p in arr:
        key = (int(round(p[0] * inv)), int(round(p[1] * inv)), int(round(p[2] * inv)))
        dup = False
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for q in seen.get((key[0] + dx, key[1] + dy, key[2] + dz), ()):
                        if float(np.linalg.norm(p - q)) < tol:
                            dup = True
                            break
                    if dup:
                        break
                if dup:
                    break
            if dup:
                break
        if not dup:
            out.append(p)
            seen.setdefault(key, []).append(p)
    return out


_TENTACLE_DELTAS: tuple[float, ...] = tuple(
    float(x) for x in np.geomspace(1e-7, 0.1, 30)
)


def _tentacle_thetas(
    C: np.ndarray,
    Q: np.ndarray,
    axis: np.ndarray,
    u: np.ndarray,
    w: np.ndarray,
    cx: float,
    cy: float,
    ru: float,
    rv: float,
    ux: float,
    uy: float,
    vx: float,
    vy: float,
) -> list[float]:
    """Extra base-ellipse θ values sampling each unbounded tentacle.

    A cone ruling ``d(θ) = d0 + du·cos θ + dv·sin θ`` is asymptotic to the companion
    where ``d(θ)ᵀ q_Q d(θ) = 0`` (a quadratic in (cos θ, sin θ), i.e. a quartic in
    ``t = tan(θ/2)``).  Around each real direction the far root of the ruling
    quadratic blows up, so a geometric ladder of small θ-offsets samples the tentacle
    out toward the box (the main loop clips points past ``±extent``).
    """
    qQ = Q[:3, :3]
    d0 = axis + cx * u + cy * w
    du = ru * ux * u + ru * uy * w
    dv = rv * vx * u + rv * vy * w
    a = float(du @ qQ @ du)
    b = 2.0 * float(du @ qQ @ dv)
    c = float(dv @ qQ @ dv)
    d = 2.0 * float(d0 @ qQ @ du)
    e = 2.0 * float(d0 @ qQ @ dv)
    f = float(d0 @ qQ @ d0)
    coeffs = [
        a - d + f,
        2.0 * (e - b),
        -2.0 * a + 4.0 * c + 2.0 * f,
        2.0 * (b + e),
        a + d + f,
    ]
    while coeffs and abs(coeffs[0]) < 1e-12:
        coeffs.pop(0)
    if not coeffs:
        return []
    extra: list[float] = []
    for root in np.roots(coeffs):
        if abs(root.imag) > 1e-9:
            continue
        th0 = float(2.0 * np.arctan(float(root.real)))
        for delta in _TENTACLE_DELTAS:
            extra.append((th0 + delta) % (2.0 * np.pi))
            extra.append((th0 - delta) % (2.0 * np.pi))
    return extra


def _sample_curve_from_cone(
    C: np.ndarray, Q: np.ndarray, n: int = 200, extent: float = 5.0
) -> "Curve":
    """Sample the quartic ``C ∩ Q`` via the cone's rulings.

    The quartic is generally unbounded: it tends to infinity along the companion's
    asymptotic directions.  Those directions are solved for analytically and sampled
    out to the ``[-extent, extent]³`` box (see :func:`_tentacle_thetas`), while the
    bounded body is sampled through the cone's rulings (a double cover of the base
    conic) at a low ``n``.
    """
    E = _entities()
    v = _cone_vertex(C)
    # Cone axis: the isolated eigenvector of the 3×3 quadratic part (the unique-sign
    # eigenvalue).  The base plane is perpendicular to it, offset from the apex, so
    # it never passes through the apex (works for a cone through the origin too).
    q = C[:3, :3]
    evals, evecs = np.linalg.eigh(q)
    axis = evecs[:, 2] if float(evals[0] * evals[1]) > 0.0 else evecs[:, 0]
    base_point = v + axis
    base_plane = E.Plane(
        E.Point(float(base_point[0]), float(base_point[1]), float(base_point[2])),
        E.Direction(float(axis[0]), float(axis[1]), float(axis[2])),
    )
    pc = _plane_conic_from_quadric(C, base_plane)
    u, w = _plane_frame(axis)
    p_h = np.append(v, 1.0)

    # Base-ellipse parametrisation (s, t) = (cx + ru·cosθ·ux + rv·sinθ·vx, …), used to
    # sample the body uniformly and to place extra tentacle samples near the asymptotes.
    entity = pc.conic.refine()
    if isinstance(entity, E.Ellipse):
        cx, cy = entity.center.x, entity.center.y
        ru, rv = entity.radius_u, entity.radius_v
        ux, uy = (
            (entity.dir_u.x, entity.dir_u.y) if entity.dir_u is not None else (1.0, 0.0)
        )
        vx, vy = (
            (entity.dir_v.x, entity.dir_v.y) if entity.dir_v is not None else (0.0, 1.0)
        )
        thetas = list(np.linspace(0.0, 2.0 * np.pi, n, endpoint=False))
        thetas.extend(
            _tentacle_thetas(C, Q, axis, u, w, cx, cy, ru, rv, ux, uy, vx, vy)
        )
        thetas.sort()
        samples = [
            (
                cx + ru * np.cos(th) * ux + rv * np.sin(th) * vx,
                cy + ru * np.cos(th) * uy + rv * np.sin(th) * vy,
            )
            for th in thetas
        ]
    else:
        samples = [pt for path in _sample_conic_2d(pc.conic, n) for pt in path]

    # The quartic is a double cover of the base conic: each ruling gives up to two
    # curve points (the two "sheets").  A ruling with a negative discriminant misses
    # the companion entirely, so it breaks the current arc; keep the two sheets in
    # separate polylines so the frontend never zig-zags between them.
    sheets: list[list[list[np.ndarray]]] = [[[]], [[]]]
    for s, t in samples:
        b = base_point + s * u + t * w
        d = b - v
        d_h = np.append(d, 0.0)
        a = float(d_h @ Q @ d_h)
        bb = 2.0 * float(p_h @ Q @ d_h)
        cc = float(p_h @ Q @ p_h)
        roots = _quadratic_roots(a, bb, cc)
        if len(roots) == 0:
            if sheets[0][-1]:
                sheets[0].append([])
            if sheets[1][-1]:
                sheets[1].append([])
            continue
        p0 = v + roots[0] * d
        p1 = v + roots[1] * d if len(roots) == 2 else p0
        if _in_box(p0, extent):
            sheets[0][-1].append(p0)
        if _in_box(p1, extent):
            sheets[1][-1].append(p1)
    paths: list[list["Point"]] = []
    for sheet in sheets:
        for arc in sheet:
            arc = _dedupe_points(arc)
            if len(arc) >= 2:
                paths.append(
                    [E.Point(float(x[0]), float(x[1]), float(x[2])) for x in arc]
                )
    return E.Curve(paths)


def _unproject_to_3d(plane: "Plane", p2: "Point") -> np.ndarray:
    """Map a 2D point (plane local coords ``(s, t)``) back into the 3D frame."""
    n = np.array([plane.normal.x, plane.normal.y, plane.normal.z], dtype=float)
    p0 = np.array([plane.point.x, plane.point.y, plane.point.z], dtype=float)
    u, v = _plane_frame(n)
    return p0 + float(p2.x) * u + float(p2.y) * v


def _newton_refine(
    x0: np.ndarray,
    Q1: np.ndarray,
    Q2: np.ndarray,
    Q3: np.ndarray,
    steps: int = 12,
) -> np.ndarray:
    """Newton-refine a seed to the common zero ``Q1 = Q2 = Q3 = 0``."""
    x = np.asarray(x0, dtype=float)
    for _ in range(steps):
        h = np.append(x, 1.0)
        f = np.array([float(h @ Q @ h) for Q in (Q1, Q2, Q3)])
        j = np.array([2.0 * (Q[:3, :3] @ x + Q[:3, 3]) for Q in (Q1, Q2, Q3)])
        try:
            dx = np.linalg.solve(j, -f)
        except np.linalg.LinAlgError:
            break
        x = x + dx
        if float(np.linalg.norm(dx)) < 1e-12:
            break
    return x


def _points_on_plane_pair(pair: "PlaneConicPair", C: np.ndarray) -> list[np.ndarray]:
    """Intersect the two plane-conics of ``pair`` with ``C`` (exact)."""
    from ._pointset import _two_conic_intersection

    pts: list[np.ndarray] = []
    for pc in (pair.conic1, pair.conic2):
        q3 = _plane_conic_from_quadric(C, pc.plane)
        for p2 in _two_conic_intersection(pc.conic.matrix, q3.conic.matrix):
            pts.append(_unproject_to_3d(pc.plane, p2))
    return pts


def _residual(x: np.ndarray, Q1: np.ndarray, Q2: np.ndarray, Q3: np.ndarray) -> float:
    """Max absolute quadric value at ``x`` (zero at a common intersection)."""
    h = np.append(np.asarray(x, dtype=float), 1.0)
    return max(abs(float(h @ Q @ h)) for Q in (Q1, Q2, Q3))


def _points_on_sampled_curve(
    curve: "Curve", Q1: np.ndarray, Q2: np.ndarray, Q3: np.ndarray
) -> list[np.ndarray]:
    """Newton-refine curve samples to the common ``Q1 = Q2 = Q3 = 0`` zeros.

    Rather than relying on sign-change bracketing (which arc-splitting of the
    sampled quartic can defeat), every curve sample is used as a Newton seed;
    seeds in the basin of a base point converge to it, and the residual check
    discards seeds that did not converge to a genuine intersection.
    """
    pts: list[np.ndarray] = []
    for path in curve.paths:
        for p in path:
            r = _newton_refine(np.array([p.x, p.y, p.z], dtype=float), Q1, Q2, Q3)
            if _residual(r, Q1, Q2, Q3) < 1e-6:
                pts.append(r)
    return pts


def _finalize_intersection_points(
    pts: "list[np.ndarray]",
    Q1: np.ndarray,
    Q2: np.ndarray,
    Q3: np.ndarray,
    tol: float = 1e-6,
) -> "list[Point]":
    """Dedupe, drop off-surface points, and return 3D ``Point`` entities."""
    E = _entities()
    pts = _dedupe_points(pts, tol=1e-3)
    kept: list[np.ndarray] = []
    for p in pts:
        h = np.append(p, 1.0)
        if all(abs(float(h @ Q @ h)) < tol for Q in (Q1, Q2, Q3)):
            kept.append(p)
    return [E.Point(float(x[0]), float(x[1]), float(x[2])) for x in kept]


def _intersect_three_quadrics(
    Q1: np.ndarray, Q2: np.ndarray, Q3: np.ndarray
) -> "list[Point]":
    """Intersect three 3D quadrics → up to eight finite points.

    Reduces to :func:`_intersect_quadrics` on a well-chosen pair ``Qi ∩ Qj``
    (preferring the exact plane-pair member, else a sampled cone member) and
    then locates ``Qk = 0`` along that quartic.  Returns the distinct finite
    points lying on all three quadrics.
    """
    E = _entities()
    Q1 = _as_quadric_matrix(Q1)
    Q2 = _as_quadric_matrix(Q2)
    Q3 = _as_quadric_matrix(Q3)
    fallback = None
    for a, b, c in ((Q1, Q2, Q3), (Q1, Q3, Q2), (Q2, Q3, Q1)):
        try:
            curve = _intersect_quadrics(a, b, n=200, extent=5.0)
        except NotImplementedError:
            continue
        if isinstance(curve, E.PlaneConicPair):
            return _finalize_intersection_points(
                _points_on_plane_pair(curve, c), Q1, Q2, Q3
            )
        if fallback is None:
            fallback = cast("Curve", curve)
    if fallback is not None:
        return _finalize_intersection_points(
            _points_on_sampled_curve(fallback, Q1, Q2, Q3), Q1, Q2, Q3
        )
    raise NotImplementedError("no degenerate member in any quadric pairing")
