# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for SDF primitive-tree AABB computation (Phase 2)."""

from __future__ import annotations

import pytest

from pytanga.viz.sdf.bounds import compute_bounds
from pytanga.viz.sdf.primitives import (
    bound_box,
    box,
    combine,
    partial_disk,
    regular_polygon,
    sphere,
    torus,
)


def test_sphere_bounds() -> None:
    b = compute_bounds(sphere(2.0))
    assert b["min"] == pytest.approx([-2.0, -2.0, -2.0])
    assert b["max"] == pytest.approx([2.0, 2.0, 2.0])


def test_box_bounds() -> None:
    b = compute_bounds(box((1.0, 2.0, 3.0)))
    assert b["min"] == pytest.approx([-1.0, -2.0, -3.0])
    assert b["max"] == pytest.approx([1.0, 2.0, 3.0])


def test_torus_bounds() -> None:
    b = compute_bounds(torus(3.0, 0.5))
    assert b["min"] == pytest.approx([-3.5, -0.5, -3.5])
    assert b["max"] == pytest.approx([3.5, 0.5, 3.5])


def test_union_bounds() -> None:
    a = sphere(1.0)
    c = sphere(1.0, position=(4.0, 0.0, 0.0))
    b = compute_bounds(combine("union", a, c))
    assert b["min"] == pytest.approx([-1.0, -1.0, -1.0])
    assert b["max"] == pytest.approx([5.0, 1.0, 1.0])


def test_intersect_bounds() -> None:
    a = box((2.0, 2.0, 2.0))
    c = box((0.5, 0.5, 0.5), position=(1.5, 0.0, 0.0))
    b = compute_bounds(combine("intersect", a, c))
    assert b["min"] == pytest.approx([1.0, -0.5, -0.5])
    assert b["max"] == pytest.approx([2.0, 0.5, 0.5])


def test_subtract_bounds() -> None:
    a = sphere(2.0)
    c = sphere(1.0, position=(10.0, 0.0, 0.0))
    b = compute_bounds(combine("subtract", a, c))
    assert b["min"] == pytest.approx([-2.0, -2.0, -2.0])
    assert b["max"] == pytest.approx([2.0, 2.0, 2.0])


def test_bound_bounds() -> None:
    b = compute_bounds(bound_box((1.0, 2.0, 3.0)))
    assert b["min"] == pytest.approx([-1.0, -2.0, -3.0])
    assert b["max"] == pytest.approx([1.0, 2.0, 3.0])


def test_padding() -> None:
    b = compute_bounds(sphere(1.0), padding=0.5)
    assert b["min"] == pytest.approx([-1.5, -1.5, -1.5])
    assert b["max"] == pytest.approx([1.5, 1.5, 1.5])


def test_transformed_sphere_bounds() -> None:
    b = compute_bounds(sphere(1.0, position=(3.0, 0.0, 0.0)))
    assert b["min"] == pytest.approx([2.0, -1.0, -1.0])
    assert b["max"] == pytest.approx([4.0, 1.0, 1.0])


def test_partial_disk_bounds() -> None:
    b = compute_bounds(partial_disk(2.0, half_height=0.5))
    assert b["min"] == pytest.approx([-2.0, -0.5, -2.0])
    assert b["max"] == pytest.approx([2.0, 0.5, 2.0])


def test_regular_polygon_bounds() -> None:
    b = compute_bounds(regular_polygon(1.5, 6, half_height=0.25))
    assert b["min"] == pytest.approx([-1.5, -0.25, -1.5])
    assert b["max"] == pytest.approx([1.5, 0.25, 1.5])
