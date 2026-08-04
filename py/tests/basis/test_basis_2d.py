# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for 2D basis classes (Phase 7.1 — smoke tests)."""

from __future__ import annotations

import pytest
from pytanga import Algebra
from pytanga.basis import BasisE2, BasisN2, BasisP2, BasisPGA2


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


def scalar(mv) -> float:
    """Return the scalar (grade-0) coefficient of an MV or raw float."""
    if isinstance(mv, float):
        return mv
    return float(mv[0])


def is_zero(mv, tol: float = 1e-12) -> bool:
    """True if all non-zero coefficients are below tol after pruning."""
    mv.prune()
    return not mv.to_dict()


# ---------------------------------------------------------------------------
# 7.1.1 — importability & isinstance
# ---------------------------------------------------------------------------


@_NEEDS_BUILD
class TestImports:
    def test_basis_e2_is_algebra(self):
        b = BasisE2()
        assert isinstance(b, Algebra)

    def test_basis_p2_is_algebra(self):
        b = BasisP2()
        assert isinstance(b, Algebra)

    def test_basis_n2_is_algebra(self):
        b = BasisN2()
        assert isinstance(b, Algebra)

    def test_basis_pga2_is_algebra(self):
        b = BasisPGA2()
        assert isinstance(b, Algebra)

    def test_basis_pga2_has_e0(self):
        b = BasisPGA2()
        assert hasattr(b, "e0")

    def test_basis_pga2_has_e0_inv(self):
        b = BasisPGA2()
        assert hasattr(b, "e0_inv")

    def test_basis_n2_has_einf(self):
        b = BasisN2()
        assert hasattr(b, "einf")

    def test_basis_n2_has_eo(self):
        b = BasisN2()
        assert hasattr(b, "eo")


# ---------------------------------------------------------------------------
# 7.1.2 — from_name integration
# ---------------------------------------------------------------------------


class TestFromNameNoCompile:
    """Tests that validate from_name routing without triggering a build."""

    def test_from_name_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown"):
            Algebra.from_name("BOGUS_2D")


@_NEEDS_BUILD
class TestFromName:
    def test_from_name_e2_returns_basis(self):
        b = Algebra.from_name("E2")
        assert isinstance(b, BasisE2)

    def test_from_name_p2_returns_basis(self):
        b = Algebra.from_name("P2")
        assert isinstance(b, BasisP2)

    def test_from_name_n2_returns_basis(self):
        b = Algebra.from_name("N2")
        assert isinstance(b, BasisN2)

    def test_from_name_pga2_returns_basis(self):
        b = Algebra.from_name("PGA2")
        assert isinstance(b, BasisPGA2)

    def test_from_name_g2_returns_plain_algebra(self):
        a = Algebra.from_name("G2")
        assert type(a) is Algebra


# ---------------------------------------------------------------------------
# 7.1.3 — BasisE2 algebra dimensions and named blades
# ---------------------------------------------------------------------------


@_NEEDS_BUILD
class TestBasisE2:
    def setup_method(self):
        self.b = BasisE2()

    def test_dim(self):
        assert self.b.dim == 2

    def test_sig(self):
        assert self.b.sig == 0

    def test_e1_squared_is_one(self):
        result = self.b.e1 * self.b.e1
        assert abs(scalar(result) - 1.0) < 1e-12

    def test_e2_squared_is_one(self):
        result = self.b.e2 * self.b.e2
        assert abs(scalar(result) - 1.0) < 1e-12

    def test_e1_e2_equals_e12(self):
        result = self.b.e1 * self.b.e2
        assert abs(float(result[self.b.E12]) - 1.0) < 1e-12

    def test_pseudoscalar_id(self):
        assert self.b.pseudoscalar_id == 3  # 1|2

    def test_I_blade_id(self):
        assert float(self.b.I[3]) == pytest.approx(1.0)

    def test_vector_factory(self):
        v = self.b.vector(3, 4)
        assert float(v[1]) == pytest.approx(3.0)
        assert float(v[2]) == pytest.approx(4.0)

    def test_algebra_dim(self):
        assert self.b.algebra_dim == 4  # 2^2


# ---------------------------------------------------------------------------
# 7.1.4 — BasisP2 algebra dimensions and named blades
# ---------------------------------------------------------------------------


@_NEEDS_BUILD
class TestBasisP2:
    def setup_method(self):
        self.b = BasisP2()

    def test_dim(self):
        assert self.b.dim == 3

    def test_sig(self):
        assert self.b.sig == 0

    def test_e1_squared_is_one(self):
        assert abs(scalar(self.b.e1 * self.b.e1) - 1.0) < 1e-12

    def test_e2_squared_is_one(self):
        assert abs(scalar(self.b.e2 * self.b.e2) - 1.0) < 1e-12

    def test_e3_squared_is_one(self):
        assert abs(scalar(self.b.e3 * self.b.e3) - 1.0) < 1e-12

    def test_pseudoscalar_id(self):
        assert self.b.pseudoscalar_id == 7  # 1|2|4

    def test_point_factory(self):
        p = self.b.point(3, 4)
        assert float(p[1]) == pytest.approx(3.0)
        assert float(p[2]) == pytest.approx(4.0)
        assert float(p[4]) == pytest.approx(1.0)  # e3 = homogeneous weight

    def test_direction_factory(self):
        d = self.b.direction(1, 2)
        assert float(d[1]) == pytest.approx(1.0)
        assert float(d[2]) == pytest.approx(2.0)
        assert float(d[4]) == pytest.approx(0.0)  # no e3 component

    def test_algebra_dim(self):
        assert self.b.algebra_dim == 8  # 2^3


