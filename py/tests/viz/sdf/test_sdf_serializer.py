# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the SDF entity serializer (Phase 4)."""

from __future__ import annotations

import pytest
from pytanga.geometry.entities import (
    Box,
    Circle,
    Direction,
    Disk,
    Ellipse,
    Ellipsoid,
    Line,
    PartialDisk,
    Plane,
    Point,
    PointPair,
    RegularPolygon,
    Space,
    Sphere,
)
from pytanga.geometry.operators import (
    Dilator,
    GeneralRotor,
    Inversion,
    Motor,
    ReflectionLine,
    ReflectionPlane,
    ReflectionPoint,
    Rotor,
    Translator,
)
from pytanga.viz import CrossHairPointStyle
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


def test_serialize_disk_capped_cylinder() -> None:
    result = serialize_entity(Disk(Point(0, 0, 0), 2.0), "d")
    assert result["sdfKind"] == "Disk"
    tree = _tree_of(result)
    assert tree["kind"] == "cappedCylinder"
    assert tree["params"]["radius"] == 2.0


def test_serialize_partial_disk() -> None:
    import math

    result = serialize_entity(
        PartialDisk(Point(0, 0, 0), 1.0, angle=math.pi, start_direction=Direction(1, 0, 0)),
        "pd",
    )
    assert result["sdfKind"] == "PartialDisk"
    tree = _tree_of(result)
    assert tree["kind"] == "partialDisk"
    assert tree["params"]["angle"] == math.pi


def test_serialize_box() -> None:
    result = serialize_entity(Box(Point(0, 0, 0), (2.0, 3.0, 4.0)), "b")
    assert result["sdfKind"] == "Box"
    tree = _tree_of(result)
    assert tree["kind"] == "box"
    assert tree["params"]["halfExtents"] == [1.0, 1.5, 2.0]


def test_serialize_ellipsoid() -> None:
    result = serialize_entity(Ellipsoid(radii=(1.0, 0.5, 0.75)), "e")
    assert result["sdfKind"] == "Ellipsoid"
    tree = _tree_of(result)
    assert tree["kind"] == "ellipsoid"
    assert tree["params"]["radii"] == [1.0, 0.5, 0.75]


def test_serialize_ellipse() -> None:
    result = serialize_entity(Ellipse(radius_u=2.0, radius_v=1.0), "el")
    assert result["sdfKind"] == "Ellipse"
    tree = _tree_of(result)
    assert tree["kind"] == "ellipsoid"
    assert tree["params"]["radii"] == [2.0, 1.0, 0.01]


def test_serialize_regular_polygon() -> None:
    result = serialize_entity(RegularPolygon(radius=1.5, sides=6), "rp")
    assert result["sdfKind"] == "RegularPolygon"
    tree = _tree_of(result)
    assert tree["kind"] == "regularPolygon"
    assert tree["params"]["radius"] == 1.5
    assert tree["params"]["sides"] == 6


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
    from pytanga.geometry.operators import VersorFactors

    with pytest.raises(TypeError):
        serialize_entity(VersorFactors(), "v")
    with pytest.raises(TypeError):
        serialize_entity(object(), "o")


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


def test_serialize_space_box() -> None:
    result = serialize_entity(Space(), "sp")
    tree = result["tree"]
    assert tree["kind"] == "box"
    assert tree["params"]["halfExtents"] == [10.0, 10.0, 10.0]


def test_serialize_direction_arrow() -> None:
    result = serialize_entity(Direction(0, 0, 1), "d")
    tree = result["tree"]
    assert tree["kind"] == "union"
    assert [c["kind"] for c in tree["children"]] == ["cappedCylinder", "cappedCone"]


def test_serialize_crosshair_point() -> None:
    result = serialize_entity(
        Point(1, 2, 3), "p", {"style": CrossHairPointStyle(size=0.2)}
    )
    tree = result["tree"]
    assert tree["kind"] == "union"
    assert [c["kind"] for c in tree["children"]] == ["box", "box", "box"]


def test_operator_mapping() -> None:
    # ReflectionLine → capped cylinder
    refl_line = ReflectionLine(Line(Point(0, 0, 0), Direction(1, 0, 0)))
    assert serialize_entity(refl_line, "rl")["tree"]["kind"] == "cappedCylinder"

    # ReflectionPlane → bounded slab
    refl_plane = ReflectionPlane(Plane(Point(0, 0, 0), Direction(0, 0, 1)))
    assert serialize_entity(refl_plane, "rp")["tree"]["kind"] == "box"

    # ReflectionPoint → sphere
    refl_point = ReflectionPoint(Point(1, 2, 3))
    assert serialize_entity(refl_point, "rpt")["tree"]["kind"] == "sphere"

    # Inversion → sphere
    inversion = Inversion(Point(0, 0, 0), 2.0)
    assert serialize_entity(inversion, "inv")["tree"]["kind"] == "sphere"

    # Rotor → sector disc (filled to angle) + full rim ring + axis arrow
    rotor = Rotor(0.5, Direction(0, 0, 1))
    rot = serialize_entity(rotor, "rot")["tree"]
    assert rot["kind"] == "union"
    assert [c["kind"] for c in rot["children"]] == [
        "intersect",
        "torus",
        "union",
    ]
    sector = rot["children"][0]
    assert [c["kind"] for c in sector["children"]] == [
        "cappedCylinder",
        "plane",
        "plane",
    ]
    assert rot["children"][1]["kind"] == "torus"
    axis = rot["children"][2]
    assert [c["kind"] for c in axis["children"]] == ["cappedCylinder", "cappedCone"]

    # Translator → arrow (cylinder + cone)
    translator = Translator(Direction(1, 0, 0))
    tr = serialize_entity(translator, "tr")["tree"]
    assert tr["kind"] == "union"
    assert [c["kind"] for c in tr["children"]] == ["cappedCylinder", "cappedCone"]

    # Dilator → concentric torus rings
    dilator = Dilator(2.0)
    dl = serialize_entity(dilator, "dl")["tree"]
    assert dl["kind"] == "union"
    assert all(c["kind"] == "torus" for c in dl["children"])

    # Motor → disc + arrow
    motor = Motor(Rotor(0.5, Direction(0, 0, 1)), Translator(Direction(1, 0, 0)))
    assert serialize_entity(motor, "mo")["tree"]["kind"] == "union"

    # GeneralRotor → sector disc + full rim ring + axis arrow
    gen = GeneralRotor(0.5, Direction(0, 0, 1), Point(1, 0, 0))
    gr = serialize_entity(gen, "gr")["tree"]
    assert gr["kind"] == "union"
    assert [c["kind"] for c in gr["children"]] == [
        "intersect",
        "torus",
        "union",
    ]
    sector = gr["children"][0]
    assert [c["kind"] for c in sector["children"]] == [
        "cappedCylinder",
        "plane",
        "plane",
    ]
    assert gr["children"][1]["kind"] == "torus"
    axis = gr["children"][2]
    assert [c["kind"] for c in axis["children"]] == ["cappedCylinder", "cappedCone"]