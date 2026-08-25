# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for Phase 11 CSG boolean combine modes (round-trip)."""

from __future__ import annotations

from pytanga.geometry.entities import Point, Sphere
from pytanga.viz.sdf.serializer import serialize_entity


def test_combine_serialized_analytic() -> None:
    result = serialize_entity(
        Sphere(Point(0.0, 0.0, 0.0), 1.0), "s", {"combine": "intersection"}
    )
    assert result["combine"] == "intersection"
    assert result["polarity"] == "positive"


def test_polarity_maps_to_combine() -> None:
    pos = serialize_entity(Sphere(Point(0.0, 0.0, 0.0), 1.0), "a", {"polarity": "positive"})
    neg = serialize_entity(Sphere(Point(0.0, 0.0, 0.0), 1.0), "b", {"polarity": "negative"})
    assert pos["combine"] == "union"
    assert neg["combine"] == "subtract"


def test_default_is_union() -> None:
    result = serialize_entity(Sphere(Point(0.0, 0.0, 0.0), 1.0), "c", {})
    assert result["combine"] == "union"
    assert result["polarity"] == "positive"


def test_smooth_combine_serialized() -> None:
    result = serialize_entity(
        Sphere(Point(0.0, 0.0, 0.0), 1.0),
        "s",
        {"combine": "smooth_union", "smoothness": 0.2},
    )
    assert result["combine"] == "smooth_union"
    assert result["smoothness"] == 0.2


def test_smooth_subtract_polarity_negative() -> None:
    result = serialize_entity(
        Sphere(Point(0.0, 0.0, 0.0), 1.0), "s", {"combine": "smooth_subtract"}
    )
    assert result["combine"] == "smooth_subtract"
    assert result["polarity"] == "negative"

