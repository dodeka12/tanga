# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Entity / operator → MV creation for the quadric spaces (2D conics, 3D quadrics).

Pure quadric math: symmetric-matrix/coefficient → MV, point embedding, and the
conic-space rotation rotor.  The specific geometry entities (``Circle``,
``Ellipse``, ``Sphere``, …) are imported lazily, mirroring
:mod:`pytanga.quadric.refine`, so the package keeps no import-time dependency
on ``pytanga.geometry``.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Protocol, cast

import numpy as np

from ._embedding import embed_point
from ._mapping import to_coeffs
from .conic import Conic, Quadric3D

if TYPE_CHECKING:
    from pytanga.algebra._algebra import Algebra
    from pytanga.algebra._mv import MV
    from pytanga.entity import Direction, Point
    from pytanga.geometry.entities import (
        Circle,
        Cone,
        Cylinder,
        Ellipse,
        Ellipsoid,
        Entity,
        Hyperbola,
        Line,
        LinePair,
        Parabola,
        ParallelLinePair,
        ParallelPlanePair,
        Plane,
        PlanePair,
        Sphere,
    )

    class _EntitiesModule(Protocol):
        """The lazily-imported :mod:`pytanga.geometry.entities` module."""

        Circle: type[Circle]
        Cone: type[Cone]
        Cylinder: type[Cylinder]
        Ellipse: type[Ellipse]
        Ellipsoid: type[Ellipsoid]
        Hyperbola: type[Hyperbola]
        Line: type[Line]
        LinePair: type[LinePair]
        Parabola: type[Parabola]
        ParallelLinePair: type[ParallelLinePair]
        ParallelPlanePair: type[ParallelPlanePair]
        Plane: type[Plane]
        PlanePair: type[PlanePair]
        Sphere: type[Sphere]


_entities_module = None


def _entities() -> "_EntitiesModule":
    """Lazily import and cache :mod:`pytanga.geometry.entities`."""
    global _entities_module
    if _entities_module is None:
        from pytanga.geometry import entities as _entities_module

    return cast("_EntitiesModule", _entities_module)


def _coeffs_to_mv(basis: "Algebra", coeffs: "tuple[float, ...]") -> MV:
    mv = basis.multivector({1 << i: float(coeffs[i]) for i in range(basis.dim)})
    if basis.opns:
        mv = mv.undual()
    return mv


def _matrix_to_mv(basis: "Algebra", matrix: np.ndarray) -> MV:
    return _coeffs_to_mv(basis, to_coeffs(matrix))


def create_point(basis: "Algebra", x: float, y: float, z: float = 0.0) -> MV:
    if basis.dim == 6:
        mv = embed_point(basis, x, y)
    else:
        mv = embed_point(basis, x, y, z)
    if not basis.opns:
        mv = mv.dual()
    return mv


def create_conic(basis: "Algebra", conic: Conic) -> MV:
    return _coeffs_to_mv(basis, conic.coeffs)


def create_circle(
    basis: "Algebra", center: "Point", normal: "Direction | None", radius: float
) -> MV:
    del normal  # 2D conic space: the circle lies in the xy-plane
    cx, cy = center.x, center.y
    matrix = np.array(
        [
            [1.0, 0.0, -cx],
            [0.0, 1.0, -cy],
            [-cx, -cy, cx * cx + cy * cy - radius * radius],
        ]
    )
    return _matrix_to_mv(basis, matrix)


def create_ellipse(basis: "Algebra", ellipse: "Ellipse") -> MV:
    cx, cy = ellipse.center.x, ellipse.center.y
    a2 = ellipse.radius_u**2
    b2 = ellipse.radius_v**2
    matrix = np.array(
        [
            [1.0 / a2, 0.0, -cx / a2],
            [0.0, 1.0 / b2, -cy / b2],
            [-cx / a2, -cy / b2, cx * cx / a2 + cy * cy / b2 - 1.0],
        ]
    )
    return _matrix_to_mv(basis, matrix)


