# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the `Rectangle2D` entity + `Rectangle2DStyle` + serializer."""

from __future__ import annotations

import pytest

from pytanga.geometry import Point, Rectangle2D
from pytanga.viz import Rectangle2DStyle
from pytanga.viz.serializer import serialize_entity


def test_rectangle2d_defaults() -> None:
    rect = Rectangle2D()
    assert (rect.center.x, rect.center.y, rect.center.z) == (0.0, 0.0, 0.0)
    assert rect.size == (1.0, 1.0)
    assert (rect.normal.x, rect.normal.y, rect.normal.z) == (0.0, 0.0, 1.0)
    assert rect.angle == 0.0


def test_rectangle2d_coerces_center_and_size() -> None:
    rect = Rectangle2D(center=Point(1.0, 2.0, 0.0), size=[10, 4])
    assert (rect.center.x, rect.center.y) == (1.0, 2.0)
    assert rect.size == (10.0, 4.0)


def test_rectangle2d_rejects_bad_size() -> None:
    with pytest.raises(TypeError):
        Rectangle2D(size=(1.0, 2.0, 3.0))


def test_rectangle2d_serializes() -> None:
    result = serialize_entity(
        Rectangle2D(center=Point(3.0, 5.0, 0.0), size=(8.0, 6.0)), "r1"
    )
    assert result["kind"] == "Rectangle2D"
    assert result["center"] == [3.0, 5.0, 0.0]
    assert result["size"] == [8.0, 6.0]
    assert result["normal"] == [0.0, 0.0, 1.0]
    assert result["angle"] == 0.0


def test_rectangle2d_style_to_dict() -> None:
    assert Rectangle2DStyle().to_dict() == {"style_type": "Rectangle2DStyle"}
    assert Rectangle2DStyle(fill=True, fill_opacity=0.2, thickness=3).to_dict() == {
        "style_type": "Rectangle2DStyle",
        "fill": True,
        "fill_opacity": 0.2,
        "thickness": 3,
    }


def test_rectangle2d_style_round_trips_through_entity() -> None:
    result = serialize_entity(
        Rectangle2D(size=(4.0, 2.0)),
        "r1",
        {"style": Rectangle2DStyle(fill=True, fill_opacity=0.25)},
    )
    assert result["style"]["style_type"] == "Rectangle2DStyle"
    assert result["style"]["fill"] is True
    assert result["style"]["fill_opacity"] == 0.25


def test_rectangle2d_between() -> None:
    a = Point(10.0, 20.0, 0.0)
    b = Point(2.0, 8.0, 0.0)
    rect = Rectangle2D.between(a, b)
    assert rect.center == Point(6.0, 14.0, 0.0)
    assert rect.size == (8.0, 12.0)
    # Corner order does not matter.
    assert Rectangle2D.between(b, a) == rect
