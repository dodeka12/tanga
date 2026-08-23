# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for Phase 11 CSG boolean combine modes (round-trip + signedness gate)."""

from __future__ import annotations

import logging
from pathlib import Path

from pytanga.basis.pga3 import BasisPGA3
from pytanga.geometry import create_entity
from pytanga.geometry.entities import Direction, Plane, Point, Sphere
from pytanga.viz.sdf.distance import DistanceFunction
from pytanga.viz.sdf.serializer import serialize_entity, serialize_mv
from pytanga.viz.sdf.visualizer import SdfVisualizer

SDF_VIEWER_JS = (
    Path(__file__).parents[3] / "pytanga" / "viz" / "templates" / "sdf" / "sdf_viewer.js"
)


def test_combine_serialized_analytic() -> None:
    result = serialize_entity(
        Sphere(Point(0.0, 0.0, 0.0), 1.0), "s", {"combine": "intersection"}
    )
    assert result["combine"] == "intersection"
    assert result["polarity"] == "positive"


def test_combine_serialized_mv_sdf() -> None:
    basis = BasisPGA3(opns=True)
    plane = create_entity(
        basis, Plane(point=Point(0.0, 0.0, 0.0), normal=Direction(0.0, 0.0, 1.0))
    )
    result = serialize_mv(plane, "p", {"combine": "subtract"})
    assert result["sdfKind"] == "mv_sdf"
    assert result["combine"] == "subtract"
    assert result["polarity"] == "negative"


def test_polarity_maps_to_combine() -> None:
    pos = serialize_entity(Sphere(Point(0.0, 0.0, 0.0), 1.0), "a", {"polarity": "positive"})
    neg = serialize_entity(Sphere(Point(0.0, 0.0, 0.0), 1.0), "b", {"polarity": "negative"})
    assert pos["combine"] == "union"
    assert neg["combine"] == "subtract"


def test_default_is_union() -> None:
    result = serialize_entity(Sphere(Point(0.0, 0.0, 0.0), 1.0), "c", {})
    assert result["combine"] == "union"
    assert result["polarity"] == "positive"


def test_distance_signed_property() -> None:
    assert DistanceFunction.SCALAR_PSEUDO.signed is True
    assert DistanceFunction.SCALAR.signed is True
    assert DistanceFunction.COMPONENT.signed is True
    assert DistanceFunction.MAGNITUDE.signed is False
    assert DistanceFunction.GRADE.signed is False


def test_signedness_gate(caplog) -> None:
    viz = SdfVisualizer()
    viz.distance = DistanceFunction.MAGNITUDE
    with caplog.at_level(logging.WARNING):
        viz.add(Sphere(Point(0.0, 0.0, 0.0), 1.0), combine="subtract")
    assert any("require a signed" in r.message for r in caplog.records)


def test_signedness_gate_silent_when_signed(caplog) -> None:
    viz = SdfVisualizer()
    viz.distance = DistanceFunction.SCALAR_PSEUDO
    with caplog.at_level(logging.WARNING):
        viz.add(Sphere(Point(0.0, 0.0, 0.0), 1.0), combine="subtract")
    assert not any("require a signed" in r.message for r in caplog.records)


def test_frontend_signedness_gate_present() -> None:
    js = SDF_VIEWER_JS.read_text(encoding="utf-8")
    assert "warnUnsignedBooleans" in js


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


def test_smooth_subtract_signedness_gate(caplog) -> None:
    viz = SdfVisualizer()
    viz.distance = DistanceFunction.MAGNITUDE
    with caplog.at_level(logging.WARNING):
        viz.add(Sphere(Point(0.0, 0.0, 0.0), 1.0), combine="smooth_subtract")
    assert any("require a signed" in r.message for r in caplog.records)

