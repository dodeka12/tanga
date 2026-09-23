# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the Q2→Q3 cone lift (``CONE_BLADE_MAP``, ``BasisQ3(c)``)."""

import numpy as np
import pytest

from pytanga.quadric import BasisQ2, BasisQ3, Conic, Quadric3D
from pytanga.quadric._basis import CONE_BLADE_MAP


def _build_ok() -> bool:
    try:
        BasisQ2()
        BasisQ3()
        return True
    except Exception:
        return False


_NEEDS_BUILD = pytest.mark.skipif(
    not _build_ok(),
    reason="C++ extension build unavailable (Python.h missing)",
)


def _quad_value(matrix: np.ndarray, point: tuple[float, ...]) -> float:
    p = np.array([*point, 1.0], dtype=float)
    return float(p @ matrix @ p)


@_NEEDS_BUILD
def test_cone_blade_map_covers_all_q2_grade1_blades() -> None:
    assert set(CONE_BLADE_MAP) == {1, 2, 4, 8, 16, 32}


@_NEEDS_BUILD
def test_basis_q3_call_lifts_circle_to_right_cone() -> None:
    q2 = BasisQ2()
    q3 = BasisQ3()
    circle_coeffs = Conic(np.diag([1.0, 1.0, -1.0])).coeffs
    conic_mv = q2.multivector({1 << i: c for i, c in enumerate(circle_coeffs)})
    lifted = q3(conic_mv)
    coeffs = tuple(float(lifted[1 << i]) for i in range(10))
    quad = Quadric3D(coeffs)
    assert quad.kind.value == "cone"
    assert quad.rank == 3
    assert _quad_value(quad.matrix, (0.0, 0.0, 0.0)) == pytest.approx(0.0, abs=1e-8)
    assert _quad_value(quad.matrix, (1.0, 0.0, 1.0)) == pytest.approx(0.0, abs=1e-8)