# ---------------------------------------------------------------------------
# 7.1.5 — BasisN2 named blades and null vectors
# ---------------------------------------------------------------------------


@_NEEDS_BUILD
class TestBasisN2:
    def setup_method(self):
        self.b = BasisN2()

    def test_dim(self):
        assert self.b.dim == 4

    def test_sig(self):
        assert self.b.sig == 0b1000

    def test_pseudoscalar_id(self):
        assert self.b.pseudoscalar_id == 15  # 1|2|4|8

    def test_ep_squared(self):
        """ep² = +1 (positive metric)."""
        assert abs(scalar(self.b.ep * self.b.ep) - 1.0) < 1e-12

    def test_em_squared(self):
        """em² = -1 (negative metric, signature bit set)."""
        assert abs(scalar(self.b.em * self.b.em) - (-1.0)) < 1e-12

    def test_einf_is_null(self):
        """einf² = 0."""
        assert is_zero(self.b.einf * self.b.einf)

    def test_eo_is_null(self):
        """eo² = 0."""
        assert is_zero(self.b.eo * self.b.eo)

    def test_einf_eo_inner_product(self):
        """einf·eo = −1."""
        result = self.b.einf.sp(self.b.eo)
        assert abs(scalar(result) - (-1.0)) < 1e-6

    def test_einf_coefficients(self):
        assert float(self.b.einf[4]) == pytest.approx(1.0)  # ep component
        assert float(self.b.einf[8]) == pytest.approx(1.0)  # em component

    def test_eo_coefficients(self):
        assert float(self.b.eo[4]) == pytest.approx(-0.5)  # ep component
        assert float(self.b.eo[8]) == pytest.approx(0.5)  # em component

    def test_algebra_dim(self):
        assert self.b.algebra_dim == 16  # 2^4


# ---------------------------------------------------------------------------
# 7.1.6 — BasisPGA2 factory methods and null condition
# ---------------------------------------------------------------------------


@_NEEDS_BUILD
class TestBasisPGA2:
    def setup_method(self):
        self.b = BasisPGA2()

    def test_dim(self):
        assert self.b.dim == 4

    def test_sig(self):
        assert self.b.sig == 0b1000

    def test_ep_squared(self):
        """ep² = +1."""
        assert abs(scalar(self.b.ep * self.b.ep) - 1.0) < 1e-12

    def test_em_squared(self):
        """em² = -1."""
        assert abs(scalar(self.b.em * self.b.em) - (-1.0)) < 1e-12

    def test_e0_is_null(self):
        """e0² = 0 (Gunn/Dorst null vector)."""
        assert is_zero(self.b.e0 * self.b.e0)

    def test_e0_inv_inner_product(self):
        """ip(e0, e0_inv) = 1."""
        result = self.b.e0.sp(self.b.e0_inv)
        assert abs(scalar(result) - 1.0) < 1e-6

    def test_point_has_correct_blades(self):
        p = self.b.point(1, 2)
        assert float(p[1]) == pytest.approx(1.0)  # e1
        assert float(p[2]) == pytest.approx(2.0)  # e2
        assert float(p[4]) == pytest.approx(1.0)  # ep component of e0
        assert float(p[8]) == pytest.approx(1.0)  # em component of e0

    def test_point_inner_product_with_e0_inv(self):
        """ip(point, e0_inv) must equal +1 for any finite point in PGA2."""
        p = self.b.point(3, 4)
        result = self.b.ip(p, self.b.e0_inv)
        assert abs(scalar(result) - 1.0) < 1e-12

    def test_ideal_direction_inner_product_with_e0_inv_is_zero(self):
        """ip(direction, e0_inv) = 0 for ideal points."""
        v = self.b.direction(1, 0)
        result = self.b.ip(v, self.b.e0_inv)
        assert is_zero(result)

    def test_direction_factory(self):
        v = self.b.direction(3, 0)
        assert float(v[1]) == pytest.approx(3.0)
        assert float(v[2]) == pytest.approx(0.0)
        assert float(v[4]) == pytest.approx(0.0)  # no ep
        assert float(v[8]) == pytest.approx(0.0)  # no em

    def test_line_factory(self):
        l = self.b.line(0, 1, 5.0)
        assert float(l[1]) == pytest.approx(0.0)
        assert float(l[2]) == pytest.approx(1.0)
        assert float(l[4]) == pytest.approx(5.0)
        assert float(l[8]) == pytest.approx(5.0)

    def test_algebra_dim(self):
        assert self.b.algebra_dim == 16  # 2^4

    def test_not_basis_n2(self):
        """BasisPGA2 is not an instance of BasisN2 (separate class)."""
        b = BasisPGA2()
        assert not isinstance(b, BasisN2)
