# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for ``pytanga.geometry.Matrix`` and ``MatrixProvider``."""

from __future__ import annotations

import numpy as np
import pytest

from pytanga.geometry import Direction, Matrix, MatrixProvider, Point


def test_matrix_square_only():  # noqa: ANN201
    with pytest.raises(ValueError):
        Matrix([[1.0, 2.0, 3.0]])


def test_matrix_identity():  # noqa: ANN201
    assert Matrix.identity(3) == Matrix(np.eye(3))
    assert Matrix.identity(4) == Matrix(np.eye(4))


def test_matrix_translation():  # noqa: ANN201
    m = Matrix.translation(1.0, 2.0, 3.0)
    assert m.shape == (4, 4)
    assert m @ Point(0.0, 0.0, 0.0) == Point(1.0, 2.0, 3.0)


def test_matrix_from_R_t():  # noqa: ANN201
    R = Matrix.rotation((0.0, 0.0, 1.0), np.pi / 2)
    m = Matrix.from_R_t(R, (1.0, 2.0, 3.0))
    assert m.shape == (4, 4)
    assert np.allclose(m.data[:3, :3], R.data)
    assert np.allclose(m.data[:3, 3], [1.0, 2.0, 3.0])
    assert m @ Point(1.0, 0.0, 0.0) == Point(1.0, 3.0, 3.0)


def test_matrix_from_R_t_validates():  # noqa: ANN201
    with pytest.raises(ValueError):
        Matrix.from_R_t(Matrix.identity(3), (1.0, 2.0))
    with pytest.raises(ValueError):
        Matrix.from_R_t(Matrix.identity(4), (1.0, 2.0, 3.0))


def test_matrix_rotation_about_x():  # noqa: ANN201
    m = Matrix.rotation((1.0, 0.0, 0.0), np.pi / 2)
    assert m.is_rotation()
    p = m @ Point(0.0, 1.0, 0.0)
    assert np.allclose([p.x, p.y, p.z], [0.0, 0.0, 1.0], atol=1e-9)


def test_matrix_scale_uniform():  # noqa: ANN201
    m = Matrix.scale(0.5)
    assert m @ Point(2.0, 4.0, 6.0) == Point(1.0, 2.0, 3.0)


def test_matrix_from_axes_is_rotation():  # noqa: ANN201
    m = Matrix.from_axes((1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0))
    assert m.is_rotation()
    assert m.det() == pytest.approx(1.0)


def test_matrix_compose():  # noqa: ANN201
    a = Matrix.rotation((0.0, 0.0, 1.0), np.pi)
    c = a @ a
    assert c.is_rotation()
    assert np.allclose(c.data, np.eye(3), atol=1e-9)


def test_matrix_inverse_transpose_det():  # noqa: ANN201
    m = Matrix.rotation((1.0, 0.0, 0.0), 0.7)
    assert (m.T @ m) == Matrix(np.eye(3))
    assert (m.inverse() @ m) == Matrix(np.eye(3))
    assert m.det() == pytest.approx(1.0)


def test_matrix_transform_direction():  # noqa: ANN201
    m = Matrix.rotation((0.0, 0.0, 1.0), np.pi / 2)
    d = m @ Direction(1.0, 0.0, 0.0)
    assert np.allclose([d.x, d.y, d.z], [0.0, 1.0, 0.0], atol=1e-9)


def test_matrix_homogeneous_point():  # noqa: ANN201
    m = Matrix.translation(10.0, 0.0, 0.0)
    assert m @ Point(1.0, 2.0, 3.0) == Point(11.0, 2.0, 3.0)


def test_matrix_to_matrix_returns_numpy():  # noqa: ANN201
    assert isinstance(Matrix.identity(3).to_matrix(), np.ndarray)


def test_matrix_provider_protocol():  # noqa: ANN201
    assert isinstance(Matrix.identity(3), MatrixProvider)
    assert not isinstance("not a matrix", MatrixProvider)