def create_hyperbola(basis: "Algebra", hyperbola: "Hyperbola") -> MV:
    d1 = np.array([hyperbola.dir1.x, hyperbola.dir1.y])
    d2 = np.array([hyperbola.dir2.x, hyperbola.dir2.y])
    q = np.outer(d1, d1) / hyperbola.a**2 - np.outer(d2, d2) / hyperbola.b**2
    c = np.array([hyperbola.center.x, hyperbola.center.y])
    b = -q @ c
    f = float(c @ q @ c) - 1.0
    matrix = np.array(
        [[q[0, 0], q[0, 1], b[0]], [q[1, 0], q[1, 1], b[1]], [b[0], b[1], f]]
    )
    return _matrix_to_mv(basis, matrix)


def create_parabola(basis: "Algebra", parabola: "Parabola") -> MV:
    d = np.array([parabola.direction.x, parabola.direction.y])
    d = d / np.linalg.norm(d)
    u = np.array([-d[1], d[0]])  # transverse direction
    v = np.array([parabola.vertex.x, parabola.vertex.y])
    p = parabola.p
    q = np.outer(u, u)
    b = -(v @ u) * u - p * d
    f = float((v @ u) ** 2) + 2.0 * p * float(v @ d)
    matrix = np.array(
        [[q[0, 0], q[0, 1], b[0]], [q[1, 0], q[1, 1], b[1]], [b[0], b[1], f]]
    )
    return _matrix_to_mv(basis, matrix)


def _normalized_line(
    origin: "Point", direction: "Direction"
) -> tuple[float, float, float]:
    nx, ny = direction.y, -direction.x
    norm = float(np.hypot(nx, ny))
    nx, ny = nx / norm, ny / norm
    c = -(nx * origin.x + ny * origin.y)
    return nx, ny, c


def create_line(basis: "Algebra", origin: "Point", direction: "Direction") -> MV:
    a, b, c = _normalized_line(origin, direction)
    lv = np.array([a, b, c])
    return _matrix_to_mv(basis, np.outer(lv, lv))


def create_line_pair(basis: "Algebra", pair: "LinePair") -> MV:
    l1 = np.array(_normalized_line(pair.line1.origin, pair.line1.direction))
    l2 = np.array(_normalized_line(pair.line2.origin, pair.line2.direction))
    return _matrix_to_mv(basis, np.outer(l1, l2) + np.outer(l2, l1))


def create_parallel_line_pair(basis: "Algebra", pair: "ParallelLinePair") -> MV:
    a, b, c1 = _normalized_line(pair.line1.origin, pair.line1.direction)
    _, _, c2 = _normalized_line(pair.line2.origin, pair.line2.direction)
    mid = (c1 + c2) / 2.0
    matrix = np.array(
        [
            [a * a, a * b, mid * a],
            [a * b, b * b, mid * b],
            [mid * a, mid * b, c1 * c2],
        ]
    )
    return _matrix_to_mv(basis, matrix)


def create_quadric(basis: "Algebra", quadric: Quadric3D) -> MV:
    return _coeffs_to_mv(basis, quadric.coeffs)


def _centered_matrix(q: np.ndarray, c: np.ndarray, const: float) -> np.ndarray:
    b = -q @ c
    f = float(c @ q @ c) + const
    return np.block([[q, b[:, None]], [b[None, :], np.array([[f]])]])


def create_sphere(basis: "Algebra", center: "Point", radius: float) -> MV:
    q = np.eye(3)
    c = np.array([center.x, center.y, center.z])
    return _matrix_to_mv(basis, _centered_matrix(q, c, -radius * radius))


def create_ellipsoid(basis: "Algebra", ellipsoid: "Ellipsoid") -> MV:
    rx, ry, rz = (float(r) for r in ellipsoid.radii)
    q = np.diag([1.0 / rx**2, 1.0 / ry**2, 1.0 / rz**2])
    c = np.array([ellipsoid.center.x, ellipsoid.center.y, ellipsoid.center.z])
    return _matrix_to_mv(basis, _centered_matrix(q, c, -1.0))


def create_cylinder(basis: "Algebra", cylinder: "Cylinder") -> MV:
    axis = np.array([cylinder.axis.x, cylinder.axis.y, cylinder.axis.z])
    axis = axis / np.linalg.norm(axis)
    q = np.eye(3) - np.outer(axis, axis)
    c = np.array([cylinder.origin.x, cylinder.origin.y, cylinder.origin.z])
    return _matrix_to_mv(basis, _centered_matrix(q, c, -(cylinder.radius**2)))


