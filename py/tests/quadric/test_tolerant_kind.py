# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for tolerance-aware conic/quadric classification via ``refine_*``."""

import numpy as np
import pytest

from pytanga.geometry.entities import Cone
from pytanga.quadric import BasisQ3, EQuadricKind, Quadric3D


def _build_ok() -> bool:
    try:
        BasisQ3()
        return True
    except Exception:
        return False


_NEEDS_BUILD = pytest.mark.skipif(
    not _build_ok(),
    reason="C++ extension build unavailable (Python.h missing)",
)


def _noisy_cone(eps: float) -> Quadric3D:
    # diag(1, 1, -1, eps): a right circular cone (x^2 + y^2 - z^2 = 0) with a tiny
    # perturbation of the homogeneous constant, turning it into a rank-4 hyperboloid.
    return Quadric3D(np.diag([1.0, 1.0, -1.0, eps]))


@_NEEDS_BUILD
def test_exact_cone_refines_to_cone_at_default_tolerance() -> None:
    q = _noisy_cone(0.0)
    assert q.kind is EQuadricKind.cone
    assert q.rank == 3
    assert isinstance(q.refine(), Cone)


@_NEEDS_BUILD
def test_noisy_cone_kind_is_hyperboloid_by_default() -> None:
    q = _noisy_cone(1e-6)
    assert q.rank == 4
    assert q.kind in (EQuadricKind.hyperboloid_1s, EQuadricKind.hyperboloid_2s)


@_NEEDS_BUILD
def test_noisy_cone_refines_to_cone_within_tolerance() -> None:
    q = _noisy_cone(1e-6)
    entity = q.refine(tol=1e-4)
    assert isinstance(entity, Cone)
