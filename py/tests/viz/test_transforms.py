# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the scene-graph transform math (`_transforms.py`)."""

import math

import numpy as np
import pytest

from pytanga.geometry.entities import Direction, Point
from pytanga.geometry.operators import Dilator, GeneralRotor, Motor, Rotor, Translator
from pytanga.viz._transforms import (
    dilator_to_matrix,
    general_rotor_to_matrix,
    motor_to_matrix,
    operator_to_matrix,
    operator_to_trs,
    rotation_matrix,
    rotor_to_matrix,
    scale_matrix,
    to_matrix,
    to_trs,
    to_trs_tuple,
    translation_matrix,
    translator_to_matrix,
)


def _p(x, y, z):
    return np.array([x, y, z, 1.0], dtype=np.float64)


def _compose_trs(position, euler, scale):
    """Re-compose a TRS triple using the same conventions as the module."""
    rx = rotation_matrix((1, 0, 0), euler[0])
    ry = rotation_matrix((0, 1, 0), euler[1])
    rz = rotation_matrix((0, 0, 1), euler[2])
    r = rx @ ry @ rz
    return translation_matrix(*position) @ r @ scale_matrix(*scale)


class TestMatrixPrimitives:
    def test_translation_matrix(self):
        m = translation_matrix(1.0, -2.0, 3.5)
        assert m.shape == (4, 4)
        assert m.dtype == np.float64
        assert m[0, 3] == 1.0
        assert m[1, 3] == -2.0
        assert m[2, 3] == 3.5
        assert m[3, 3] == 1.0
        # bottom row untouched
        assert m[3, 0] == 0.0 and m[3, 1] == 0.0 and m[3, 2] == 0.0

    def test_rotation_matrix_z(self):
        m = rotation_matrix(Direction(0, 0, 1), math.pi / 2)
        result = m @ _p(1, 0, 0)
        assert np.allclose(result, _p(0, 1, 0), atol=1e-12)

    def test_rotation_matrix_zero_axis_is_identity(self):
        m = rotation_matrix(Direction(0, 0, 0), 1.0)
        assert np.allclose(m, np.eye(4))

    def test_scale_matrix_scalar(self):
        m = scale_matrix(2.0)
        assert m[0, 0] == 2.0
        assert m[1, 1] == 2.0
        assert m[2, 2] == 2.0
        assert m[3, 3] == 1.0

    def test_scale_matrix_component(self):
        m = scale_matrix(2.0, 3.0, 4.0)
        assert m[0, 0] == 2.0
        assert m[1, 1] == 3.0
        assert m[2, 2] == 4.0


class TestOperatorMatrix:
    def test_translator_to_matrix(self):
        t = Translator(vector=Direction(1, 2, 3))
        expected = translation_matrix(1, 2, 3)
        assert np.allclose(translator_to_matrix(t), expected)

    def test_rotor_to_matrix(self):
        r = Rotor(angle=math.pi / 2, axis=Direction(0, 0, 1))
        assert np.allclose(
            rotor_to_matrix(r),
            rotation_matrix(Direction(0, 0, 1), math.pi / 2),
        )

    def test_general_rotor_to_matrix(self):
        gr = GeneralRotor(
            angle=math.pi / 2,
            axis=Direction(0, 0, 1),
            origin=Point(1, 0, 0),
        )
        m = general_rotor_to_matrix(gr)
        # Origin is the fixed point of the transform.
        assert np.allclose(m @ _p(1, 0, 0), _p(1, 0, 0), atol=1e-12)
        # A point offset +x from the origin rotates to +y.
        assert np.allclose(m @ _p(2, 0, 0), _p(1, 1, 0), atol=1e-12)

    def test_motor_to_matrix(self):
        motor = Motor(
            rotor=Rotor(angle=math.pi / 2, axis=Direction(0, 0, 1)),
            translator=Translator(vector=Direction(1, 0, 0)),
        )
        m = motor_to_matrix(motor)
        # Rotation first, then translation.
        assert np.allclose(m @ _p(2, 0, 0), _p(1, 2, 0), atol=1e-12)

    def test_dilator_to_matrix(self):
        d = Dilator(factor=2.0, origin=Point(1, 0, 0))
        m = dilator_to_matrix(d)
        # Origin stays fixed.
        assert np.allclose(m @ _p(1, 0, 0), _p(1, 0, 0), atol=1e-12)
        # Offset +x from origin scales by 2, so global (2,0,0) -> (3,0,0).
        assert np.allclose(m @ _p(2, 0, 0), _p(3, 0, 0), atol=1e-12)

    def test_operator_to_matrix_unknown(self):
        with pytest.raises(TypeError, match="Unsupported operator type"):
            operator_to_matrix(object())


