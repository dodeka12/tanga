# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for pytanga.quadric — bases, embedding, coeff maps, build-from-points."""

import numpy as np
import pytest

from pytanga.quadric import (
    BasisQ2,
    BasisQ3,
    conic_from_points,
    conic_from_points_svd,
    embed_point,
    from_coeffs,
    line_from_points,
    quadric_from_points,
    quadric_from_points_svd,
    to_coeffs,
)


def _build_ok() -> bool:
    try:
        BasisQ2()
        return True
    except Exception:
        return False


_NEEDS_BUILD = pytest.mark.skipif(
    not _build_ok(),
    reason="C++ extension build unavailable (python3.12-dev / Python.h missing)",
)


def _coeff_mv(basis, coeffs):
    """Build the grade-1 MV for a coeff tuple (b1…bN order)."""
    return basis.multivector({1 << i: c for i, c in enumerate(coeffs)})


def _homogeneous(point):
    return np.array([*point, 1.0], dtype=float)


def _quadratic_value(matrix, point):
    p = _homogeneous(point)
    return float(p @ matrix @ p)


def _assert_same_up_to_scale(a, b, tol=1e-8):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    if np.dot(a.ravel(), b.ravel()) < 0:
        b = -b
    assert np.allclose(a, b, atol=tol)


# ---------------------------------------------------------------------------
# 1.1 — Bases
# ---------------------------------------------------------------------------


@_NEEDS_BUILD
class TestBases:
    def test_q2_dim_sig(self):
        b = BasisQ2()
        assert b.dim == 6
        assert b.sig == 0

    def test_q3_dim_sig(self):
        b = BasisQ3()
        assert b.dim == 10
        assert b.sig == 0

    def test_q2_named_blades(self):
        b = BasisQ2()
        for name in ("b1", "b2", "b3", "b4", "b5", "b6"):
            v = getattr(b, name)
            assert (v * v).scalar == pytest.approx(1.0)

    def test_q3_named_blades(self):
        b = BasisQ3()
        names = ("b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8", "b9", "b10")
        for name in names:
            v = getattr(b, name)
            assert (v * v).scalar == pytest.approx(1.0)

    def test_q2_pseudoscalar(self):
        b = BasisQ2()
        assert b.pseudoscalar_id == 63  # 1|2|4|8|16|32
        assert b.I[63] == pytest.approx(1.0)

    def test_q3_pseudoscalar(self):
        b = BasisQ3()
        assert b.pseudoscalar_id == 1023  # 2^10 - 1
        assert b.I[1023] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# 1.2 — Mapping round-trips and validation
# ---------------------------------------------------------------------------


@_NEEDS_BUILD
class TestMapping:
    def test_q2_round_trip(self):
        coeffs = (1.0, -2.0, 3.0, 4.0, -5.0, 6.0)
        assert to_coeffs(from_coeffs(coeffs)) == pytest.approx(coeffs)

    def test_q3_round_trip(self):
        coeffs = tuple(float(i) for i in range(1, 11))
        assert to_coeffs(from_coeffs(coeffs)) == pytest.approx(coeffs)

    def test_to_coeffs_accepts_nested_lists(self):
        a = [[1.0, 0.0, 2.0], [0.0, 3.0, 4.0], [2.0, 4.0, 5.0]]
        c = to_coeffs(a)
        s = np.sqrt(2.0) / 2.0
        assert c == pytest.approx((2.0, 4.0, 5.0 * s, 1.0 * s, 3.0 * s, 0.0))

    def test_to_coeffs_rejects_unsupported_size(self):
        with pytest.raises(ValueError):
            to_coeffs([[1.0, 0.0], [0.0, 1.0]])

    def test_to_coeffs_rejects_nonsymmetric(self):
        a = [[1.0, 2.0, 3.0], [2.0, 4.0, 5.0], [9.0, 5.0, 6.0]]
        with pytest.raises(ValueError):
            to_coeffs(a)

    def test_from_coeffs_rejects_wrong_length(self):
        with pytest.raises(ValueError):
            from_coeffs((1.0, 2.0, 3.0))


# ---------------------------------------------------------------------------
# 1.3 — Embedding incidence
# ---------------------------------------------------------------------------


@_NEEDS_BUILD
class TestEmbedding:
    def test_q2_incidence(self):
        b = BasisQ2()
        a = np.array([[2.0, 1.0, 0.5], [1.0, 3.0, -0.5], [0.5, -0.5, 1.0]])
        coeff_mv = _coeff_mv(b, to_coeffs(a))
        for x, y in [(0.0, 0.0), (1.0, 2.0), (-3.0, 1.5), (2.5, -0.5)]:
            lhs = embed_point(b, x, y).sp(coeff_mv)
            rhs = 0.5 * _quadratic_value(a, (x, y))
            assert lhs == pytest.approx(rhs)

    def test_q3_incidence(self):
        b = BasisQ3()
        q = np.array(
            [
                [1.0, 0.5, -0.25, 0.1],
                [0.5, 2.0, 0.75, -0.2],
                [-0.25, 0.75, 3.0, 0.3],
                [0.1, -0.2, 0.3, 4.0],
            ]
        )
        coeff_mv = _coeff_mv(b, to_coeffs(q))
        for x, y, z in [(0.0, 0.0, 0.0), (1.0, 2.0, 3.0), (-1.0, 0.5, 2.5)]:
            lhs = embed_point(b, x, y, z).sp(coeff_mv)
            rhs = 0.5 * _quadratic_value(q, (x, y, z))
            assert lhs == pytest.approx(rhs)


# ---------------------------------------------------------------------------
# 1.4 — Build from points
# ---------------------------------------------------------------------------


@_NEEDS_BUILD
class TestBuildFromPoints:
    def test_conic_dual_matches_svd(self):
        b = BasisQ2()
        points = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (2.0, 2.0), (3.0, 1.0)]
        a_dual = conic_from_points(b, points)
        a_svd = conic_from_points_svd(b, points)
        _assert_same_up_to_scale(a_dual, a_svd)
        for p in points:
            assert _quadratic_value(a_dual, p) == pytest.approx(0.0, abs=1e-8)

    def test_quadric_dual_matches_svd(self):
        b = BasisQ3()
        points = [
            (0.1, -0.3, 0.7),
            (1.1, 0.2, -0.5),
            (-0.4, 1.0, 0.3),
            (0.8, -0.9, 1.2),
            (-1.0, -0.7, 0.6),
            (0.5, 1.3, -0.2),
            (2.0, 0.1, 0.9),
            (-0.6, 0.4, 1.5),
            (1.5, -1.1, -0.8),
        ]
        q_dual = quadric_from_points(b, points)
        q_svd = quadric_from_points_svd(b, points)
        _assert_same_up_to_scale(q_dual, q_svd)
        for p in points:
            assert _quadratic_value(q_dual, p) == pytest.approx(0.0, abs=1e-8)

    def test_line_from_points_contains_both_points(self):
        b = BasisQ2()
        a = (1.0, 2.0)
        c = (-3.0, 0.5)
        line = line_from_points(b, a, c)
        assert (embed_point(b, *a) ^ line).is_zero
        assert (embed_point(b, *c) ^ line).is_zero
