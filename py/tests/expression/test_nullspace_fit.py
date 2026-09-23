# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Expression solver null-space tests for underdetermined (wide) linear systems.

``Expression.lstsq(rhs=None)`` / ``svd()`` must return the correct null space of a
system with more unknowns than equations (e.g. a conic fit is 5×6, a quadric fit
9×10).  Regression guard for the ``full_matrices=True`` fix.
"""

import pytest

from pytanga.algebra import Algebra
from pytanga.blade_mask import BladeMask
from pytanga.expression import Variable


def _build_ok() -> bool:
    try:
        Algebra(6, 0)
        Algebra(10, 0)
        return True
    except Exception:
        return False


_NEEDS_BUILD = pytest.mark.skipif(
    not _build_ok(),
    reason="C++ extension build unavailable (Python.h missing)",
)


@_NEEDS_BUILD
@pytest.mark.parametrize("dim", [6, 10])
def test_wide_system_lstsq_returns_null_vector(dim: int) -> None:
    # v is a grade-1 variable (dim blades); v ^ b1 lives in the (dim-1) bivectors
    # containing b1, so the linear map is (dim-1) x dim (wide) with a 1-D null
    # space spanned by b1 itself.
    alg = Algebra(dim, 0)
    b1 = alg.multivector({1: 1.0})
    v = Variable("V1", BladeMask(alg, grades=[1]))
    sol = (v ^ b1).lstsq()
    assert sol.mag > 0
    assert (sol ^ b1).mag < 1e-8


@_NEEDS_BUILD
def test_wide_system_svd_pads_null_space() -> None:
    alg = Algebra(6, 0)
    b1 = alg.multivector({1: 1.0})
    v = Variable("V1", BladeMask(alg, grades=[1]))
    values, mvs = (v ^ b1).svd()
    assert len(values) == 6
    assert len(mvs) == 6
    assert values[-1] == 0.0
    assert (mvs[-1] ^ b1).mag < 1e-8


@_NEEDS_BUILD
def test_square_system_unchanged() -> None:
    alg = Algebra(3, 0)
    a = alg.multivector({0: 2.0, 1: 1.0})
    v = Variable("V1", BladeMask.full(alg))
    values, mvs = (v * a).svd()
    assert len(values) == len(mvs) == 8
    assert values == sorted(values, reverse=True)
