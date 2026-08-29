# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Q2 (2D quadric / conic space) creation — entities → MV."""

from __future__ import annotations

import numpy as np

from pytanga.quadric import embed_point, to_coeffs

from .entities import (
    Circle,
    Conic,
    Ellipse,
    Hyperbola,
    Line,
    LinePair,
    ParallelLinePair,
    Parabola,
)


def _coeffs_to_mv(basis, coeffs):
    mv = basis.multivector({1 << i: float(coeffs[i]) for i in range(basis.dim)})
    if basis.opns:
        mv = mv.undual()
    return mv


def _matrix_to_mv(basis, matrix):
    return _coeffs_to_mv(basis, to_coeffs(matrix))


def create_entity(basis, entity):
    if isinstance(entity, Conic):
        return create_conic(basis, entity)
    if isinstance(entity, Circle):
        return create_circle(basis, entity.center, entity.normal, entity.radius)
    if isinstance(entity, Ellipse):
        return create_ellipse(basis, entity)
    if isinstance(entity, Hyperbola):
        return create_hyperbola(basis, entity)
    if isinstance(entity, Parabola):
        return create_parabola(basis, entity)
    if isinstance(entity, Line):
        return create_line(basis, entity.origin, entity.direction)
    if isinstance(entity, ParallelLinePair):
        return create_parallel_line_pair(basis, entity)
    if isinstance(entity, LinePair):
        return create_line_pair(basis, entity)
    raise TypeError(f"Entity type {type(entity).__name__} not supported in Q2")


def create_point(basis, x, y, z):
    mv = embed_point(basis, x, y)
    if not basis.opns:
        mv = mv.dual()
    return mv


def create_conic(basis, conic):
    return _coeffs_to_mv(basis, conic.coeffs)


def create_circle(basis, center, normal, radius):
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


def create_ellipse(basis, ellipse):
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


def create_hyperbola(basis, hyperbola):
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


def create_parabola(basis, parabola):
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


def _normalized_line(origin, direction):
    nx, ny = direction.y, -direction.x
    norm = float(np.hypot(nx, ny))
    nx, ny = nx / norm, ny / norm
    c = -(nx * origin.x + ny * origin.y)
    return nx, ny, c


def create_line(basis, origin, direction):
    a, b, c = _normalized_line(origin, direction)
    lv = np.array([a, b, c])
    return _matrix_to_mv(basis, np.outer(lv, lv))


def create_line_pair(basis, pair):
    l1 = np.array(_normalized_line(pair.line1.origin, pair.line1.direction))
    l2 = np.array(_normalized_line(pair.line2.origin, pair.line2.direction))
    return _matrix_to_mv(basis, np.outer(l1, l2) + np.outer(l2, l1))


def create_parallel_line_pair(basis, pair):
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
