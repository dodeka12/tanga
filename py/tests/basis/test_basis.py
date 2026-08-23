# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for pytanga.basis — predefined basis classes (Phase 9)."""

import pytest
from pytanga import Algebra
from pytanga.basis import BasisE3, BasisN3, BasisP3, BasisPGA3


# Skip all tests that instantiate a Basis class (requires C++ compilation) when
# the build infrastructure is broken (e.g. python3.12-dev / Python.h missing).
def _build_ok() -> bool:
    try:
        BasisE3()
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
    """Return the scalar (grade-0) coefficient of an MV."""
    return mv[0]


def is_zero(mv, tol: float = 1e-12) -> bool:
    """True if all non-zero coefficients are below tol after pruning."""
    mv.prune()
    return not mv.to_dict()


# ---------------------------------------------------------------------------
# 9.1 — importability & isinstance
# ---------------------------------------------------------------------------


@_NEEDS_BUILD
class TestImports:
    def test_basis_e3_is_algebra(self):
        b = BasisE3()
        assert isinstance(b, Algebra)

    def test_basis_p3_is_algebra(self):
        b = BasisP3()
        assert isinstance(b, Algebra)

    def test_basis_n3_is_algebra(self):
        b = BasisN3()
        assert isinstance(b, Algebra)

    def test_basis_pga3_is_algebra(self):
        b = BasisPGA3()
        assert isinstance(b, Algebra)

    def test_basis_pga3_has_no_einf(self):
        """BasisPGA3 does NOT expose einf (that's an N3 name)."""
        b = BasisPGA3()
        assert not hasattr(b, "einf")

    def test_basis_pga3_has_e0(self):
        """BasisPGA3 exposes e0 (the Gunn/Dorst null vector)."""
        b = BasisPGA3()
        assert hasattr(b, "e0")

    def test_basis_pga3_has_e0_recip(self):
        """BasisPGA3 exposes e0_recip (reciprocal of e0)."""
        b = BasisPGA3()
        assert hasattr(b, "e0_recip")


# ---------------------------------------------------------------------------
# 9.2 — BasisE3 algebra dimensions and named blades
# ---------------------------------------------------------------------------


@_NEEDS_BUILD
class TestBasisE3:
    def setup_method(self):
        self.b = BasisE3()

    def test_dim(self):
        assert self.b.dim == 3

    def test_sig(self):
        assert self.b.sig == 0

    def test_e1_squared_is_one(self):
        result = self.b.e1 * self.b.e1
        assert abs(scalar(result) - 1.0) < 1e-12

    def test_e2_squared_is_one(self):
        result = self.b.e2 * self.b.e2
        assert abs(scalar(result) - 1.0) < 1e-12

    def test_e3_squared_is_one(self):
        result = self.b.e3 * self.b.e3
        assert abs(scalar(result) - 1.0) < 1e-12

    def test_pseudoscalar_id(self):
        assert self.b.pseudoscalar_id == 7  # 1|2|4

    def test_I_blade_id(self):
        assert self.b.I[7] == pytest.approx(1.0)

    def test_vector_factory(self):
        v = self.b.multivector({1: 1, 2: 2, 4: 3})
        assert v[1] == pytest.approx(1.0)
        assert v[2] == pytest.approx(2.0)
        assert v[4] == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# 9.4 — BasisP3 algebra dimensions and named blades
# ---------------------------------------------------------------------------


@_NEEDS_BUILD
class TestBasisP3:
    def setup_method(self):
        self.b = BasisP3()

    def test_dim(self):
        assert self.b.dim == 4

    def test_pseudoscalar_id(self):
        assert self.b.pseudoscalar_id == 15  # 1|2|4|8

    def test_point_factory(self):
        p = self.b.multivector({1: 1, 2: 2, 4: 3, 8: 1})
        assert p[1] == pytest.approx(1.0)
        assert p[2] == pytest.approx(2.0)
        assert p[4] == pytest.approx(3.0)
        assert p[8] == pytest.approx(1.0)  # homogeneous coordinate


# ---------------------------------------------------------------------------
# 9.5 — BasisN3 named blades and null vectors
# ---------------------------------------------------------------------------


@_NEEDS_BUILD
class TestBasisN3:
    def setup_method(self):
        self.b = BasisN3()

    def test_dim(self):
        assert self.b.dim == 5

    def test_sig(self):
        assert self.b.sig == 0b10000

    def test_pseudoscalar_id(self):
        assert self.b.pseudoscalar_id == 31  # 1|2|4|8|16

    def test_ep_squared(self):
        """ep² = +1 (positive metric)."""
        result = self.b.ep * self.b.ep
        assert abs(scalar(result) - 1.0) < 1e-12

    def test_em_squared(self):
        """em² = -1 (negative metric, signature bit set)."""
        result = self.b.em * self.b.em
        assert abs(scalar(result) - (-1.0)) < 1e-12

    def test_einf_is_null(self):
        """einf² = 0."""
        result = self.b.einf * self.b.einf
        assert is_zero(result)

    def test_eo_is_null(self):
        """eo² = 0."""
        result = self.b.eo * self.b.eo
        assert is_zero(result)

    def test_einf_coefficients(self):
        assert self.b.einf[8] == pytest.approx(1.0)  # ep component
        assert self.b.einf[16] == pytest.approx(1.0)  # em component

    def test_eo_coefficients(self):
        assert self.b.eo[8] == pytest.approx(-0.5)  # ep component
        assert self.b.eo[16] == pytest.approx(0.5)  # em component


# ---------------------------------------------------------------------------
# 9.6 — BasisPGA3 factory methods and null condition
# ---------------------------------------------------------------------------


@_NEEDS_BUILD
class TestBasisPGA3:
    def setup_method(self):
        self.b = BasisPGA3()

    def test_point_has_correct_blades(self):
        p = self.b.multivector({1: 1, 2: 2, 4: 3, 8: 1, 16: 1})
        assert p[1] == pytest.approx(1.0)
        assert p[2] == pytest.approx(2.0)
        assert p[4] == pytest.approx(3.0)
        # PGA3 point in IPNS: x·e₁ + y·e₂ + z·e₃ + e₀
        # where e₀ = ep + em in the 5D embedding.
        assert p[8] == pytest.approx(1.0)  # ep component of e₀
        assert p[16] == pytest.approx(1.0)  # em component of e₀

    def test_point_inner_product_with_e0_recip(self):
        """ip(point, e0_recip) must equal +1 for any finite point in PGA3."""
        p = self.b.multivector({1: 1, 2: 2, 4: 3, 8: 1, 16: 1})
        result = self.b.ip(p, self.b.e0_recip)
        assert abs(scalar(result) - 1.0) < 1e-12

    def test_ideal_direction_inner_product_with_e0_recip_is_zero(self):
        """ip(direction, e0_recip) = 0 for ideal points."""
        v = self.b.multivector({1: 1})
        result = self.b.ip(v, self.b.e0_recip)
        assert is_zero(result)

    def test_direction_factory(self):
        v = self.b.multivector({1: 3})
        assert v[1] == pytest.approx(3.0)
        assert v[2] == pytest.approx(0.0)
        assert v[4] == pytest.approx(0.0)
