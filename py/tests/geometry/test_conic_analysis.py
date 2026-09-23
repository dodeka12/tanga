# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for grade-1/dual analysis + refine() to specific entities."""

import functools
import itertools
import math

import numpy as np
import pytest

from pytanga.geometry import (
    Circle,
    Cone,
    Conic,
    Cylinder,
    Direction,
    Ellipse,
    Ellipsoid,
    Geometry,
    Hyperbola,
    LinePair,
    Parabola,
    Plane,
    PlanePair,
    ParallelPlanePair,
    PlaneConic,
    PlaneConicPair,
    Curve,
    Point,
    PointSet,
    Quadric3D,
    Rotor,
    Sphere,
    analyze,
    analyze_entity,
    analyze_operator,
    create,
    refine,
)
from pytanga.quadric import BasisQ2, BasisQ3
from pytanga.quadric._create import create_rotor
from pytanga.quadric._embedding import _embed_point
from pytanga.quadric._mapping import _to_coeffs
from pytanga.quadric._intersection import _intersect_quadrics, _plane_frame


def _coeff_mv(basis, coeffs):  # noqa: ANN001, ANN202
    return basis.multivector({1 << i: c for i, c in enumerate(coeffs)})


def _refine_conic(matrix):  # noqa: ANN001, ANN202
    basis = BasisQ2(opns=False)
    mv = _coeff_mv(basis, _to_coeffs(matrix))
    conic = analyze_entity(mv)
    assert isinstance(conic, Conic)
    return refine(conic)


def _refine_quadric(matrix):  # noqa: ANN001, ANN202
    basis = BasisQ3(opns=False)
    mv = _coeff_mv(basis, _to_coeffs(matrix))
    quadric = analyze_entity(mv)
    assert isinstance(quadric, Quadric3D)
    return refine(quadric)


class TestAnalyzeConic:
    def test_point_opns(self):  # noqa: ANN201
        b = BasisQ2()  # opns=True
        from pytanga.quadric._embedding import _embed_point

        p = analyze_entity(_embed_point(b, 3.0, 4.0))
        assert isinstance(p, Point)
        assert p.x == pytest.approx(3.0)
        assert p.y == pytest.approx(4.0)
        assert p.z == pytest.approx(0.0)

    def test_conic_ipns(self):  # noqa: ANN201
        b = BasisQ2(opns=False)
        matrix = np.array([[1.0, 0.0, -1.0], [0.0, 1.0, -2.0], [-1.0, -2.0, 1.0]])
        conic = analyze_entity(_coeff_mv(b, _to_coeffs(matrix)))
        assert isinstance(conic, Conic)
        assert conic.coeffs == pytest.approx(_to_coeffs(matrix))


