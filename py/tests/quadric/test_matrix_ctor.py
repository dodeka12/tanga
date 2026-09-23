# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the matrix-accepting ``Conic`` / ``Quadric3D`` constructors and ``to_matrix()``."""

import numpy as np
import pytest

from pytanga.geometry import Matrix
from pytanga.quadric import Conic, Quadric3D


def test_conic_from_coeff_vector() -> None:
    coeffs = Conic(np.diag([1.0, 1.0, -1.0])).coeffs
    c = Conic(coeffs)
    assert c.coeffs == coeffs
    assert c.kind.value == "circle"


def test_conic_from_ndarray_matrix() -> None:
    m = np.diag([1.0, 1.0, -1.0])
    c = Conic(m)
    assert c.kind.value == "circle"
    assert np.allclose(c.to_matrix(), m)


def test_conic_from_pytanga_matrix() -> None:
    m = np.diag([1.0, 1.0, -1.0])
    assert Conic(Matrix(m)).coeffs == Conic(m).coeffs


def test_conic_rejects_wrong_matrix_shape() -> None:
    with pytest.raises(ValueError):
        Conic(np.eye(4))


def test_quadric_from_coeff_vector() -> None:
    coeffs = Quadric3D(np.diag([1.0, 1.0, 1.0, -1.0])).coeffs
    q = Quadric3D(coeffs)
    assert q.coeffs == coeffs
    assert q.kind.value == "sphere"


def test_quadric_from_ndarray_matrix() -> None:
    m = np.diag([1.0, 1.0, 1.0, -1.0])
    q = Quadric3D(m)
    assert q.kind.value == "sphere"
    assert np.allclose(q.to_matrix(), m)


def test_quadric_from_pytanga_matrix() -> None:
    m = np.diag([1.0, 1.0, 1.0, -4.0])
    q = Quadric3D(Matrix(m))
    assert np.allclose(q.to_matrix(), m)


def test_quadric_rejects_wrong_matrix_shape() -> None:
    with pytest.raises(ValueError):
        Quadric3D(np.eye(3))
