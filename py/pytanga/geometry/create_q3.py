# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Q3 (3D quadric space) creation — entities → MV."""

from __future__ import annotations

import numpy as np

from pytanga.quadric import embed_point, to_coeffs

from .entities import (
    Cone,
    Cylinder,
    Ellipsoid,
    Plane,
    Quadric3D,
    Sphere,
)


def _coeffs_to_mv(basis, coeffs):
    mv = basis.multivector({1 << i: float(coeffs[i]) for i in range(basis.dim)})
    if basis.opns:
        mv = mv.undual()
    return mv


def _matrix_to_mv(basis, matrix):
    return _coeffs_to_mv(basis, to_coeffs(matrix))


def create_entity(basis, entity):
    if isinstance(entity, Quadric3D):
        return create_quadric(basis, entity)
    if isinstance(entity, Sphere):
        return create_sphere(basis, entity.center, entity.radius)
    if isinstance(entity, Ellipsoid):
        return create_ellipsoid(basis, entity)
    if isinstance(entity, Cylinder):
        return create_cylinder(basis, entity)
    if isinstance(entity, Cone):
        return create_cone(basis, entity)
    if isinstance(entity, Plane):
        return create_plane(basis, entity)
    raise TypeError(f"Entity type {type(entity).__name__} not supported in Q3")


def create_point(basis, x, y, z):
    mv = embed_point(basis, x, y, z)
    if not basis.opns:
        mv = mv.dual()
    return mv


def create_quadric(basis, quadric):
    return _coeffs_to_mv(basis, quadric.coeffs)


def _centered_matrix(q, c, const):
    b = -q @ c
    f = float(c @ q @ c) + const
    return np.block([[q, b[:, None]], [b[None, :], np.array([[f]])]])


def create_sphere(basis, center, radius):
    q = np.eye(3)
    c = np.array([center.x, center.y, center.z])
    return _matrix_to_mv(basis, _centered_matrix(q, c, -radius * radius))


def create_ellipsoid(basis, ellipsoid):
    rx, ry, rz = (float(r) for r in ellipsoid.radii)
    q = np.diag([1.0 / rx**2, 1.0 / ry**2, 1.0 / rz**2])
    c = np.array([ellipsoid.center.x, ellipsoid.center.y, ellipsoid.center.z])
    return _matrix_to_mv(basis, _centered_matrix(q, c, -1.0))


def create_cylinder(basis, cylinder):
    axis = np.array([cylinder.axis.x, cylinder.axis.y, cylinder.axis.z])
    axis = axis / np.linalg.norm(axis)
    q = np.eye(3) - np.outer(axis, axis)
    c = np.array([cylinder.origin.x, cylinder.origin.y, cylinder.origin.z])
    return _matrix_to_mv(basis, _centered_matrix(q, c, -(cylinder.radius**2)))


def create_cone(basis, cone):
    axis = np.array([cone.axis.x, cone.axis.y, cone.axis.z])
    axis = axis / np.linalg.norm(axis)
    sec2 = 1.0 / (np.cos(cone.half_angle) ** 2)
    q = np.eye(3) - sec2 * np.outer(axis, axis)
    c = np.array([cone.vertex.x, cone.vertex.y, cone.vertex.z])
    return _matrix_to_mv(basis, _centered_matrix(q, c, 0.0))


def create_plane(basis, plane):
    n = np.array([plane.normal.x, plane.normal.y, plane.normal.z])
    n = n / np.linalg.norm(n)
    d = -float(n @ np.array([plane.point.x, plane.point.y, plane.point.z]))
    matrix = np.zeros((4, 4))
    matrix[:3, 3] = n / 2.0
    matrix[3, :3] = n / 2.0
    matrix[3, 3] = d
    return _matrix_to_mv(basis, matrix)