def create_cone(basis: "Algebra", cone: "Cone") -> MV:
    axis = np.array([cone.axis.x, cone.axis.y, cone.axis.z])
    axis = axis / np.linalg.norm(axis)
    sec2 = 1.0 / (np.cos(cone.half_angle) ** 2)
    q = np.eye(3) - sec2 * np.outer(axis, axis)
    c = np.array([cone.vertex.x, cone.vertex.y, cone.vertex.z])
    return _matrix_to_mv(basis, _centered_matrix(q, c, 0.0))


def create_plane(basis: "Algebra", plane: "Plane") -> MV:
    n = np.array([plane.normal.x, plane.normal.y, plane.normal.z])
    n = n / np.linalg.norm(n)
    d = -float(n @ np.array([plane.point.x, plane.point.y, plane.point.z]))
    matrix = np.zeros((4, 4))
    matrix[:3, 3] = n / 2.0
    matrix[3, :3] = n / 2.0
    matrix[3, 3] = d
    return _matrix_to_mv(basis, matrix)


def _normalized_plane(plane: "Plane") -> np.ndarray:
    n = np.array([plane.normal.x, plane.normal.y, plane.normal.z])
    n = n / np.linalg.norm(n)
    d = -float(n @ np.array([plane.point.x, plane.point.y, plane.point.z]))
    return np.array([n[0], n[1], n[2], d])


def create_plane_pair(basis: "Algebra", pair: "PlanePair") -> MV:
    p1 = _normalized_plane(pair.plane1)
    p2 = _normalized_plane(pair.plane2)
    return _matrix_to_mv(basis, np.outer(p1, p2) + np.outer(p2, p1))


def create_parallel_plane_pair(basis: "Algebra", pair: "ParallelPlanePair") -> MV:
    a, b, c, d1 = _normalized_plane(pair.plane1)
    _, _, _, d2 = _normalized_plane(pair.plane2)
    mid = (d1 + d2) / 2.0
    n = np.array([a, b, c])
    matrix = np.block(
        [
            [np.outer(n, n), mid * n[:, None]],
            [mid * n[None, :], np.array([[d1 * d2]])],
        ]
    )
    return _matrix_to_mv(basis, matrix)


def create_entity(
    basis: "Algebra", entity: "Entity | Ellipse | Ellipsoid | Cylinder"
) -> MV:
    E = _entities()
    if basis.dim == 6:
        if isinstance(entity, Conic):
            return create_conic(basis, entity)
        if isinstance(entity, E.Circle):
            return create_circle(basis, entity.center, entity.normal, entity.radius)
        if isinstance(entity, E.Ellipse):
            return create_ellipse(basis, entity)
        if isinstance(entity, E.Hyperbola):
            return create_hyperbola(basis, entity)
        if isinstance(entity, E.Parabola):
            return create_parabola(basis, entity)
        if isinstance(entity, E.Line):
            return create_line(basis, entity.origin, entity.direction)
        if isinstance(entity, E.ParallelLinePair):
            return create_parallel_line_pair(basis, entity)
        if isinstance(entity, E.LinePair):
            return create_line_pair(basis, entity)
        raise TypeError(f"Entity type {type(entity).__name__} not supported in Q2")
    if isinstance(entity, Quadric3D):
        return create_quadric(basis, entity)
    if isinstance(entity, E.Sphere):
        return create_sphere(basis, entity.center, entity.radius)
    if isinstance(entity, E.Ellipsoid):
        return create_ellipsoid(basis, entity)
    if isinstance(entity, E.Cylinder):
        return create_cylinder(basis, entity)
    if isinstance(entity, E.Cone):
        return create_cone(basis, entity)
    if isinstance(entity, E.Plane):
        return create_plane(basis, entity)
    if isinstance(entity, E.ParallelPlanePair):
        return create_parallel_plane_pair(basis, entity)
    if isinstance(entity, E.PlanePair):
        return create_plane_pair(basis, entity)
    raise TypeError(f"Entity type {type(entity).__name__} not supported in Q3")


