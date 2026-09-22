# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for entity → (Transform, shape) decomposition and set_entity diffing."""

import math

import pytest

from pytanga.geometry.entities import (
    Arc,
    Box,
    Circle,
    Cylinder,
    Direction,
    Line,
    Plane,
    Point,
    Space,
    Sphere,
)
from pytanga.viz._decompose import _entity_decompose, is_placement_entity
from pytanga.viz._nodes import VizSceneObject


class TestEntityDecompose:
    def test_circle(self) -> None:
        t, shape = _entity_decompose(Circle(Point(1, 2, 3), 5.0))
        assert t.position == (1.0, 2.0, 3.0)
        assert shape == {"radius": 5.0, "isImaginary": False}
        assert t @ Direction(0, 0, 1) == Direction(0, 0, 1)

    def test_circle_normal_rotation(self) -> None:
        t, _ = _entity_decompose(Circle(Point(0, 0, 0), 1.0, normal=Direction(1, 0, 0)))
        d = t @ Direction(0, 0, 1)
        assert (d.x, d.y, d.z) == pytest.approx((1.0, 0.0, 0.0))

    def test_cylinder_align_center_folds_into_position(self) -> None:
        t, shape = _entity_decompose(
            Cylinder(origin=Point(0, 0, 0), axis=Direction(0, 0, 1), length=4.0, radius=1.0)
        )
        assert t.position == (0.0, 0.0, 2.0)
        assert shape == {"length": 4.0, "radius": 1.0}
        d = t @ Direction(0, 1, 0)
        assert (d.x, d.y, d.z) == pytest.approx((0.0, 0.0, 1.0))

    def test_box(self) -> None:
        t, shape = _entity_decompose(Box(Point(1, 1, 1), (2, 3, 4)))
        assert t.position == (1.0, 1.0, 1.0)
        assert shape == {"size": (2.0, 3.0, 4.0)}

    def test_line(self) -> None:
        t, shape = _entity_decompose(
            Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0), length=2.0)
        )
        assert t.position == (0.0, 0.0, 0.0)
        assert shape == {"length": 2.0}
        d = t @ Direction(0, 1, 0)
        assert (d.x, d.y, d.z) == pytest.approx((1.0, 0.0, 0.0))

    def test_arc_frame(self) -> None:
        t, shape = _entity_decompose(
            Arc(
                origin=Point(1, 2, 3),
                axis=Direction(0, 0, 1),
                radius=2.0,
                tube_radius=0.1,
                angle=math.pi,
                start_direction=Direction(1, 0, 0),
            )
        )
        assert t.position == (1.0, 2.0, 3.0)
        assert shape["radius"] == 2.0
        assert shape["angle"] == pytest.approx(math.pi)
        z = t @ Direction(0, 0, 1)
        assert (z.x, z.y, z.z) == pytest.approx((0.0, 0.0, 1.0))
        x = t @ Direction(1, 0, 0)
        assert (x.x, x.y, x.z) == pytest.approx((1.0, 0.0, 0.0))

    def test_plane(self) -> None:
        t, shape = _entity_decompose(
            Plane(point=Point(0, 0, 1), normal=Direction(0, 0, 1), extent=5.0)
        )
        assert t.position == (0.0, 0.0, 1.0)
        assert shape == {"extent": 5.0}

    def test_is_placement_entity(self) -> None:
        assert is_placement_entity(Circle(Point(0, 0, 0), 1.0))
        assert is_placement_entity(Point(0, 0, 0))
        assert not is_placement_entity(Space(scale=1.0))


class TestSetEntityDiff:
    def test_center_change_marks_transform(self) -> None:
        node = VizSceneObject("a", Circle(Point(0, 0, 0), 1.0), kind="Circle")
        node.consume_dirty()
        node.set_entity(Circle(Point(1, 0, 0), 1.0))
        assert node.dirty_for("transform")
        assert not node.dirty_for("content")

    def test_radius_change_marks_content(self) -> None:
        node = VizSceneObject("a", Circle(Point(0, 0, 0), 1.0), kind="Circle")
        node.consume_dirty()
        node.set_entity(Circle(Point(0, 0, 0), 2.0))
        assert node.dirty_for("content")
        assert not node.dirty_for("transform")

    def test_kind_change_marks_full(self) -> None:
        node = VizSceneObject("a", Circle(Point(0, 0, 0), 1.0), kind="Circle")
        node.consume_dirty()
        node.set_entity(Sphere(Point(0, 0, 0), 1.0))
        assert node.dirty_for("full")

    def test_within_eps_marks_nothing(self) -> None:
        node = VizSceneObject("a", Circle(Point(0, 0, 0), 1.0), kind="Circle")
        node.consume_dirty()
        node.set_entity(Circle(Point(1e-12, 0, 0), 1.0))
        assert not node.dirty_for("transform")
        assert not node.dirty_for("content")

    def test_placement_and_shape_change_mark_both(self) -> None:
        node = VizSceneObject("a", Circle(Point(0, 0, 0), 1.0), kind="Circle")
        node.consume_dirty()
        node.set_entity(Circle(Point(2, 0, 0), 3.0))
        assert node.dirty_for("transform")
        assert node.dirty_for("content")