class TestRefineConic:
    def test_circle(self):  # noqa: ANN201
        matrix = np.array([[1.0, 0.0, -1.0], [0.0, 1.0, -2.0], [-1.0, -2.0, 1.0]])
        c = _refine_conic(matrix)
        assert isinstance(c, Circle)
        assert c.center.x == pytest.approx(1.0)
        assert c.center.y == pytest.approx(2.0)
        assert c.radius == pytest.approx(2.0)

    def test_ellipse(self):  # noqa: ANN201
        matrix = np.diag([0.25, 1.0 / 9.0, -1.0])
        e = _refine_conic(matrix)
        assert isinstance(e, Ellipse)
        assert e.center == Point(0.0, 0.0, 0.0)
        assert sorted((e.radius_u, e.radius_v)) == pytest.approx([2.0, 3.0])

    def test_ellipse_rotation(self):  # noqa: ANN201
        # x² - xy + y² = 1  ->  ellipse rotated 45° about the origin.
        matrix = np.array([[1.0, -0.5, 0.0], [-0.5, 1.0, 0.0], [0.0, 0.0, -1.0]])
        e = _refine_conic(matrix)
        assert isinstance(e, Ellipse)
        assert e.center == Point(0.0, 0.0, 0.0)
        assert e.dir_u is not None and e.dir_v is not None
        # Principal directions are orthogonal unit vectors at ±45°.
        assert e.dir_u.dot(e.dir_v) == pytest.approx(0.0, abs=1e-9)
        for d in (e.dir_u, e.dir_v):
            assert abs(d.x) == pytest.approx(1.0 / np.sqrt(2.0), abs=1e-6)
            assert abs(d.y) == pytest.approx(1.0 / np.sqrt(2.0), abs=1e-6)
            assert d.z == pytest.approx(0.0)

    def test_hyperbola(self):  # noqa: ANN201
        matrix = np.diag([1.0, -1.0, -1.0])
        h = _refine_conic(matrix)
        assert isinstance(h, Hyperbola)
        assert h.a == pytest.approx(1.0)
        assert h.b == pytest.approx(1.0)
        assert h.center == Point(0.0, 0.0, 0.0)

    def test_parabola(self):  # noqa: ANN201
        matrix = np.array([[0.0, 0.0, -1.0], [0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]])
        p = _refine_conic(matrix)
        assert isinstance(p, Parabola)
        assert p.p == pytest.approx(1.0)
        assert p.vertex.x == pytest.approx(0.0)
        assert p.vertex.y == pytest.approx(0.0)
        assert p.direction.x == pytest.approx(1.0)

    def test_line_pair(self):  # noqa: ANN201
        matrix = np.array([[0.0, 0.5, 0.0], [0.5, 0.0, 0.0], [0.0, 0.0, 0.0]])
        lp = _refine_conic(matrix)
        assert isinstance(lp, LinePair)

    def test_general_hyperboloid_raises(self):  # noqa: ANN201
        matrix = np.diag([1.0, 1.0, -1.0, -1.0])
        with pytest.raises(ValueError):
            _refine_quadric(matrix)


class TestRefineQuadric:
    def test_sphere(self):  # noqa: ANN201
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

    def test_ellipsoid(self):  # noqa: ANN201
        matrix = np.diag([0.25, 1.0 / 9.0, 1.0 / 16.0, -1.0])
        e = _refine_quadric(matrix)
        assert isinstance(e, Ellipsoid)
        assert e.center == Point(0.0, 0.0, 0.0)
        assert sorted(e.radii, reverse=True) == pytest.approx([4.0, 3.0, 2.0])

    def test_cylinder(self):  # noqa: ANN201
        matrix = np.diag([1.0, 1.0, 0.0, -1.0])
        c = _refine_quadric(matrix)
        assert isinstance(c, Cylinder)
        assert c.radius == pytest.approx(1.0)
        assert abs(c.axis.z) == pytest.approx(1.0)

    def test_cone(self):  # noqa: ANN201
        matrix = np.diag([1.0, 1.0, -1.0, 0.0])
        c = _refine_quadric(matrix)
        assert isinstance(c, Cone)
        assert c.vertex == Point(0.0, 0.0, 0.0)
        assert c.half_angle == pytest.approx(np.pi / 4.0)
        assert abs(c.axis.z) == pytest.approx(1.0)

    def test_plane(self):  # noqa: ANN201
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
    def test_analyze_then_refine(self):  # noqa: ANN201
        basis = BasisQ2(opns=False)
        matrix = np.array([[1.0, 0.0, -1.0], [0.0, 1.0, -2.0], [-1.0, -2.0, 1.0]])
        mv = _coeff_mv(basis, _to_coeffs(matrix))
        raw = analyze(mv)
        assert isinstance(raw, Conic)
        specific = refine(raw)
        assert isinstance(specific, Circle)

    def test_geometry_facade_refines(self):  # noqa: ANN201
        basis = BasisQ2(opns=False)
        geo = Geometry(basis)
        matrix = np.array([[1.0, 0.0, -1.0], [0.0, 1.0, -2.0], [-1.0, -2.0, 1.0]])
        mv = _coeff_mv(basis, _to_coeffs(matrix))
        raw = geo(mv)
        assert isinstance(raw, Conic)
        specific = geo(raw)
        assert isinstance(specific, Circle)


