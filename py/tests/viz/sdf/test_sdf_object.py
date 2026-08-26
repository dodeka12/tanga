# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for SdfObject + _entity_to_sdf (viz-sdf-object-model Phase 3)."""

from __future__ import annotations

from pytanga.geometry import (
    Box,
    Circle,
    Cylinder,
    Direction,
    Disk,
    Ellipse,
    Ellipsoid,
    Line,
    PartialDisk,
    Point,
    RegularPolygon,
    Sphere,
)
from pytanga.viz import SdfCircleStyle, SdfLineStyle
from pytanga.viz.sdf import Combine, ECompose, SdfObject
from pytanga.viz.sdf.object import _entity_to_sdf


def test_sdf_object_sphere_to_sdf_node() -> None:
    node = SdfObject(Sphere(Point(1.0, 2.0, 3.0), 2.0), id="s").to_sdf_node()
    assert node.kind == "sphere"
    assert node.params == {"radius": 2.0}
    assert node.transform == {"position": [1.0, 2.0, 3.0]}
    assert node.id == "s"


def test_entity_to_sdf_cylinder_centered() -> None:
    node = _entity_to_sdf(
        Cylinder(
            origin=Point(0.0, 0.0, 0.0),
            axis=Direction(0.0, 1.0, 0.0),
            length=3.0,
            radius=0.35,
            align_center=0.5,
        )
    )
    assert node.kind == "cappedCylinder"
    assert node.params == {"halfHeight": 1.5, "radius": 0.35}
    # Centered at origin, no rotation needed (axis already +Y).
    assert node.transform == {"position": [0.0, 0.0, 0.0]}


def test_entity_to_sdf_cylinder_align_zero() -> None:
    node = _entity_to_sdf(
        Cylinder(
            origin=Point(0.0, 0.0, 0.0),
            axis=Direction(0.0, 1.0, 0.0),
            length=3.0,
            radius=0.35,
            align_center=0.0,
        )
    )
    # Starts at origin, extends +Y → midpoint at +Y * (length/2).
    assert node.transform["position"] == [0.0, 0.75, 0.0]


def test_entity_to_sdf_line_thickness_from_style() -> None:
    line = Line.from_points(Point(0.0, 0.0, 0.0), Point(0.0, 2.0, 0.0))
    node = _entity_to_sdf(line, SdfLineStyle(thickness=0.5))
    assert node.kind == "cappedCylinder"
    assert node.params == {"halfHeight": 1.0, "radius": 0.5}


def test_entity_to_sdf_circle_tube_radius_from_style() -> None:
    node = _entity_to_sdf(
        Circle(Point(0.0, 0.0, 0.0), 1.0, Direction(0.0, 0.0, 1.0)),
        SdfCircleStyle(tube_radius=0.1),
    )
    assert node.kind == "torus"
    assert node.params == {"mainRadius": 1.0, "tubeRadius": 0.1}


def test_entity_to_sdf_infinite_line_adds_bound() -> None:
    line = Line(Point(0.0, 0.0, 0.0), Direction(0.0, 1.0, 0.0))
    node = _entity_to_sdf(line)
    assert node.kind == "intersect"
    assert len(node.children) == 2


def test_operator_builds_combine() -> None:
    a = SdfObject(Sphere(Point(0.0, 0.0, 0.0), 1.0))
    b = SdfObject(Cylinder(origin=Point(0, 0, 0), axis=Direction(0, 1, 0), length=1.0, radius=0.3, align_center=0.5))
    node = a + b
    assert isinstance(node, Combine)
    assert node.op is ECompose.UNION


def test_operator_coerces_raw_entity() -> None:
    a = SdfObject(Sphere(Point(0.0, 0.0, 0.0), 1.0))
    node = a + Sphere(Point(1.0, 0.0, 0.0), 0.5)
    assert isinstance(node, Combine)
    assert isinstance(node.b, SdfObject)


def test_entity_to_sdf_disk() -> None:
    node = _entity_to_sdf(Disk(Point(1.0, 2.0, 3.0), 2.0))
    assert node.kind == "cappedCylinder"
    assert node.params == {"halfHeight": 0.01, "radius": 2.0}
    assert node.transform["position"] == [1.0, 2.0, 3.0]


def test_entity_to_sdf_partial_disk() -> None:
    import math

    node = _entity_to_sdf(
        PartialDisk(Point(0.0, 0.0, 0.0), 1.0, angle=math.pi, start_direction=Direction(1, 0, 0))
    )
    assert node.kind == "partialDisk"
    assert node.params["radius"] == 1.0
    assert node.params["halfHeight"] == 0.01
    assert node.params["angle"] == math.pi


def test_entity_to_sdf_partial_disk_full_reduces_to_cylinder() -> None:
    node = _entity_to_sdf(PartialDisk())
    assert node.kind == "cappedCylinder"


def test_entity_to_sdf_box() -> None:
    node = _entity_to_sdf(Box(Point(1.0, 0.0, 0.0), (2.0, 3.0, 4.0)))
    assert node.kind == "box"
    assert node.params == {"halfExtents": [1.0, 1.5, 2.0]}
    assert node.transform["position"] == [1.0, 0.0, 0.0]


def test_entity_to_sdf_ellipsoid() -> None:
    node = _entity_to_sdf(Ellipsoid(radii=(1.0, 0.5, 0.75)))
    assert node.kind == "ellipsoid"
    assert node.params == {"radii": [1.0, 0.5, 0.75]}


def test_entity_to_sdf_ellipse() -> None:
    node = _entity_to_sdf(Ellipse(radius_u=2.0, radius_v=1.0))
    assert node.kind == "ellipsoid"
    assert node.params == {"radii": [2.0, 1.0, 0.01]}


def test_entity_to_sdf_regular_polygon() -> None:
    node = _entity_to_sdf(RegularPolygon(radius=1.5, sides=6))
    assert node.kind == "regularPolygon"
    assert node.params["radius"] == 1.5
    assert node.params["sides"] == 6
    assert node.params["halfHeight"] == 0.01


def test_entity_to_sdf_regular_polygon_orientation() -> None:
    from pytanga.viz.sdf.primitives import _normalize, _rotate_about

    node = _entity_to_sdf(RegularPolygon(radius=1.0, sides=6))
    axis = tuple(node.transform["rotation"]["axis"])
    angle = node.transform["rotation"]["angle"]

    # The primitive's plane normal (+Y) must map to the entity normal (+Z), and
    # its first vertex (+Z) must stay in the xy-plane (perpendicular to +Z).
    y_img = _normalize(_rotate_about((0.0, 1.0, 0.0), axis, angle))
    z_img = _normalize(_rotate_about((0.0, 0.0, 1.0), axis, angle))
    assert abs(y_img[0]) < 1e-9
    assert abs(y_img[1]) < 1e-9
    assert abs(y_img[2] - 1.0) < 1e-9
    assert abs(z_img[2]) < 1e-9
