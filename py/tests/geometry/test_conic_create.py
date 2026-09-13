# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for creation (entities → quadric-space MV)."""

import math

import numpy as np
import pytest

from pytanga.basis.e3 import BasisE3
from pytanga.geometry import (
    Circle,
    Conic,
    Direction,
    Ellipsoid,
    Point,
    Quadric3D,
    Rotor,
    analyze,
    create,
    refine,
)
from pytanga.quadric import BasisQ2, BasisQ3, to_coeffs


def _coeff_mv(basis, coeffs):
    return basis.multivector({1 << i: c for i, c in enumerate(coeffs)})


def _rotation_matrix(theta, axis):
    a = np.array([axis.x, axis.y, axis.z], dtype=float)
    a = a / np.linalg.norm(a)
    k = np.array([[0.0, -a[2], a[1]], [a[2], 0.0, -a[0]], [-a[1], a[0], 0.0]])
    return np.eye(3) + math.sin(theta) * k + (1.0 - math.cos(theta)) * (k @ k)


def _rotate(x, theta, axis):
    return _rotation_matrix(theta, axis) @ np.asarray(x, dtype=float)


def _circle_matrix():
    return np.array([[1.0, 0.0, -1.0], [0.0, 1.0, -2.0], [-1.0, -2.0, 1.0]])


class TestConicCreate:
    def test_conic_round_trip_ipns(self):
        b = BasisQ2(opns=False)
        mv = _coeff_mv(b, to_coeffs(_circle_matrix()))
        raw = analyze(mv)
        assert isinstance(raw, Conic)
        assert (mv - create(b, raw)).is_zero

    def test_conic_round_trip_opns(self):
        b = BasisQ2(opns=True)
        coeffs = to_coeffs(_circle_matrix())
        mv = _coeff_mv(b, coeffs).undual()  # grade-5 OPNS conic
        raw = analyze(mv)
        assert isinstance(raw, Conic)
        # round-trip is exact up to a global scale/sign
        created = create(b, raw)
        assert (mv + created).is_zero or (mv - created).is_zero

    def test_circle_round_trip(self):
        b = BasisQ2(opns=False)
        circle = Circle(Point(1.0, 2.0, 0.0), 2.0)
        mv = create(b, circle)
        assert isinstance(refine(analyze(mv)), Circle)


class TestQuadricCreate:
    def test_quadric_round_trip_ipns(self):
        b = BasisQ3(opns=False)
        coeffs = tuple(float(i) for i in range(1, 11))
        mv = _coeff_mv(b, coeffs)
        raw = analyze(mv)
        assert isinstance(raw, Quadric3D)
        assert (mv - create(b, raw)).is_zero

    def test_ellipsoid_round_trip(self):
        b = BasisQ3(opns=False)
        ellipsoid = Ellipsoid(Point(1.0, 2.0, 3.0), (2.0, 3.0, 4.0))
        mv = create(b, ellipsoid)
        raw = analyze(mv)
        assert isinstance(raw, Quadric3D)
        refined = refine(raw)
        assert isinstance(refined, Ellipsoid)
        assert refined.center.x == pytest.approx(1.0)
        assert refined.center.y == pytest.approx(2.0)
        assert refined.center.z == pytest.approx(3.0)
        assert sorted(refined.radii, reverse=True) == pytest.approx([4.0, 3.0, 2.0])


class TestRejectUnsupported:
    def test_conic_not_supported_in_e3(self):
        with pytest.raises(TypeError):
            create(BasisE3(), Conic((1.0, 2.0, 3.0, 4.0, 5.0, 6.0)))

    def test_quadric_not_supported_in_q2(self):
        with pytest.raises(TypeError):
            create(BasisQ2(), Quadric3D(tuple(float(i) for i in range(1, 11))))


class TestConicRotor:
    def test_rotor_grades_and_norm(self):
        r = create(BasisQ2(opns=True), Rotor(math.radians(30), Direction(0, 0, 1)))
        assert set(r.grades) == {0, 2, 4}
        assert r.norm2() == pytest.approx(1.0)

    def test_rotor_rotates_conic(self):
        b = BasisQ2(opns=True)
        theta = math.radians(45)
        r = create(b, Rotor(theta, Direction(0, 0, 1)))

        amat = np.diag([0.25, 1.0, -1.0])
        a = create(b, Conic(to_coeffs(amat)))
        bmat = analyze(r.vp(a)).matrix

        rot = np.array(
            [[math.cos(theta), -math.sin(theta)], [math.sin(theta), math.cos(theta)]]
        )
        rh = np.eye(3)
        rh[:2, :2] = rot
        expected = rh @ amat @ rh.T
        scale = bmat[2, 2] / expected[2, 2]
        assert np.allclose(bmat, expected * scale, atol=1e-6)

    def test_rotor_q3_grades_and_norm(self):
        r = create(
            BasisQ3(opns=True), Rotor(math.radians(30), Direction(0.3, -0.4, 0.5))
        )
        assert set(r.grades) == {0, 2, 4, 6}
        assert r.norm2() == pytest.approx(1.0)

    def test_rotor_q3_rotates_point(self):
        from pytanga.quadric._embedding import embed_point

        b = BasisQ3(opns=True)
        theta = math.radians(37.0)
        axis = Direction(0.3, -0.4, 0.5)
        r = create(b, Rotor(theta, axis))

        x = np.array([0.7, -0.4, 0.9])
        rotated = r * embed_point(b, *x) * r.rev()
        expected = embed_point(b, *_rotate(x, theta, axis))
        assert (rotated - expected).norm2() == pytest.approx(0.0, abs=1e-10)

    def test_rotor_q3_rotates_quadric(self):
        from pytanga.quadric._mapping import from_coeffs

        b = BasisQ3(opns=True)
        theta = math.radians(37.0)
        axis = Direction(0.3, -0.4, 0.5)
        r = create(b, Rotor(theta, axis))

        q = np.array(
            [
                [2.0, 0.5, 0.3, 0.1],
                [0.5, 3.0, -0.2, 0.4],
                [0.3, -0.2, 1.5, -0.3],
                [0.1, 0.4, -0.3, -1.0],
            ]
        )
        a = b.multivector({1 << i: c for i, c in enumerate(to_coeffs(q))})
        rotated = from_coeffs([float((r * a * r.rev())[1 << i]) for i in range(10)])

        r4 = np.eye(4)
        r4[:3, :3] = _rotation_matrix(theta, axis)
        assert np.allclose(rotated, r4 @ q @ r4.T, atol=1e-10)

    def test_quadric_create_module(self):
        from pytanga.quadric._create import create_entity as qcreate_entity
        from pytanga.quadric._create import create_rotor as qcreate_rotor

        r = qcreate_rotor(BasisQ2(opns=True), 0.5, Direction(0, 0, 1))
        assert set(r.grades) == {0, 2, 4}
        assert r.norm2() == pytest.approx(1.0)

        conic = qcreate_entity(BasisQ2(opns=True), Conic(to_coeffs(_circle_matrix())))
        assert set(conic.grades) == {5}

        quad = qcreate_entity(
            BasisQ3(opns=True), Quadric3D(tuple(float(i) for i in range(1, 11)))
        )
        assert set(quad.grades) == {9}
