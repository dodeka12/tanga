# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the per-algebra string blade-name cache in ``Algebra._resolve_key_signed``."""

from pytanga.basis import BasisE3


def test_string_key_is_cached() -> None:
    alg = BasisE3()
    first = alg._resolve_key_signed("e12")
    second = alg._resolve_key_signed("e12")
    assert first == (3, 1)
    assert second == (3, 1)
    # One entry, no re-parse on the second call.
    assert alg._blade_name_cache == {"e12": (3, 1)}


def test_reversed_name_caches_sign() -> None:
    alg = BasisE3()
    result = alg._resolve_key_signed("e21")
    assert result == (3, -1)
    assert alg._blade_name_cache["e21"] == (3, -1)


def test_public_access_roundtrip() -> None:
    alg = BasisE3()
    mv = alg.multivector({"e12": 2.0})
    assert mv["e12"] == 2.0
    assert mv["e21"] == -2.0
