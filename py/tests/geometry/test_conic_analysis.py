# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for grade-1/dual analysis + refine() to specific entities."""

import numpy as np
import pytest

from pytanga.geometry import (
    Circle,
    Cone,
    Conic,
    Cylinder,
    Ellipse,
    Ellipsoid,
    Geometry,
    Hyperbola,
    LinePair,
    Parabola,
    Plane,
    Point,
    Quadric3D,
    Sphere,
    analyze,
    analyze_entity,
    refine,
)
from pytanga.quadric import BasisQ2, BasisQ3, to_coeffs


def _coeff_mv(basis, coeffs):
    return basis.multivector({1 << i: c for i, c in enumerate(coeffs)})


def _refine_conic(matrix):
    basis = BasisQ2(opns=False)
    mv = _coeff_mv(basis, to_coeffs(matrix))
    conic = analyze_entity(mv)
    assert isinstance(conic, Conic)
    return refine(conic)


def _refine_quadric(matrix):
    basis = BasisQ3(opns=False)
    mv = _coeff_mv(basis, to_coeffs(matrix))
    quadric = analyze_entity(mv)
    assert isinstance(quadric, Quadric3D)
    return refine(quadric)


class TestAnalyzeConic:
    def test_point_opns(self):
        b = BasisQ2()  # opns=True
        from pytanga.quadric import embed_point

        p = analyze_entity(embed_point(b, 3.0, 4.0))
        assert isinstance(p, Point)
        assert p.x == pytest.approx(3.0)
        assert p.y == pytest.approx(4.0)
        assert p.z == pytest.approx(0.0)

    def test_conic_ipns(self):
        b = BasisQ2(opns=False)
        matrix = np.array([[1.0, 0.0, -1.0], [0.0, 1.0, -2.0], [-1.0, -2.0, 1.0]])
        conic = analyze_entity(_coeff_mv(b, to_coeffs(matrix)))
        assert isinstance(conic, Conic)
        assert conic.coeffs == pytest.approx(to_coeffs(matrix))


class TestRefineConic:
    def test_circle(self):
        matrix = np.array([[1.0, 0.0, -1.0], [0.0, 1.0, -2.0], [-1.0, -2.0, 1.0]])
        c = _refine_conic(matrix)
        assert isinstance(c, Circle)
        assert c.center.x == pytest.approx(1.0)
        assert c.center.y == pytest.approx(2.0)
        assert c.radius == pytest.approx(2.0)

    def test_ellipse(self):
        matrix = np.diag([0.25, 1.0 / 9.0, -1.0])
        e = _refine_conic(matrix)
        assert isinstance(e, Ellipse)
        assert e.center == Point(0.0, 0.0, 0.0)
        assert sorted((e.radius_u, e.radius_v)) == pytest.approx([2.0, 3.0])

    def test_hyperbola(self):
        matrix = np.diag([1.0, -1.0, -1.0])
        h = _refine_conic(matrix)
        assert isinstance(h, Hyperbola)
        assert h.a == pytest.approx(1.0)
        assert h.b == pytest.approx(1.0)
        assert h.center == Point(0.0, 0.0, 0.0)

    def test_parabola(self):
        matrix = np.array([[0.0, 0.0, -1.0], [0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]])
        p = _refine_conic(matrix)
        assert isinstance(p, Parabola)
        assert p.p == pytest.approx(1.0)
        assert p.vertex.x == pytest.approx(0.0)
        assert p.vertex.y == pytest.approx(0.0)
        assert p.direction.x == pytest.approx(1.0)

    def test_line_pair(self):
        matrix = np.array([[0.0, 0.5, 0.0], [0.5, 0.0, 0.0], [0.0, 0.0, 0.0]])
        lp = _refine_conic(matrix)
        assert isinstance(lp, LinePair)

    def test_general_hyperboloid_raises(self):
        matrix = np.diag([1.0, 1.0, -1.0, -1.0])
        with pytest.raises(ValueError):
            _refine_quadric(matrix)


class TestRefineQuadric:
    def test_sphere(self):
        matrix = np.array(
            [
                [1.0, 0.0, 0.0, -1.0],
                [0.0, 1.0, 0.0, -2.0],
                [0.0, 0.0, 1.0, -3.0],
                [-1.0, -2.0, -3.0, 10.0],
            ]
        )
        s = _refine_quadric(matrix)
        assert isinstance(s, Sphere)
        assert s.center.x == pytest.approx(1.0)
        assert s.center.y == pytest.approx(2.0)
        assert s.center.z == pytest.approx(3.0)
        assert s.radius == pytest.approx(2.0)

    def test_ellipsoid(self):
        matrix = np.diag([0.25, 1.0 / 9.0, 1.0 / 16.0, -1.0])
        e = _refine_quadric(matrix)
        assert isinstance(e, Ellipsoid)
        assert e.center == Point(0.0, 0.0, 0.0)
        assert sorted(e.radii, reverse=True) == pytest.approx([4.0, 3.0, 2.0])

    def test_cylinder(self):
        matrix = np.diag([1.0, 1.0, 0.0, -1.0])
        c = _refine_quadric(matrix)
        assert isinstance(c, Cylinder)
        assert c.radius == pytest.approx(1.0)
        assert abs(c.axis.z) == pytest.approx(1.0)

    def test_cone(self):
        matrix = np.diag([1.0, 1.0, -1.0, 0.0])
        c = _refine_quadric(matrix)
        assert isinstance(c, Cone)
        assert c.vertex == Point(0.0, 0.0, 0.0)
        assert c.half_angle == pytest.approx(np.pi / 4.0)
        assert abs(c.axis.z) == pytest.approx(1.0)

    def test_plane(self):
        matrix = np.array(
            [
                [0.0, 0.0, 0.0, 0.5],
                [0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0],
                [0.5, 0.0, 0.0, 0.0],
            ]
        )
        p = _refine_quadric(matrix)
        assert isinstance(p, Plane)
        assert p.normal.x == pytest.approx(1.0)
        assert p.point == Point(0.0, 0.0, 0.0)


class TestRoundTrip:
    def test_analyze_then_refine(self):
        basis = BasisQ2(opns=False)
        matrix = np.array([[1.0, 0.0, -1.0], [0.0, 1.0, -2.0], [-1.0, -2.0, 1.0]])
        mv = _coeff_mv(basis, to_coeffs(matrix))
        raw = analyze(mv)
        assert isinstance(raw, Conic)
        specific = refine(raw)
        assert isinstance(specific, Circle)

    def test_geometry_facade_refines(self):
        basis = BasisQ2(opns=False)
        geo = Geometry(basis)
        matrix = np.array([[1.0, 0.0, -1.0], [0.0, 1.0, -2.0], [-1.0, -2.0, 1.0]])
        mv = _coeff_mv(basis, to_coeffs(matrix))
        raw = geo(mv)
        assert isinstance(raw, Conic)
        specific = geo(raw)
        assert isinstance(specific, Circle)
