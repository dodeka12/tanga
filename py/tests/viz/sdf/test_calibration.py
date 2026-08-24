# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for Phase 9 gradient calibration + algebra-vs-analytic validation."""

from __future__ import annotations

import math

import numpy as np
import pytest

from pytanga.geometry import create_entity
from pytanga.geometry.entities import Direction, Line, Plane, Point
from pytanga.viz.sdf.calibration import (
    calibrate_scale,
    distance_value,
    evaluate_sdf,
    find_surface_point,
    gradient_norm,
    scale_at,
)

ALGEBRAS = ["e3", "p3", "n3", "pga3"]


def _basis(name: str):
    if name == "e3":
        from pytanga.basis.e3 import BasisE3

        return BasisE3(opns=True)
    if name == "p3":
        from pytanga.basis.p3 import BasisP3

        return BasisP3(opns=True)
    if name == "n3":
        from pytanga.basis.n3 import BasisN3

        return BasisN3(opns=True)
    if name == "pga3":
        from pytanga.basis.pga3 import BasisPGA3

        return BasisPGA3(opns=True)
    raise ValueError(name)


def _plane_mv(basis):
    return create_entity(
        basis, Plane(point=Point(0.0, 0.0, 0.0), normal=Direction(0.0, 0.0, 1.0))
    )


@pytest.mark.parametrize("name", ALGEBRAS)
def test_zero_set_matches_analytic_plane(name: str) -> None:
    basis = _basis(name)
    plane = _plane_mv(basis)

    # The algebra SDF vanishes on the analytic plane (z = 0) …
    for x, y in [(0.0, 0.0), (1.0, 2.0), (-3.0, 1.0)]:
        assert abs(evaluate_sdf(plane, x, y, 0.0, normalize=False)) < 1e-9

    # … and grows proportional to the metric distance off it.
    d1 = evaluate_sdf(plane, 0.0, 0.0, 1.0, normalize=False)
    d2 = evaluate_sdf(plane, 0.0, 0.0, 2.0, normalize=False)
    assert abs(d1) > 0.0 and abs(d2) > 0.0
    assert abs(abs(d2) - 2.0 * abs(d1)) < 1e-9


@pytest.mark.parametrize("name", ALGEBRAS)
def test_gradient_near_unit(name: str) -> None:
    basis = _basis(name)
    plane = _plane_mv(basis)

    s = calibrate_scale(plane, normalize=False)
    gn = gradient_norm(plane, 0.0, 0.0, 0.1, normalize=False)
    assert gn > 0.0
    # The calibrated field has |∇(s·d)| ≈ 1 near the surface.
    assert abs(s * gn - 1.0) < 1e-3


def test_scale_calibration_pga3() -> None:
    # pga3's point∧plane meet is grade-4, so scalar_pseudo is unsigned with a
    # √2 gradient; the calibration must divide it back to unit.
    basis = _basis("pga3")
    plane = _plane_mv(basis)

    gn = gradient_norm(plane, 0.0, 0.0, 0.1, normalize=False)
    assert abs(gn - math.sqrt(2.0)) < 1e-3  # raw is √2 (not unit)

    s = calibrate_scale(plane, normalize=False)
    assert abs(s - 1.0 / math.sqrt(2.0)) < 1e-3
    assert abs(s * gn - 1.0) < 1e-3


def test_find_surface_point_plane() -> None:
    basis = _basis("pga3")
    plane = _plane_mv(basis)
    sp = find_surface_point(plane, normalize=False)
    assert abs(evaluate_sdf(plane, *sp, normalize=False)) < 1e-4


def test_p3_trivector_zero_set() -> None:
    basis = _basis("p3")
    line = create_entity(
        basis, Line(origin=Point(0.0, 0.0, 0.0), direction=Direction(1.0, 0.0, 0.0))
    )
    # Points on the line have a vanishing trivector magnitude (zero-set = line).
    assert abs(evaluate_sdf(line, 3.0, 0.0, 0.0, normalize=False)) < 1e-9
    assert evaluate_sdf(line, 0.0, 1.0, 0.0, normalize=False) > 0.0


def test_n3_quadratic_point() -> None:
    basis = _basis("n3")
    pt = create_entity(basis, Point(1.0, 2.0, 3.0))
    # The conformal point's SDF vanishes at the point and grows away (the
    # ½ρ²·e∞ quadratic embedding produces a valid point distance).
    assert abs(evaluate_sdf(pt, 1.0, 2.0, 3.0, normalize=False)) < 1e-9
    assert evaluate_sdf(pt, 1.0, 2.0, 4.0, normalize=False) > 0.0


def test_distance_value_matches_reference() -> None:
    r = np.array([1.0, 2.0, 3.0, 0.0, 0.0], dtype=float)
    slot = 4
    # scalar_pseudo = r[0] + r[4] + sqrt(r[1]² + r[2]²) = 1 + 0 + sqrt(13).
    assert abs(distance_value(r, slot, "scalar_pseudo") - (1.0 + math.sqrt(13.0))) < 1e-12
    assert abs(distance_value(r, slot, "magnitude") - float(np.linalg.norm(r))) < 1e-12
    assert abs(distance_value(r, slot, "scalar") - 1.0) < 1e-12

    # grade (k=1) resolves the *blade* grade from result_ids, not the slot index:
    # slots map to blade ids [1, 2, 3, 4, 5]; grade-1 blades are ids 1/2/4 → slots
    # 0/1/3 → sqrt(2² + 3² + 5²) = sqrt(38).
    r_g = np.array([2.0, 3.0, 4.0, 5.0, 0.0], dtype=float)
    assert abs(
        distance_value(r_g, slot, "grade", result_ids=[1, 2, 3, 4, 5]) - math.sqrt(38.0)
    ) < 1e-12


def test_sign_observed() -> None:
    # Signed modes: e3/n3 plane evaluates to -z (negative on the +z normal
    # side), p3 to +z, pga3 is unsigned (|z|·√2). Locks in the documented
    # per-algebra sign convention (see calibration.py module docstring).
    for name, expected_z1 in [("e3", -1.0), ("p3", 1.0), ("n3", -1.0)]:
        basis = _basis(name)
        plane = _plane_mv(basis)
        assert evaluate_sdf(plane, 0.0, 0.0, 1.0, normalize=False) == pytest.approx(
            expected_z1, abs=1e-9
        )
    # pga3: unsigned — d(0,0,-1) == d(0,0,1) == √2.
    basis = _basis("pga3")
    plane = _plane_mv(basis)
    assert evaluate_sdf(plane, 0.0, 0.0, 1.0, normalize=False) == pytest.approx(
        math.sqrt(2.0), abs=1e-9
    )
    assert evaluate_sdf(plane, 0.0, 0.0, -1.0, normalize=False) == pytest.approx(
        math.sqrt(2.0), abs=1e-9
    )


def test_calibrate_scale_circle_not_stuck_at_center() -> None:
    from pytanga.basis.n3 import BasisN3
    from pytanga.geometry.entities import Circle, Direction, Point

    basis = BasisN3(opns=True)
    circle = create_entity(
        basis, Circle(center=Point(0.0, 0.0, 0.0), normal=Direction(0.0, 0.0, 1.0), radius=1.0)
    )
    s = calibrate_scale(circle, normalize=False)
    # The circle's centre is a stationary point (gradient ≈ 0, d = 0.5); the
    # surface finder must escape it and return a sane scale (~1), not a huge one.
    assert 0.1 < s < 10.0, f"calibrated scale {s} is not sane for a circle"

