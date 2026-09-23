# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the tolerance surfaced on the `Geometry` facade."""

import numpy as np
import pytest

from pytanga.geometry import Geometry
from pytanga.geometry.entities import Cone
from pytanga.quadric import BasisQ3, Quadric3D


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


def _noisy_cone() -> Quadric3D:
    return Quadric3D(np.diag([1.0, 1.0, -1.0, 1e-6]))


@_NEEDS_BUILD
def test_geometry_tol_constructor_refines_noisy_cone() -> None:
    geo = Geometry(BasisQ3(), tol=1e-4)
    assert isinstance(geo.refine(_noisy_cone()), Cone)


@_NEEDS_BUILD
def test_geometry_tol_per_call_override() -> None:
    geo = Geometry(BasisQ3())
    # default tolerance classifies the noisy cone as a hyperboloid -> no entity
    with pytest.raises(ValueError):
        geo.refine(_noisy_cone())
    # a per-call tolerance override wins over the (unset) instance tolerance
    assert isinstance(geo.refine(_noisy_cone(), tol=1e-4), Cone)


@_NEEDS_BUILD
def test_geometry_tol_setter() -> None:
    geo = Geometry(BasisQ3())
    geo.tol = 1e-4
    assert isinstance(geo.refine(_noisy_cone()), Cone)
    geo.tol = None
    with pytest.raises(ValueError):
        geo.refine(_noisy_cone())
