# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for `SquarePointStyle` (square `Point` marker)."""

from __future__ import annotations

from pytanga.geometry import Point
from pytanga.viz import SquarePointStyle
from pytanga.viz.serializer import serialize_entity


def test_square_point_style_defaults_to_dict() -> None:
    assert SquarePointStyle().to_dict() == {"style_type": "SquarePointStyle"}


def test_square_point_style_fields() -> None:
    style = SquarePointStyle(color="#ffffff", opacity=1.0, size=4.0, thickness=0.5)
    assert style.to_dict() == {
        "style_type": "SquarePointStyle",
        "color": "#ffffff",
        "opacity": 1.0,
        "size": 4.0,
        "thickness": 0.5,
    }


def test_square_point_style_round_trips_through_point_entity() -> None:
    result = serialize_entity(
        Point(1.0, 2.0, 0.0),
        "pt1",
        {"style": SquarePointStyle(size=4.0, thickness=0.5)},
    )
    assert result["style"]["style_type"] == "SquarePointStyle"
    assert result["style"]["size"] == 4.0
    assert result["style"]["thickness"] == 0.5
