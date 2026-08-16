# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for random geometric entity generators (RndPoint/RndDirection)."""

from __future__ import annotations

import numpy as np
import pytest

from pytanga.basis import (
    BasisE2,
    BasisE3,
    BasisN2,
    BasisN3,
    BasisP2,
    BasisP3,
    BasisPGA2,
    BasisPGA3,
)
from pytanga.geometry import (
    Geometry,
    Normal,
    RndDirection,
    RndPoint,
    Uniform,
)
from pytanga.geometry.entities import Direction, Point

ALL_ALGEBRAS = [
    BasisE2,
    BasisE3,
    BasisN2,
    BasisN3,
    BasisP2,
    BasisP3,
    BasisPGA2,
    BasisPGA3,
]


@pytest.fixture(params=ALL_ALGEBRAS, ids=lambda c: c.__name__)
def algebra(request):
    return request.param()


# ── rng / seeding ──────────────────────────────────────────────


def test_rng_is_generator(algebra):
    geo = Geometry(algebra)
    assert isinstance(geo.rng, np.random.Generator)


def test_seed_determinism(algebra):
    a = Geometry(algebra, seed=42)(RndPoint((-2, 2), (-2, 2), (-2, 2)))
    b = Geometry(algebra, seed=42)(RndPoint((-2, 2), (-2, 2), (-2, 2)))
    assert a.to_dict() == b.to_dict()


# ── RndPoint: direct generation ────────────────────────────────


def test_rndpoint_returns_point_with_rng():
    gen = np.random.default_rng(0)
    result = RndPoint((-1, 1), (-1, 1), (-1, 1))(gen)
    assert isinstance(result, Point)


def test_rndpoint_count_returns_list():
    gen = np.random.default_rng(0)
    result = RndPoint((-1, 1), (-1, 1), (-1, 1), count=10)(gen)
    assert isinstance(result, list)
    assert len(result) == 10
    assert all(isinstance(p, Point) for p in result)


def test_rndpoint_normal_distribution():
    gen = np.random.default_rng(0)
    rnd = RndPoint(Normal(0, 0.001), Normal(0, 0.001), (-5, 5))
    samples = [rnd(gen) for _ in range(200)]
    xs = [p.x for p in samples]
    ys = [p.y for p in samples]
    assert abs(np.mean(xs)) < 0.01
    assert abs(np.mean(ys)) < 0.01
    # z is uniform in (-5, 5)
    assert all(-5.0 <= p.z < 5.0 for p in samples)


def test_rndpoint_uniform_bounds():
    gen = np.random.default_rng(0)
    rnd = RndPoint((1, 2), (-3, -2), (0, 0.1))
    for _ in range(20):
        p = rnd(gen)
        assert 1.0 <= p.x < 2.0
        assert -3.0 <= p.y < -2.0
        assert 0.0 <= p.z < 0.1


# ── RndDirection ───────────────────────────────────────────────


def test_rnddirection_returns_direction_with_rng():
    gen = np.random.default_rng(0)
    result = RndDirection((-1, 1), (-1, 1), (-1, 1))(gen)
    assert isinstance(result, Direction)


def test_rnddirection_count_returns_list():
    gen = np.random.default_rng(0)
    result = RndDirection((-1, 1), (-1, 1), (-1, 1), count=5)(gen)
    assert isinstance(result, list)
    assert len(result) == 5
    assert all(isinstance(d, Direction) for d in result)


# ── Geometry.__call__ integration ──────────────────────────────


def test_geometry_call_single_rndpoint_returns_mv(algebra):
    mv = Geometry(algebra, seed=0)(RndPoint((-2, 2), (-2, 2), (-2, 2)))
    assert hasattr(mv, "to_dict")


def test_geometry_call_count_returns_mv_list(algebra):
    mvs = Geometry(algebra, seed=0)(RndPoint((-2, 2), (-2, 2), (-2, 2), count=10))
    assert isinstance(mvs, list)
    assert len(mvs) == 10
    assert all(hasattr(mv, "to_dict") for mv in mvs)


def test_geometry_call_list_of_rndpoint(algebra):
    mvs = Geometry(algebra, seed=0)(
        [RndPoint((-2, 2), (-2, 2), (-2, 2)) for _ in range(4)]
    )
    assert isinstance(mvs, list)
    assert len(mvs) == 4
    assert all(hasattr(mv, "to_dict") for mv in mvs)


def test_geometry_call_normal_distribution(algebra):
    mv = Geometry(algebra, seed=0)(RndPoint(Normal(0, 0.1), (-1, 1), (-1, 1)))
    assert hasattr(mv, "to_dict")


# ── Uniform class ──────────────────────────────────────────────


def test_uniform_class_sampling():
    gen = np.random.default_rng(0)
    for _ in range(10):
        v = Uniform(2.0, 3.0)(gen)
        assert 2.0 <= v < 3.0


def test_unknown_spec_raises():
    with pytest.raises(TypeError):
        RndPoint("not-a-spec", (-1, 1), (-1, 1))