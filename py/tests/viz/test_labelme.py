# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the `pytanga.viz.labelme` module."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from pytanga.geometry import Circle, Ellipse, Line, Matrix, OpenCVFrame, Point, Rectangle2D
from pytanga.viz import (
    ActCircle,
    ActEllipse,
    ActLine,
    ActPoint,
    ActPolygon,
    ActRectangle2D,
    CalibratedPlaneMapper,
    CameraCalibration,
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
        doc2 = store.loads(store.dumps(doc)).document
        assert doc2.shapes == doc.shapes
        assert doc2.image_path == doc.image_path


class TestAddShapes:
    def test_active_true(self) -> None:
        store = LabelMeStore()
        handle = _FakeHandle()
        objs = store.add_shapes(handle, _doc(), active=True)[0]
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
        objs = store.add_shapes(handle, _doc(), active=False)[0]
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


def test_mask_round_trip() -> None:
    store = LabelMeStore()
    doc = LabelMeDocument(
        shapes=[LabelShape(label="a", points=[(0, 0)], shape_type="point", mask="AAAA")]
    )
    doc2 = store.loads(store.dumps(doc)).document
    assert doc2.shapes[0].mask == "AAAA"


def test_description_none_preserved() -> None:
    store = LabelMeStore()
    doc = LabelMeDocument(
        shapes=[LabelShape(label="a", points=[(0, 0)], shape_type="point")]
    )
    doc2 = store.loads(store.dumps(doc)).document
    assert doc2.shapes[0].description is None


def test_style_act_not_serialized() -> None:
    store = LabelMeStore()
    doc = LabelMeDocument(
        shapes=[
            LabelShape(
                label="a",
                points=[(0, 0)],
                shape_type="point",
                style=object(),
                act=object(),
            )
        ]
    )
    text = store.dumps(doc)
    assert '"style"' not in text
    assert '"act"' not in text


def test_default_mapper_round_trips_entities() -> None:
    # The default PlanarMapper must preserve the pre-mapper behavior exactly
    # (pixel == world XY): even size-based shapes round-trip.
    store = LabelMeStore()
    doc = LabelMeDocument(
        shapes=[
            LabelShape(label="r", points=[(0, 0), (4, 2)], shape_type="rectangle"),
            LabelShape(label="l", points=[(0, 0), (3, 4)], shape_type="line"),
        ]
    )
    rebuilt = store.shapes_from_objects(store.iter_objects(doc, active=False)[0])
    assert rebuilt[0].points == [(0.0, 0.0), (4.0, 2.0)]
    assert rebuilt[1].points == [(0.0, 0.0), (3.0, 4.0)]


def test_calibrated_mapper_round_trip_point_shapes() -> None:
    # Point-based shapes (line/polygon/point) store their vertices directly, so
    # a calibrated mapper round-trips them exactly.
    calib = CameraCalibration(
        K=Matrix([[500.0, 0.0, 320.0], [0.0, 500.0, 240.0], [0.0, 0.0, 1.0]]),
        R=Matrix(np.eye(3)),
        t=[0.0, 0.0, 0.0],
        image_size=(640, 480),
        frame=OpenCVFrame(),
        units=1.0,
    )
    store = LabelMeStore(mapper=CalibratedPlaneMapper(calib, depth=1.0))
    doc = LabelMeDocument(
        shapes=[
            LabelShape(label="l", points=[(50, 50), (400, 300)], shape_type="line"),
            LabelShape(
                label="poly",
                points=[(100, 100), (300, 100), (300, 300)],
                shape_type="polygon",
            ),
            LabelShape(label="pt", points=[(320, 240)], shape_type="point"),
        ]
    )
    rebuilt = store.shapes_from_objects(store.iter_objects(doc, active=True)[0])
    assert [s.shape_type for s in rebuilt] == [s.shape_type for s in doc.shapes]
    for orig, back in zip(doc.shapes, rebuilt):
        assert len(back.points) == len(orig.points)
        for (u0, v0), (u1, v1) in zip(orig.points, back.points):
            assert u0 == pytest.approx(u1, abs=1e-6)
            assert v0 == pytest.approx(v1, abs=1e-6)


def test_load_skips_single_point_rectangle() -> None:
    store = LabelMeStore()
    text = json.dumps(
        {
            "shapes": [
                {"label": "r", "points": [[1, 1]], "shape_type": "rectangle"},
            ],
        }
    )
    result = store.loads(text)
    assert result.document.shapes == []
    assert len(result.errors) == 1
    assert "needs at least 2 points" in result.errors[0]


def test_load_reports_mixed_valid_invalid() -> None:
    store = LabelMeStore()
    text = json.dumps(
        {
            "shapes": [
                {"label": "ok", "points": [[0, 0], [1, 1]], "shape_type": "line"},
                {"label": "bad", "points": [[1, 1]], "shape_type": "rectangle"},
            ],
        }
    )
    result = store.loads(text)
    assert [s.label for s in result.document.shapes] == ["ok"]
    assert len(result.errors) == 1
    assert "bad" in result.errors[0]


def test_add_shapes_reports_unknown_shape_type() -> None:
    store = LabelMeStore()
    handle = _FakeHandle()
    doc = LabelMeDocument(
        shapes=[LabelShape(label="x", points=[(0, 0)], shape_type="blob")]
    )
    objs, errors = store.add_shapes(handle, doc, active=False)
    assert objs == []
    assert len(errors) == 1
    assert "Unknown labelme shape_type" in errors[0]


def test_coordinate_precision_rounds() -> None:
    doc = LabelMeDocument(
        shapes=[LabelShape(label="a", points=[(1.23456, 2.34567)], shape_type="point")]
    )
    precise = LabelMeStore()
    assert "1.23456" in precise.dumps(doc)
    rounded = LabelMeStore(coordinate_precision=2)
    assert "1.23" in rounded.dumps(doc)
    assert "1.23456" not in rounded.dumps(doc)


def test_real_file_round_trip_full_precision() -> None:
    store = LabelMeStore()
    path = Path(__file__).parent / "data" / "sample_labelme.json"
    result = store.load(path)
    assert result.errors == []
    doc2 = store.loads(store.dumps(result.document)).document
    assert doc2 == result.document

