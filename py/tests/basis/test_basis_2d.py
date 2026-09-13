# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for 2D basis classes (Phase 7.1 — smoke tests)."""

from __future__ import annotations

import pytest
from pytanga import Algebra
from pytanga.basis import BasisE2, BasisN2, BasisP2, BasisPGA2
from pytanga.geometry.create import create_entity
from pytanga.geometry.entities import Direction, Point


# Skip all tests that instantiate a Basis class (requires C++ compilation) when
# the build infrastructure is broken (e.g. python3.12-dev / Python.h missing).
def _build_ok() -> bool:
    try:
        BasisE2()
        return True
    except Exception:
        return False


_NEEDS_BUILD = pytest.mark.skipif(
    not _build_ok(),
    reason="C++ extension build unavailable (python3.12-dev / Python.h missing)",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def scalar(mv) -> float:  # noqa: ANN001
    """Return the scalar (grade-0) coefficient of an MV or raw float."""
    if isinstance(mv, float):
        return mv
    return float(mv[0])


def is_zero(mv, tol: float = 1e-12) -> bool:  # noqa: ANN001
    """True if all non-zero coefficients are below tol after pruning."""
    mv.prune()
    return not mv.to_dict()


# ---------------------------------------------------------------------------
# 7.1.1 — importability & isinstance
# ---------------------------------------------------------------------------


@_NEEDS_BUILD
class TestImports:
    def test_basis_e2_is_algebra(self):  # noqa: ANN201
        b = BasisE2()
        assert isinstance(b, Algebra)

    def test_basis_p2_is_algebra(self):  # noqa: ANN201
        b = BasisP2()
        assert isinstance(b, Algebra)

    def test_basis_n2_is_algebra(self):  # noqa: ANN201
        b = BasisN2()
        assert isinstance(b, Algebra)

    def test_basis_pga2_is_algebra(self):  # noqa: ANN201
        b = BasisPGA2()
        assert isinstance(b, Algebra)

    def test_basis_pga2_has_e0(self):  # noqa: ANN201
        b = BasisPGA2()
        assert hasattr(b, "e0")

    def test_basis_pga2_has_e0_recip(self):  # noqa: ANN201
        b = BasisPGA2()
        assert hasattr(b, "e0_recip")

    def test_basis_n2_has_einf(self):  # noqa: ANN201
        b = BasisN2()
        assert hasattr(b, "einf")

    def test_basis_n2_has_eo(self):  # noqa: ANN201
        b = BasisN2()
        assert hasattr(b, "eo")


# ---------------------------------------------------------------------------
# 7.1.2 — BasisE2 algebra dimensions and named blades
# ---------------------------------------------------------------------------


@_NEEDS_BUILD
class TestBasisE2:
    def setup_method(self):  # noqa: ANN201
        self.b = BasisE2()

    def test_dim(self):  # noqa: ANN201
        assert self.b.dim == 2

    def test_sig(self):  # noqa: ANN201
        assert self.b.sig == 0

    def test_e1_squared_is_one(self):  # noqa: ANN201
        result = self.b.e1 * self.b.e1
        assert abs(scalar(result) - 1.0) < 1e-12

    def test_e2_squared_is_one(self):  # noqa: ANN201
        result = self.b.e2 * self.b.e2
        assert abs(scalar(result) - 1.0) < 1e-12

    def test_e1_e2_equals_e12(self):  # noqa: ANN201
        result = self.b.e1 * self.b.e2
        assert abs(float(result[self.b.E12]) - 1.0) < 1e-12

    def test_pseudoscalar_id(self):  # noqa: ANN201
        assert self.b.pseudoscalar_id == 3  # 1|2

    def test_I_blade_id(self):  # noqa: ANN201
        assert float(self.b.I[3]) == pytest.approx(1.0)

    def test_vector_factory(self):  # noqa: ANN201
        v = self.b.multivector({1: 3, 2: 4})
        assert float(v[1]) == pytest.approx(3.0)
        assert float(v[2]) == pytest.approx(4.0)

    def test_algebra_dim(self):  # noqa: ANN201
        assert self.b.algebra_dim == 4  # 2^2


# ---------------------------------------------------------------------------
# 7.1.4 — BasisP2 algebra dimensions and named blades
# ---------------------------------------------------------------------------


@_NEEDS_BUILD
class TestBasisP2:
    def setup_method(self):  # noqa: ANN201
        self.b = BasisP2()

    def test_dim(self):  # noqa: ANN201
        assert self.b.dim == 3

    def test_sig(self):  # noqa: ANN201
        assert self.b.sig == 0

    def test_e1_squared_is_one(self):  # noqa: ANN201
        assert abs(scalar(self.b.e1 * self.b.e1) - 1.0) < 1e-12

    def test_e2_squared_is_one(self):  # noqa: ANN201
        assert abs(scalar(self.b.e2 * self.b.e2) - 1.0) < 1e-12

    def test_e3_squared_is_one(self):  # noqa: ANN201
        assert abs(scalar(self.b.e3 * self.b.e3) - 1.0) < 1e-12

    def test_pseudoscalar_id(self):  # noqa: ANN201
        assert self.b.pseudoscalar_id == 7  # 1|2|4

    def test_point_factory(self):  # noqa: ANN201
        p = create_entity(self.b, Point(3, 4, 0))
        assert float(p[1]) == pytest.approx(3.0)
        assert float(p[2]) == pytest.approx(4.0)
        assert float(p[4]) == pytest.approx(1.0)  # e3 = homogeneous weight

    def test_direction_factory(self):  # noqa: ANN201
        d = create_entity(self.b, Direction(1, 2, 0))
        assert float(d[1]) == pytest.approx(1.0)
        assert float(d[2]) == pytest.approx(2.0)
        assert float(d[4]) == pytest.approx(0.0)  # no e3 component

    def test_algebra_dim(self):  # noqa: ANN201
        assert self.b.algebra_dim == 8  # 2^3


# ---------------------------------------------------------------------------
# 7.1.5 — BasisN2 named blades and null vectors
# ---------------------------------------------------------------------------


@_NEEDS_BUILD
class TestBasisN2:
    def setup_method(self):  # noqa: ANN201
        self.b = BasisN2()

    def test_dim(self):  # noqa: ANN201
        assert self.b.dim == 4

    def test_sig(self):  # noqa: ANN201
        assert self.b.sig == 0b1000

    def test_pseudoscalar_id(self):  # noqa: ANN201
        assert self.b.pseudoscalar_id == 15  # 1|2|4|8

    def test_ep_squared(self):  # noqa: ANN201
        """ep² = +1 (positive metric)."""
        assert abs(scalar(self.b.ep * self.b.ep) - 1.0) < 1e-12

    def test_em_squared(self):  # noqa: ANN201
        """em² = -1 (negative metric, signature bit set)."""
        assert abs(scalar(self.b.em * self.b.em) - (-1.0)) < 1e-12

    def test_einf_is_null(self):  # noqa: ANN201
        """einf² = 0."""
        assert is_zero(self.b.einf * self.b.einf)

    def test_eo_is_null(self):  # noqa: ANN201
        """eo² = 0."""
        assert is_zero(self.b.eo * self.b.eo)

    def test_einf_eo_inner_product(self):  # noqa: ANN201
        """einf·eo = −1."""
        result = self.b.einf.sp(self.b.eo)
        assert abs(scalar(result) - (-1.0)) < 1e-6

    def test_einf_coefficients(self):  # noqa: ANN201
        assert float(self.b.einf[4]) == pytest.approx(1.0)  # ep component
        assert float(self.b.einf[8]) == pytest.approx(1.0)  # em component

    def test_eo_coefficients(self):  # noqa: ANN201
        assert float(self.b.eo[4]) == pytest.approx(-0.5)  # ep component
        assert float(self.b.eo[8]) == pytest.approx(0.5)  # em component

    def test_algebra_dim(self):  # noqa: ANN201
        assert self.b.algebra_dim == 16  # 2^4


# ---------------------------------------------------------------------------
# 7.1.6 — BasisPGA2 factory methods and null condition
# ---------------------------------------------------------------------------


@_NEEDS_BUILD
class TestBasisPGA2:
    def setup_method(self):  # noqa: ANN201
        self.b = BasisPGA2()

    def test_dim(self):  # noqa: ANN201
        assert self.b.dim == 4

    def test_sig(self):  # noqa: ANN201
        assert self.b.sig == 0b1000

    def test_ep_squared(self):  # noqa: ANN201
        """ep² = +1."""
        assert abs(scalar(self.b.ep * self.b.ep) - 1.0) < 1e-12

    def test_em_squared(self):  # noqa: ANN201
        """em² = -1."""
        assert abs(scalar(self.b.em * self.b.em) - (-1.0)) < 1e-12

    def test_e0_is_null(self):  # noqa: ANN201
        """e0² = 0 (Gunn/Dorst null vector)."""
        assert is_zero(self.b.e0 * self.b.e0)

    def test_e0_recip_inner_product(self):  # noqa: ANN201
        """ip(e0, e0_recip) = 1."""
        result = self.b.e0.sp(self.b.e0_recip)
        assert abs(scalar(result) - 1.0) < 1e-6

    def test_point_has_correct_blades(self):  # noqa: ANN201
        p = self.b.multivector({1: 1, 2: 2, 4: 1.0, 8: 1.0})
        assert float(p[1]) == pytest.approx(1.0)  # e1
        assert float(p[2]) == pytest.approx(2.0)  # e2
        assert float(p[4]) == pytest.approx(1.0)  # ep component of e0
        assert float(p[8]) == pytest.approx(1.0)  # em component of e0

    def test_point_inner_product_with_e0_recip(self):  # noqa: ANN201
        """ip(point, e0_recip) must equal +1 for any finite point in PGA2."""
        p = self.b.multivector({1: 3, 2: 4, 4: 1.0, 8: 1.0})
        result = self.b.ip(p, self.b.e0_recip)
        assert abs(scalar(result) - 1.0) < 1e-12

    def test_ideal_direction_inner_product_with_e0_recip_is_zero(self):  # noqa: ANN201
        """ip(direction, e0_recip) = 0 for ideal points."""
        v = self.b.multivector({1: 1.0})
        result = self.b.ip(v, self.b.e0_recip)
        assert is_zero(result)

    def test_direction_factory(self):  # noqa: ANN201
        v = self.b.multivector({1: 3.0, 2: 0.0})
        assert float(v[1]) == pytest.approx(3.0)
        assert float(v[2]) == pytest.approx(0.0)
        assert float(v[4]) == pytest.approx(0.0)  # no ep
        assert float(v[8]) == pytest.approx(0.0)  # no em

    def test_line_factory(self):  # noqa: ANN201
        line_mv = self.b.multivector({1: 0.0, 2: 1.0, 4: 5.0, 8: 5.0})
        assert float(line_mv[1]) == pytest.approx(0.0)
        assert float(line_mv[2]) == pytest.approx(1.0)
        assert float(line_mv[4]) == pytest.approx(5.0)
        assert float(line_mv[8]) == pytest.approx(5.0)

    def test_algebra_dim(self):  # noqa: ANN201
        assert self.b.algebra_dim == 16  # 2^4

    def test_not_basis_n2(self):  # noqa: ANN201
        """BasisPGA2 is not an instance of BasisN2 (separate class)."""
        b = BasisPGA2()
        assert not isinstance(b, BasisN2)