def test_quadric_analysis_and_intersection_modules():  # noqa: ANN201
    from pytanga.quadric._analysis import analyze_entity as qanalyze
    from pytanga.quadric._pointset import _two_conic_intersection as qintersect

    basis = BasisQ2(opns=False)
    mv = _coeff_mv(
        basis,
        _to_coeffs(np.array([[1.0, 0.0, -1.0], [0.0, 1.0, -2.0], [-1.0, -2.0, 1.0]])),
    )
    assert isinstance(qanalyze(mv), Conic)

    a = np.diag([1.0, 1.0, -1.0])
    b = np.array([[1.0, 0.0, -1.0], [0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]])
    assert len(qintersect(a, b)) == 2


class TestRotorAnalysis:
    def test_q2_rotor_round_trip(self):  # noqa: ANN201
        basis = BasisQ2(opns=True)
        theta = math.radians(37.0)
        r = create(basis, Rotor(theta, Direction(0, 0, 1)))
        op = analyze_operator(r)
        assert isinstance(op, Rotor)
        assert op.angle == pytest.approx(theta, abs=1e-10)
        assert (op.axis.x, op.axis.y) == pytest.approx((0.0, 0.0), abs=1e-10)

    def test_q3_rotor_round_trip(self):  # noqa: ANN201
        basis = BasisQ3(opns=True)
        theta = math.radians(37.0)
        axis = Direction(0.3, -0.4, 0.5)
        r = create(basis, Rotor(theta, axis))
        op = analyze_operator(r)
        assert isinstance(op, Rotor)
        assert op.angle == pytest.approx(theta, abs=1e-10)
        # axis recovered up to ± sign
        n = np.linalg.norm([axis.x, axis.y, axis.z])
        got = np.array([op.axis.x, op.axis.y, op.axis.z])
        want = np.array([axis.x, axis.y, axis.z]) / n
        assert np.allclose(got, want, atol=1e-10) or np.allclose(got, -want, atol=1e-10)

    def test_analyze_fallback_returns_rotor(self):  # noqa: ANN201
        basis = BasisQ2(opns=True)
        r = create(basis, Rotor(math.radians(20), Direction(0, 0, 1)))
        assert isinstance(analyze(r), Rotor)

    def test_non_versor_raises(self):  # noqa: ANN201
        basis = BasisQ3(opns=False)
        q = _to_coeffs(np.eye(4))
        mv = _coeff_mv(basis, q)  # grade-1 quadric (odd) → not a versor
        with pytest.raises(ValueError):
            analyze_operator(mv)

    def test_scalar_is_identity_rotor(self):  # noqa: ANN201
        for basis in (BasisQ2(opns=True), BasisQ3(opns=True)):
            scalar = basis.multivector({0: 1.0})  # identity versor
            op = analyze_operator(scalar)
            assert isinstance(op, Rotor)
            assert op.angle == pytest.approx(0.0, abs=1e-12)

    def test_rotated_quadric_analyzes(self):  # noqa: ANN201
        """A general-axis rotor on a quadric must still analyze (noise pruned)."""
        basis = BasisQ3(opns=True)
        geo = Geometry(basis)
        points = [
            geo(Point(2.0, 0.0, 0.0)),
            geo(Point(-0.8323, 1.1821, 0.0)),
            geo(Point(-1.3073, -0.9838, 0.0)),
            geo(Point(0.9826, 0.9947, -0.2913)),
            geo(Point(-1.1887, -0.8946, -0.2913)),
            geo(Point(-1.1180, 0.1036, 0.5777)),
            geo(Point(1.4769, 0.5244, 0.3782)),
            geo(Point(-1.3483, 0.6547, 0.3782)),
            geo(Point(0.2925, -0.6426, -0.5998)),
        ]
        base = None
        for p in points:
            base = p if base is None else base ^ p
        rotor = create(basis, Rotor(math.radians(1.0), Direction(0.3, -0.4, 0.5)))
        rotated = rotor.vp(base)
        assert isinstance(analyze_entity(rotated), Quadric3D)
        assert isinstance(analyze(rotated), Quadric3D)


