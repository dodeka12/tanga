# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the `pytanga.viz.labelme` module."""

from __future__ import annotations

from typing import Any

from pytanga.geometry import Circle, Ellipse, Line, Point, Rectangle2D
from pytanga.viz import (
    ActCircle,
    ActEllipse,
    ActLine,
    ActPoint,
    ActPolygon,
    ActRectangle2D,
    LabelMeDocument,
    LabelMeStore,
    LabelShape,
)


class _FakeHandle:
    def __init__(self) -> None:
        self.added: list[object] = []

    def add(self, obj: Any, *, style: Any = None, **kwargs: Any) -> str:
        self.added.append(obj)
        return f"e{len(self.added)}"


def _doc() -> LabelMeDocument:
    return LabelMeDocument(
        shapes=[
            LabelShape(label="rect", points=[(0.0, 0.0), (4.0, 2.0)], shape_type="rectangle"),
            LabelShape(label="circ", points=[(1.0, 1.0), (3.0, 1.0)], shape_type="circle"),
            LabelShape(
                label="poly",
                points=[(0.0, 0.0), (2.0, 0.0), (2.0, 2.0)],
                shape_type="polygon",
            ),
            LabelShape(label="strip", points=[(0.0, 0.0), (2.0, 0.0)], shape_type="linestrip"),
            LabelShape(label="line", points=[(0.0, 0.0), (1.0, 0.0)], shape_type="line"),
            LabelShape(label="pt", points=[(5.0, 5.0)], shape_type="point"),
        ]
    )


class TestSerialize:
    def test_round_trip(self) -> None:
        store = LabelMeStore()
        doc = _doc()
        doc2 = store.loads(store.dumps(doc))
        assert doc2.shapes == doc.shapes
        assert doc2.image_path == doc.image_path


class TestAddShapes:
    def test_active_true(self) -> None:
        store = LabelMeStore()
        handle = _FakeHandle()
        objs = store.add_shapes(handle, _doc(), active=True)
        assert isinstance(objs[0], ActRectangle2D)
        assert isinstance(objs[1], ActCircle)
        assert isinstance(objs[2], ActPolygon)
        assert isinstance(objs[3], ActPolygon)  # linestrip → open ActPolygon
        assert isinstance(objs[4], ActLine)
        assert isinstance(objs[5], ActPoint)
        assert len(handle.added) == 6

    def test_active_false(self) -> None:
        store = LabelMeStore()
        handle = _FakeHandle()
        objs = store.add_shapes(handle, _doc(), active=False)
        assert isinstance(objs[0], Rectangle2D)
        assert isinstance(objs[1], Circle)
        assert isinstance(objs[3], object)  # linestrip → PointPath (open)
        assert isinstance(objs[4], Line)
        assert isinstance(objs[5], Point)


class TestInverse:
    def test_shapes_from_objects(self) -> None:
        store = LabelMeStore()
        shapes = store.shapes_from_objects(
            [
                (ActRectangle2D(center=Point(2, 1, 0), size=(4, 2)), "r"),
                (ActCircle(center=Point(1, 1, 0), radius=2.0), "c"),
                (ActLine(Point(0, 0, 0), Point(3, 4, 0)), "l"),
                (ActPoint(Point(5, 5, 0)), "p"),
            ]
        )
        assert shapes[0].shape_type == "rectangle"
        assert shapes[0].points == [(0.0, 0.0), (4.0, 2.0)]
        assert shapes[1].shape_type == "circle"
        assert shapes[2].shape_type == "line"
        assert shapes[2].points == [(0.0, 0.0), (3.0, 4.0)]
        assert shapes[3].shape_type == "point"


class TestExtensions:
    def test_ellipse_extension_on(self) -> None:
        store = LabelMeStore(allow_extensions=True)
        ellipse = Ellipse(center=Point(0, 0, 0), radius_u=3.0, radius_v=2.0)
        shapes = store.shapes_from_objects([(ellipse, "x")])
        assert shapes[0].shape_type == "ellipse"
        assert len(shapes[0].points) == 3

    def test_ellipse_extension_off_sampled_polygon(self) -> None:
        store = LabelMeStore(allow_extensions=False)
        ellipse = Ellipse(center=Point(0, 0, 0), radius_u=3.0, radius_v=2.0)
        shapes = store.shapes_from_objects([(ellipse, "x")])
        assert shapes[0].shape_type == "polygon"
        assert len(shapes[0].points) == 32

    def test_ellipse_extension_off_circle(self) -> None:
        store = LabelMeStore(allow_extensions=False)
        ellipse = Ellipse(center=Point(1, 2, 0), radius_u=2.0, radius_v=2.0)
        shapes = store.shapes_from_objects([(ellipse, "x")])
        assert shapes[0].shape_type == "circle"
