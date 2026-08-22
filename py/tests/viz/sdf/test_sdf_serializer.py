# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the SDF entity serializer (Phase 4)."""

from __future__ import annotations

import pytest
from pytanga.geometry.entities import (
    Circle,
    Direction,
    Line,
    Plane,
    Point,
    PointPair,
    Space,
    Sphere,
)
from pytanga.geometry.operators import Rotor
from pytanga.viz.sdf.serializer import serialize_entity


def _tree_of(result: dict) -> dict:
    return result["tree"]


def test_serialize_point_uses_size() -> None:
    result = serialize_entity(Point(1, 2, 3), "p", {"size": 0.15})
    tree = _tree_of(result)
    assert tree["kind"] == "sphere"
    assert tree["params"]["radius"] == 0.15
    assert tree["transform"]["position"] == [1.0, 2.0, 3.0]


def test_serialize_line_finite_capped_cylinder() -> None:
    line = Line.from_points(Point(0, 0, 0), Point(0, 0, 4))
    result = serialize_entity(line, "l", {"thickness": 0.05})
    tree = _tree_of(result)
    assert tree["kind"] == "cappedCylinder"
    assert tree["params"]["radius"] == 0.05
    assert tree["params"]["halfHeight"] == pytest.approx(2.0)
    assert tree["transform"]["position"] == pytest.approx([0.0, 0.0, 2.0])


def test_serialize_line_infinite_has_bound() -> None:
    line = Line(Point(0, 0, 0), Direction(0, 1, 0))
    result = serialize_entity(line, "l", {"thickness": 0.05})
    tree = _tree_of(result)
    assert tree["kind"] == "intersect"
    kinds = {child["kind"] for child in tree["children"]}
    assert kinds == {"cappedCylinder", "box"}


def test_serialize_circle_torus() -> None:
    circle = Circle(Point(0, 0, 0), 2.0, Direction(0, 0, 1))
    result = serialize_entity(circle, "c", {"thickness": 0.03})
    tree = _tree_of(result)
    assert tree["kind"] == "torus"
    assert tree["params"]["mainRadius"] == 2.0
    assert tree["params"]["tubeRadius"] == 0.03


def test_serialize_sphere_filled() -> None:
    sphere = Sphere(Point(1, 1, 1), 2.5)
    result = serialize_entity(sphere, "s")
    tree = _tree_of(result)
    assert tree["kind"] == "sphere"
    assert tree["params"]["radius"] == 2.5
    assert tree["transform"]["position"] == [1.0, 1.0, 1.0]


def test_serialize_point_pair_two_spheres_and_segment() -> None:
    pp = PointPair(Point(0, 0, 0), Point(0, 0, 2))
    result = serialize_entity(pp, "pp", {"size": 0.06, "thickness": 0.02})
    tree = _tree_of(result)
    assert tree["kind"] == "union"
    kinds = [child["kind"] for child in tree["children"]]
    assert kinds.count("sphere") == 2
    assert kinds.count("cappedCylinder") == 1


def test_serialize_plane_bounded_slab() -> None:
    plane = Plane(Point(0, 0, 0), Direction(0, 0, 1), extent=5.0)
    result = serialize_entity(plane, "pl")
    tree = _tree_of(result)
    assert tree["kind"] == "box"
    assert tree["params"]["halfExtents"] == [5.0, 5.0, pytest.approx(0.05)]


def test_serialize_plane_with_spans() -> None:
    plane = Plane(
        Point(0, 0, 0),
        Direction(0, 0, 1),
        span_u=Direction(2, 0, 0),
        span_v=Direction(0, 4, 0),
    )
    result = serialize_entity(plane, "pl")
    tree = _tree_of(result)
    assert tree["params"]["halfExtents"] == [1.0, 2.0, pytest.approx(0.02)]


def test_unsupported_kind_raises() -> None:
    with pytest.raises(TypeError):
        serialize_entity(Direction(1, 0, 0), "d")
    with pytest.raises(TypeError):
        serialize_entity(Space(Point(0, 0, 0)), "sp")
    with pytest.raises(TypeError):
        serialize_entity(Rotor(angle=0.5, axes=(0, 0, 1)), "r")


def test_style_scope_ignores_wireframe() -> None:
    result = serialize_entity(
        Point(0, 0, 0), "p", {"size": 0.1, "wireframe": True}
    )
    tree = _tree_of(result)
    # wireframe is not forwarded into the SDF tree.
    assert "wireframe" not in result
    assert "wireframe" not in tree


def test_serialize_combine_and_polarity() -> None:
    result = serialize_entity(
        Sphere(Point(0, 0, 0), 1.0), "s", {"combine": "subtract"}
    )
    assert result["combine"] == "subtract"
    assert result["polarity"] == "negative"

    result2 = serialize_entity(
        Sphere(Point(0, 0, 0), 1.0), "s2", {"polarity": "negative"}
    )
    assert result2["combine"] == "subtract"
    assert result2["polarity"] == "negative"


def test_color_opacity_forwarded() -> None:
    result = serialize_entity(
        Sphere(Point(0, 0, 0), 1.0), "s", {"color": "#ff0000", "opacity": 0.5}
    )
    assert result["color"] == "#ff0000"
    assert result["opacity"] == 0.5