class TestOperatorToTrs:
    def test_rotor(self):
        pos, euler, scale = operator_to_trs(
            Rotor(angle=math.pi / 2, axis=Direction(0, 0, 1))
        )
        assert pos == (0.0, 0.0, 0.0)
        assert np.allclose(euler, (0.0, 0.0, math.pi / 2))
        assert scale == (1.0, 1.0, 1.0)

    def test_translator(self):
        pos, euler, scale = operator_to_trs(Translator(vector=Direction(1, 2, 3)))
        assert pos == (1.0, 2.0, 3.0)
        assert euler == (0.0, 0.0, 0.0)
        assert scale == (1.0, 1.0, 1.0)

    def test_motor(self):
        pos, euler, scale = operator_to_trs(
            Motor(
                rotor=Rotor(angle=math.pi / 2, axis=Direction(0, 0, 1)),
                translator=Translator(vector=Direction(1, 0, 0)),
            )
        )
        assert pos == (1.0, 0.0, 0.0)
        assert np.allclose(euler, (0.0, 0.0, math.pi / 2))
        assert scale == (1.0, 1.0, 1.0)

    def test_general_rotor(self):
        pos, euler, scale = operator_to_trs(
            GeneralRotor(
                angle=math.pi / 2,
                axis=Direction(0, 0, 1),
                origin=Point(1, 0, 0),
            )
        )
        # position = (I - R) @ origin = (1, -1, 0)
        assert np.allclose(pos, (1.0, -1.0, 0.0))
        assert np.allclose(euler, (0.0, 0.0, math.pi / 2))
        assert scale == (1.0, 1.0, 1.0)

    def test_dilator(self):
        pos, euler, scale = operator_to_trs(Dilator(factor=2.0, origin=Point(1, 0, 0)))
        # position = (1 - f) * origin = (-1, 0, 0)
        assert np.allclose(pos, (-1.0, 0.0, 0.0))
        assert euler == (0.0, 0.0, 0.0)
        assert scale == (2.0, 2.0, 2.0)


class TestRoundTrip:
    def test_to_trs_roundtrip(self):
        r = rotation_matrix((1.0, 0.5, -0.3), 0.9)
        m = translation_matrix(0.5, -1.0, 2.0) @ r @ scale_matrix(2.0, 1.0, 3.0)
        pos, euler, scale = to_trs(m)
        recomposed = _compose_trs(pos, euler, scale)
        assert np.allclose(recomposed, m, atol=1e-10)

    def test_to_trs_identity(self):
        pos, euler, scale = to_trs(np.eye(4))
        assert pos == (0.0, 0.0, 0.0)
        assert euler == (0.0, 0.0, 0.0)
        assert scale == (1.0, 1.0, 1.0)

    def test_to_trs_rejects_bad_shape(self):
        with pytest.raises(ValueError, match="Expected a"):
            to_trs(np.eye(3))


class TestToMatrixConvenience:
    def test_point(self):
        assert np.allclose(to_matrix(Point(1, 2, 3)), translation_matrix(1, 2, 3))

    def test_direction(self):
        assert np.allclose(
            to_matrix(Direction(4, 5, 6)),
            translation_matrix(4, 5, 6),
        )

    def test_operator_dispatch(self):
        assert np.allclose(
            to_matrix(Translator(vector=Direction(1, 2, 3))),
            translation_matrix(1, 2, 3),
        )

    def test_to_trs_tuple_point(self):
        assert to_trs_tuple(Point(1, 2, 3)) == (
            (1.0, 2.0, 3.0),
            (0.0, 0.0, 0.0),
            (1.0, 1.0, 1.0),
        )

    def test_to_trs_tuple_direction(self):
        assert to_trs_tuple(Direction(1, 0, 0)) == (
            (1.0, 0.0, 0.0),
            (0.0, 0.0, 0.0),
            (1.0, 1.0, 1.0),
        )