class TestPlanePairAnalysis:
    def test_intersecting_plane_pair(self):  # noqa: ANN201
        # x=0 and y=0 → Q = p1 p2ᵀ + p2 p1ᵀ (rank 2, intersecting).
        p1 = np.array([1.0, 0.0, 0.0, 0.0])
        p2 = np.array([0.0, 1.0, 0.0, 0.0])
        q = Quadric3D(_to_coeffs(np.outer(p1, p2) + np.outer(p2, p1)))
        assert q.kind.value == "plane_pair"
        pair = refine(q)
        assert isinstance(pair, PlanePair)
        normals = {
            (pair.plane1.normal.x, pair.plane1.normal.y, pair.plane1.normal.z),
            (pair.plane2.normal.x, pair.plane2.normal.y, pair.plane2.normal.z),
        }
        assert normals == {(1.0, 0.0, 0.0), (0.0, 1.0, 0.0)}

    def test_parallel_plane_pair(self):  # noqa: ANN201
        # x=1 and x=-1 → x² − 1 = 0 (rank 2, parallel).
        p3 = np.array([1.0, 0.0, 0.0, -1.0])
        p4 = np.array([1.0, 0.0, 0.0, 1.0])
        q = Quadric3D(_to_coeffs(np.outer(p3, p4) + np.outer(p4, p3)))
        assert q.kind.value == "parallel_plane_pair"
        pair = refine(q)
        assert isinstance(pair, ParallelPlanePair)
        xs = {round(pair.plane1.point.x, 6), round(pair.plane2.point.x, 6)}
        assert xs == {1.0, -1.0}

    def test_double_plane(self):  # noqa: ANN201
        # x=0 doubled → x² = 0 (rank 1) → a single plane.
        p5 = np.array([1.0, 0.0, 0.0, 0.0])
        q = Quadric3D(_to_coeffs(np.outer(p5, p5)))
        assert q.kind.value == "plane"

    def test_plane_pair_round_trip(self):  # noqa: ANN201
        # Entity → MV → analyze → refine round-trip (intersecting planes).
        basis = BasisQ3(opns=True)
        pair = PlanePair(
            Plane(Point(0, 0, 0), Direction(1, 0, 0)),
            Plane(Point(0, 0, 0), Direction(0, 1, 0)),
        )
        quadric = analyze_entity(create(basis, pair))
        assert isinstance(quadric, Quadric3D)
        refined = refine(quadric)
        assert isinstance(refined, PlanePair)

    def test_parallel_plane_pair_round_trip(self):  # noqa: ANN201
        # Entity → MV → analyze → refine round-trip (parallel planes).
        basis = BasisQ3(opns=True)
        pair = ParallelPlanePair(
            Plane(Point(1, 0, 0), Direction(1, 0, 0)),
            Plane(Point(-1, 0, 0), Direction(1, 0, 0)),
        )
        quadric = analyze_entity(create(basis, pair))
        assert isinstance(quadric, Quadric3D)
        refined = refine(quadric)
        assert isinstance(refined, ParallelPlanePair)
        xs = {round(refined.plane1.point.x, 6), round(refined.plane2.point.x, 6)}
        assert xs == {1.0, -1.0}


def _body_diagonal_dirs(result) -> list[tuple[float, float, float]]:  # noqa: ANN001
    """Map each member conic's (line) directions back to 3D via the plane frame."""
    dirs: list[tuple[float, float, float]] = []
    for pc in (result.conic1, result.conic2):
        pair = refine(pc.conic)
        n = np.array([pc.plane.normal.x, pc.plane.normal.y, pc.plane.normal.z])
        u, v = _plane_frame(n)
        for line in (pair.line1, pair.line2):
            d = line.direction.x * u + line.direction.y * v
            d = d / np.linalg.norm(d)
            dirs.append(tuple(round(float(x), 6) for x in d))
    return dirs