def _q3_rotor(basis: "Algebra", theta: float, axis: "Direction") -> MV:
    """Rotation about an arbitrary axis in the 3D quadric space (``CA{10}``).

    Built as ``R_lin · R_mixed · R_quad`` — three commuting factors acting on the
    linear, mixed-quadratic, and traceless-quadratic monomials at rates ``θ, θ, 2θ``
    (see ``dev/notes/quadric-rotor-derivation.md``).
    """
    r = np.array([axis.x, axis.y, axis.z], dtype=float)
    norm = float(np.linalg.norm(r))
    if norm < 1e-15:
        raise ValueError("rotor axis must be non-zero")
    r /= norm
    ref = np.array([0.0, 0.0, 1.0]) if abs(r[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    p = np.cross(ref, r)
    p /= np.linalg.norm(p)
    q = np.cross(r, p)

    sqrt2 = math.sqrt(2.0)
    c = math.cos(theta)
    s = math.sin(theta)
    c2 = math.cos(theta / 2.0)
    s2 = math.sin(theta / 2.0)

    def _lin(v: np.ndarray) -> MV:
        return basis.multivector({1: v[0], 2: v[1], 4: v[2]})

    def _quad(v: np.ndarray) -> MV:
        # D_u = M(u uᵀ) — the u² monomial blade.
        x, y, z = v
        return basis.multivector(
            {
                16: sqrt2 / 2.0 * x * x,
                32: sqrt2 / 2.0 * y * y,
                64: sqrt2 / 2.0 * z * z,
                128: x * y,
                256: x * z,
                512: y * z,
            }
        )

    def _cross(u: np.ndarray, v: np.ndarray) -> MV:
        # X_uv = M(u vᵀ + v uᵀ) — the uv monomial blade.
        return basis.multivector(
            {
                16: sqrt2 * u[0] * v[0],
                32: sqrt2 * u[1] * v[1],
                64: sqrt2 * u[2] * v[2],
                128: u[0] * v[1] + u[1] * v[0],
                256: u[0] * v[2] + u[2] * v[0],
                512: u[1] * v[2] + u[2] * v[1],
            }
        )

    P = _lin(p)
    Q = _lin(q)
    r_lin = basis.multivector({0: c2}) - s2 * (P ^ Q)
    r_mixed = basis.multivector({0: c2}) - s2 * (_cross(p, r) ^ _cross(q, r))
    r_quad = basis.multivector({0: c}) - s * ((_quad(p) - _quad(q)) ^ _cross(p, q))
    return r_lin * r_mixed * r_quad


def create_rotor(basis: "Algebra", angle: float, axis: "Direction") -> MV:
    """Quadric-space rotation rotor (Perwass, GAConicSpc eqn. GAGeo:C2:RotorDef1).

    Q2 (2D conic space, ``dim == 6``) — applied as ``R A R̃``, with

    * ``R₁ = cos θ − (√2/2)·sin θ·(b₄∧b₆ − b₅∧b₆)``
    * ``R₂ = cos(θ/2) − sin(θ/2)·b₁∧b₂``

    expressed in the Euclidean-rescaled ``CA{6}`` basis (``b₃₄₅ = e₃₄₅/√2``).
    The rotation axis is implicit (the ``b₁₂`` plane, i.e. about the z-axis), so
    ``axis`` is ignored.

    Q3 (3D quadric space, ``dim == 10``) — a rotation about the (normalised)
    ``axis`` by ``angle``, as ``R_lin · R_mixed · R_quad`` (three commuting factors;
    see ``dev/notes/quadric-rotor-derivation.md``).

    The rotor is an even versor (grades 0, 2, 4 in Q2; 0, 2, 4, 6 in Q3) and is
    independent of the OPNS/IPNS flag.
    """
    if basis.dim == 6:
        theta = float(angle)
        c1 = math.cos(theta)
        s1 = math.sin(theta)
        c2 = math.cos(theta / 2.0)
        s2 = math.sin(theta / 2.0)
        k = math.sqrt(2.0) / 2.0 * s1

        b12 = 1 | 2  # b₁∧b₂
        b46 = 8 | 32  # b₄∧b₆
        b56 = 16 | 32  # b₅∧b₆

        r1 = basis.multivector({0: c1, b46: -k, b56: k})
        r2 = basis.multivector({0: c2, b12: -s2})
        return r2 * r1
    if basis.dim == 10:
        return _q3_rotor(basis, float(angle), axis)
    raise ValueError(f"unsupported quadric basis dimension: {basis.dim}")
