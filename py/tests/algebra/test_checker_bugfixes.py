# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Regression tests for bugs found by the ``ty`` type checker.

Each test pins a bug that previously survived because it sat on an untested
path.  See ``dev/todos/ty-type-hints/01-tooling-baseline.md`` (step 1.5).
"""

import pytest

import pytanga
from pytanga.algebra import to_rotor
from pytanga.blade_mask import BladeMask


@pytest.fixture(scope="module")
def alg():
    return pytanga.Algebra(dim=3, sig=0)


def test_mv_is_versor_returns_bool(alg):
    """``MV.is_versor`` had a duplicated ``@property``.

    Previously ``mv.is_versor`` raised
    ``TypeError: 'property' object is not callable``.
    """
    assert isinstance(alg.multivector({"s": 1.0}).is_versor, bool)


def test_to_rotor_without_plane_raises_value_error():
    """``to_rotor()`` raised ``AttributeError`` with neither plane argument.

    Previously it raised ``AttributeError: 'NoneType' object has no attribute
    'is_grade'``; it must raise a clear ``ValueError`` instead.
    """
    with pytest.raises(ValueError):
        to_rotor(0.5)


def test_ids_from_mv_list_returns_set(alg):
    """``_ids_from_mv_list`` returns a set (matching its annotation)."""
    _alg, ids = BladeMask._ids_from_mv_list([alg.multivector({"e1": 1.0})])
    assert isinstance(ids, set)