class TestQuadricIntersection:
    def test_intersect_cube_plane_pairs(self):  # noqa: ANN201
        # x²−y²=0 and y²−z²=0 → the four cube body diagonals.
        Q1 = np.diag([1.0, -1.0, 0.0, 0.0])
        Q2 = np.diag([0.0, 1.0, -1.0, 0.0])
        result = _intersect_quadrics(Q1, Q2)
        assert isinstance(result, PlaneConicPair)
        dirs = _body_diagonal_dirs(result)
        assert len(dirs) == 4
        for d in dirs:
            # body diagonals have |x| == |y| == |z|
            assert abs(abs(d[0]) - abs(d[1])) < 1e-5
            assert abs(abs(d[1]) - abs(d[2])) < 1e-5

    def test_intersect_two_planes(self):  # noqa: ANN201
        # x=0 and y=0 → the z-axis (a single line).
        Q1 = np.diag([1.0, 0.0, 0.0, 0.0])
        Q2 = np.diag([0.0, 1.0, 0.0, 0.0])
        result = _intersect_quadrics(Q1, Q2)
        assert isinstance(result, PlaneConicPair)
        for pc in (result.conic1, result.conic2):
            assert pc.conic.kind.value == "line"

    def test_intersect_two_spheres(self):  # noqa: ANN201
        # Two radius-2 spheres 2 apart → a circle in the plane x=1.
        Q1 = np.diag([1.0, 1.0, 1.0, -4.0])
        Q2 = np.array(
            [[1.0, 0, 0, -2.0], [0, 1.0, 0, 0], [0, 0, 1.0, 0], [-2.0, 0, 0, 0.0]]
        )
        result = _intersect_quadrics(Q1, Q2)
        assert isinstance(result, PlaneConicPair)
        assert result.conic1.conic.kind.value == "circle"
        assert abs(result.conic1.plane.normal.x) == pytest.approx(1.0)

    def test_intersect_hard_case_raises(self):  # noqa: ANN201
        # Nested (disjoint) spheres → no real degenerate member.
        Q1 = np.diag([1.0, 1.0, 1.0, -1.0])
        Q2 = np.diag([1.0, 1.0, 1.0, -4.0])
        with pytest.raises(NotImplementedError):
            _intersect_quadrics(Q1, Q2)

    def test_intersect_cone_member(self):  # noqa: ANN201
        # A generic pencil has real rank-3 cone members → sampled curve.
        rng = np.random.default_rng(0)
        Q1 = rng.normal(size=(4, 4))
        Q1 = Q1 + Q1.T
        Q2 = rng.normal(size=(4, 4))
        Q2 = Q2 + Q2.T
        result = _intersect_quadrics(Q1, Q2)
        assert isinstance(result, Curve)
        points = [p for path in result.paths for p in path]
        assert len(points) > 0
        for p in points:
            xh = np.array([p.x, p.y, p.z, 1.0])
            assert abs(float(xh @ Q1 @ xh)) < 1e-6
            assert abs(float(xh @ Q2 @ xh)) < 1e-6

    def test_intersect_sphere_plane_is_conic(self):  # noqa: ANN201
        # Sphere ∩ plane → a planar circle (exact conic), not a sampled curve.
        Q1 = np.diag([1.0, 1.0, 1.0, -1.0])
        Q2 = np.diag([1.0, 0.0, 0.0, 0.0])
        result = _intersect_quadrics(Q1, Q2)
        assert isinstance(result, PlaneConicPair)
        assert result.conic1.conic.kind.value == "circle"

    def test_analyze_ipns_grade2_intersection(self):  # noqa: ANN201
        # The IPNS grade-2 blade (x²−y²) ∧ (y²−z²) → the four body diagonals.
        basis = BasisQ3(opns=False)
        Q1 = np.diag([1.0, -1.0, 0.0, 0.0])
        Q2 = np.diag([0.0, 1.0, -1.0, 0.0])
        blade = _coeff_mv(basis, _to_coeffs(Q1)) ^ _coeff_mv(basis, _to_coeffs(Q2))
        result = analyze_entity(blade)
        assert isinstance(result, PlaneConicPair)
        dirs = _body_diagonal_dirs(result)
        assert len(dirs) == 4
        for d in dirs:
            assert abs(abs(d[0]) - abs(d[1])) < 1e-5
            assert abs(abs(d[1]) - abs(d[2])) < 1e-5

    def test_analyze_combined_ipns_grade2(self):  # noqa: ANN201
        basis = BasisQ3(opns=False)
        Q1 = np.diag([1.0, -1.0, 0.0, 0.0])
        Q2 = np.diag([0.0, 1.0, -1.0, 0.0])
        blade = _coeff_mv(basis, _to_coeffs(Q1)) ^ _coeff_mv(basis, _to_coeffs(Q2))
        assert isinstance(analyze(blade), PlaneConicPair)

    def test_analyze_ipns_grade3_point_tuple(self):  # noqa: ANN201
        # The IPNS grade-3 blade (x²−y²) ∧ (y²−z²) ∧ (z²−1) is the net of the
        # three quadrics; dualizing it yields the OPNS grade-7 join whose eight
        # base points are the cube vertices (±1, ±1, ±1).
        basis = BasisQ3(opns=False)
        Q1 = np.diag([1.0, -1.0, 0.0, 0.0])
        Q2 = np.diag([0.0, 1.0, -1.0, 0.0])
        Q3 = np.diag([0.0, 0.0, 1.0, -1.0])
        blade = (
            _coeff_mv(basis, _to_coeffs(Q1))
            ^ _coeff_mv(basis, _to_coeffs(Q2))
            ^ _coeff_mv(basis, _to_coeffs(Q3))
        )
        result = analyze_entity(blade)
        assert isinstance(result, PointSet)
        assert len(result) == 8
        pts = {tuple(round(c) for c in (p.x, p.y, p.z)) for p in result}
        assert pts == {
            (sx, sy, sz) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)
        }

    def test_analyze_opns_grade8_join(self):  # noqa: ANN201
        # The OPNS join of the cube's 9 points is grade 8 → the degenerate
        # quadric intersection (the four body diagonals), via the central
        # ``analyze_entity`` (dual → grade-2 pencil → PlaneConicPair).
        basis = BasisQ3(opns=True)
        points = [np.array(c, float) for c in itertools.product((-1.0, 1.0), repeat=3)]
        points.append(np.array([0.0, 0.0, 0.0]))
        embs = [_embed_point(basis, p[0], p[1], p[2]) for p in points]
        blade = functools.reduce(lambda a, c: a.join(c), embs)
        result = analyze_entity(blade)
        assert isinstance(result, PlaneConicPair)
        dirs = _body_diagonal_dirs(result)
        assert len(dirs) == 4
        for d in dirs:
            assert abs(abs(d[0]) - abs(d[1])) < 1e-5
            assert abs(abs(d[1]) - abs(d[2])) < 1e-5

    def test_analyze_opns_grade8_rotated_join(self):  # noqa: ANN201
        # Rotating the cube about a non-standard axis still resolves to a plane
        # pair (the pencil's rank-2 members via the cubic fallback), not the
        # "cone with apex at the origin" error.
        basis = BasisQ3(opns=True)
        points = [np.array(c, float) for c in itertools.product((-1.0, 1.0), repeat=3)]
        points.append(np.array([0.0, 0.0, 0.0]))
        embs = [_embed_point(basis, p[0], p[1], p[2]) for p in points]
        blade = functools.reduce(lambda a, c: a.join(c), embs)
        rotor = create_rotor(basis, math.radians(40.0), Direction(0.6, 0.8, 0.0))
        result = analyze_entity(rotor.vp(blade))
        assert isinstance(result, PlaneConicPair)
        assert len(_body_diagonal_dirs(result)) == 4

    def test_analyze_opns_grade8_moved_center(self):  # noqa: ANN201
        # Moving the cube's centre keeps the 9 points degenerate (rank 8): the
        # pencil's degenerate members are now cylinders/cone (through the origin),
        # and the intersection is a sampled quartic curve, not a plane pair.
        basis = BasisQ3(opns=True)
        corners = [np.array(c, float) for c in itertools.product((-0.5, 0.5), repeat=3)]
        points = corners + [np.array([0.2, 0.1, 0.05])]
        embs = [_embed_point(basis, p[0], p[1], p[2]) for p in points]
        blade = functools.reduce(lambda a, c: a.join(c), embs)
        result = analyze_entity(blade)
        assert isinstance(result, Curve)
        assert any(len(path) > 0 for path in result.paths)
