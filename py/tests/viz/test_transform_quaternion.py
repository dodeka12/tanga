# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the quaternion ``Transform`` and ``Point``/``Direction`` operators."""

import math

import numpy as np
import pytest

from pytanga.geometry.entities import Direction, Point
from pytanga.geometry.transforms import (
    matrix_to_quat,
    quat_from_axis_angle,
    quat_from_vectors,
    quat_mul,
    quat_to_matrix,
)
from pytanga.geometry.transform import Transform


class TestQuaternionHelpers:
    def test_axis_angle_rotates_vector(self) -> None:
        q = quat_from_axis_angle(Direction(0, 0, 1), math.pi / 2)
        m = quat_to_matrix(q)
        v = np.array([1.0, 0.0, 0.0, 1.0])
        assert np.allclose(m @ v, [0.0, 1.0, 0.0, 1.0], atol=1e-12)

    def test_matrix_to_quat_roundtrip(self) -> None:
        q = quat_from_axis_angle(Direction(1, 2, 3), 0.7)
        m = quat_to_matrix(q)
        q2 = matrix_to_quat(m)
        assert np.allclose(quat_to_matrix(q2), m, atol=1e-10)

    def test_quat_mul_matches_matrix_product(self) -> None:
        qa = quat_from_axis_angle(Direction(0, 0, 1), math.pi / 4)
        qb = quat_from_axis_angle(Direction(1, 0, 0), math.pi / 6)
        qc = quat_mul(qa, qb)
        mc = quat_to_matrix(qa) @ quat_to_matrix(qb)
        assert np.allclose(quat_to_matrix(qc), mc, atol=1e-10)

    def test_quat_from_vectors_rotates_a_onto_b(self) -> None:
        q = quat_from_vectors(Direction(0, 0, 1), Direction(1, 0, 0))
        m = quat_to_matrix(q)
        v = np.array([0.0, 0.0, 1.0, 1.0])
        assert np.allclose(m @ v, [1.0, 0.0, 0.0, 1.0], atol=1e-10)


class TestTransformQuaternion:
    def test_default_rotation_is_identity_quaternion(self) -> None:
        assert Transform().rotation == (0.0, 0.0, 0.0, 1.0)

    def test_euler_input_converts_to_quaternion(self) -> None:
        t = Transform(rotation=(0.0, 0.0, math.pi / 2))
        half = math.pi / 4
        assert t.rotation == pytest.approx(
            (0.0, 0.0, math.sin(half), math.cos(half))
        )

    def test_matrix_set_matrix_roundtrip(self) -> None:
        t = Transform(
            position=(1.0, 2.0, 3.0),
            rotation=(0.0, 0.0, math.pi / 3),
            scale=(2.0, 1.0, 3.0),
        )
        m = t.matrix()
        t2 = Transform().set_matrix(m)
        assert np.allclose(t2.matrix(), m, atol=1e-10)

    def test_to_dict_rotation_has_four_elements(self) -> None:
        d = Transform().to_dict()
        assert len(d["rotation"]) == 4
        assert d["rotation"] == [0.0, 0.0, 0.0, 1.0]


class TestTransformOperators:
    def test_matmul_point(self) -> None:
        t = Transform(position=(1.0, 0.0, 0.0))
        assert t @ Point(1.0, 2.0, 3.0) == Point(2.0, 2.0, 3.0)

    def test_matmul_direction_has_no_translation(self) -> None:
        t = Transform(position=(5.0, 5.0, 5.0), rotation=(0.0, 0.0, math.pi / 2))
        d = t @ Direction(1.0, 0.0, 0.0)
        assert (d.x, d.y, d.z) == pytest.approx((0.0, 1.0, 0.0))

    def test_matmul_applies_scale(self) -> None:
        t = Transform(scale=(2.0, 2.0, 2.0))
        assert t @ Point(1.0, 1.0, 1.0) == Point(2.0, 2.0, 2.0)

    def test_rmatmul_point(self) -> None:
        t = Transform(position=(0.0, 2.0, 0.0))
        assert Point(1.0, 1.0, 1.0) @ t == Point(1.0, 3.0, 1.0)

    def test_mul_and_rmul_aliases(self) -> None:
        t = Transform(position=(1.0, 0.0, 0.0))
        assert t * Point(0.0, 0.0, 0.0) == Point(1.0, 0.0, 0.0)
        assert Point(0.0, 0.0, 0.0) * t == Point(1.0, 0.0, 0.0)

    def test_direction_rmatmul(self) -> None:
        t = Transform(rotation=(0.0, 0.0, math.pi / 2))
        d = Direction(1.0, 0.0, 0.0) @ t
        assert (d.x, d.y, d.z) == pytest.approx((0.0, 1.0, 0.0))

    def test_unsupported_operand_raises(self) -> None:
        t = Transform()
        with pytest.raises(TypeError):
            t @ 5
        with pytest.raises(TypeError):
            5 @ t
