# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for GalgebraBridge — round‑trip and product consistency with galgebra."""

import sys
import os

import numpy as np
import pytest

# galgebra is an optional dependency
galgebra = pytest.importorskip("galgebra")
from galgebra.ga import Ga  # noqa: E402

from pytanga.algebra import GalgebraBridge  # noqa: E402


# ═══════════════════════════════════════════════════════════════════════════
# Orthogonal E3
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def ga_e3():
    return Ga("e1 e2 e3", g=[1, 1, 1])


@pytest.fixture(scope="module")
def bridge_e3(ga_e3):
    return GalgebraBridge(np.diag([1.0, 1.0, 1.0]), ga=ga_e3)


class TestOrthoE3:
    def test_dim_and_sig(self, bridge_e3):
        assert bridge_e3.dim == 3
        assert bridge_e3.is_orthogonal is True
        assert bridge_e3.algebra.sig == 0

    def test_scalar_roundtrip(self, bridge_e3, ga_e3):
        mv_ga = ga_e3.mv(5.0)
        mv_t = bridge_e3.from_galgebra(mv_ga)
        mv_back = bridge_e3.to_galgebra(mv_t)
        assert abs(float(mv_back.obj) - 5.0) < 1e-10

    def test_vector_roundtrip(self, bridge_e3, ga_e3):
        import sympy
        mv_ga = ga_e3.mv([1.5, 2.0, -3.0], "vector")
        mv_t = bridge_e3.from_galgebra(mv_ga)
        mv_back = bridge_e3.to_galgebra(mv_t)
        diff = sympy.expand((mv_back - mv_ga).obj)
        assert diff == 0

    def test_bivector_roundtrip(self, bridge_e3, ga_e3):
        import sympy
        mv_ga = ga_e3.mv([1.0, 2.0, 3.0], "bivector")
        mv_t = bridge_e3.from_galgebra(mv_ga)
        mv_back = bridge_e3.to_galgebra(mv_t)
        diff = sympy.expand((mv_back - mv_ga).obj)
        assert diff == 0

    def test_full_mv_roundtrip(self, bridge_e3, ga_e3):
        import sympy
        coeffs = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
        expr = sum(c * b for c, b in zip(coeffs, ga_e3.blades.flat))
        mv_ga = ga_e3.mv(expr)
        mv_t = bridge_e3.from_galgebra(mv_ga)
        mv_back = bridge_e3.to_galgebra(mv_t)
        diff = sympy.expand((mv_back - mv_ga).obj)
        assert diff == 0

    def test_gp_consistency(self, bridge_e3, ga_e3):
        e1 = ga_e3.mv([1.0, 0.0, 0.0], "vector")
        e2 = ga_e3.mv([0.0, 1.0, 0.0], "vector")
        gp_ga = e1 * e2
        e1_t = bridge_e3.from_galgebra(e1)
        e2_t = bridge_e3.from_galgebra(e2)
        gp_t = e1_t * e2_t
        gp_back = bridge_e3.to_galgebra(gp_t)
        assert (gp_back - gp_ga).obj == 0

    def test_ip_consistency(self, bridge_e3, ga_e3):
        e1 = ga_e3.mv([1.0, 0.0, 0.0], "vector")
        e2 = ga_e3.mv([0.0, 1.0, 0.0], "vector")
        ip_ga = e1 | e2
        e1_t = bridge_e3.from_galgebra(e1)
        e2_t = bridge_e3.from_galgebra(e2)
        ip_t = e1_t | e2_t
        ip_back = bridge_e3.to_galgebra(ip_t)
        assert (ip_back - ip_ga).obj == 0

    def test_op_consistency(self, bridge_e3, ga_e3):
        e1 = ga_e3.mv([1.0, 0.0, 0.0], "vector")
        e2 = ga_e3.mv([0.0, 1.0, 0.0], "vector")
        op_ga = e1 ^ e2
        e1_t = bridge_e3.from_galgebra(e1)
        e2_t = bridge_e3.from_galgebra(e2)
        op_t = e1_t ^ e2_t
        op_back = bridge_e3.to_galgebra(op_t)
        assert (op_back - op_ga).obj == 0

    def test_symbolic_raises(self, bridge_e3, ga_e3):
        # Create a symbolic MV: use 'scalar' with a symbolic name
        mv_ga = ga_e3.mv("sym", "scalar")
        with pytest.raises(ValueError, match="symbolic"):
            bridge_e3.from_galgebra(mv_ga)


# ═══════════════════════════════════════════════════════════════════════════
# Non‑orthogonal 2D
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def ga_nonortho():
    g = [[2.0, 1.0], [1.0, 2.0]]
    return Ga("e1 e2", g=g)


@pytest.fixture(scope="module")
def bridge_nonortho(ga_nonortho):
    return GalgebraBridge(np.array(ga_nonortho.g, dtype=float), ga=ga_nonortho)


class TestNonOrtho:
    def test_not_orthogonal(self, bridge_nonortho):
        assert bridge_nonortho.is_orthogonal is False
        assert bridge_nonortho.dim == 2

    def test_vector_roundtrip(self, bridge_nonortho, ga_nonortho):
        import sympy
        e1 = ga_nonortho.mv([1.0, 0.0], "vector")
        e1_t = bridge_nonortho.from_galgebra(e1)
        e1_back = bridge_nonortho.to_galgebra(e1_t)
        diff = sympy.expand((e1_back - e1).obj)
        assert diff == 0

    def test_gp_consistency(self, bridge_nonortho, ga_nonortho):
        import sympy
        e1 = ga_nonortho.mv([1.0, 0.0], "vector")
        e2 = ga_nonortho.mv([0.0, 1.0], "vector")
        gp_ga = e1 * e2
        e1_t = bridge_nonortho.from_galgebra(e1)
        e2_t = bridge_nonortho.from_galgebra(e2)
        gp_t = e1_t * e2_t
        gp_back = bridge_nonortho.to_galgebra(gp_t)
        diff = sympy.expand((gp_back - gp_ga).obj)
        assert diff == 0 or abs(float(diff)) < 1e-10

    def test_inner_product_matches_metric(self, bridge_nonortho, ga_nonortho):
        import sympy
        e1 = ga_nonortho.mv([1.0, 0.0], "vector")
        e2 = ga_nonortho.mv([0.0, 1.0], "vector")
        ip_ga = e1 | e2
        assert abs(float(ip_ga.obj) - 1.0) < 1e-10
        e1_t = bridge_nonortho.from_galgebra(e1)
        e2_t = bridge_nonortho.from_galgebra(e2)
        ip_t = e1_t | e2_t
        ip_back = bridge_nonortho.to_galgebra(ip_t)
        diff = sympy.expand((ip_back - ip_ga).obj)
        assert diff == 0 or abs(float(diff)) < 1e-10

    def test_to_galgebra_without_ga_raises(self, bridge_nonortho):
        # Create bridge without ga, then try to_galgebra
        b = GalgebraBridge(np.array([[2.0, 1.0], [1.0, 2.0]]))
        from pytanga.algebra import Algebra
        alg = Algebra(dim=2, sig=0)
        mv = alg.multivector({"e1": 1.0})
        with pytest.raises(ValueError, match="requires a galgebra Ga"):
            b.to_galgebra(mv)
