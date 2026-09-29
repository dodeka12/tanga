# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for `CirclePointStyle` and `IconPointStyle` (Point marker variants)."""

from __future__ import annotations

from pytanga.geometry import Point
from pytanga.viz import CirclePointStyle, IconPointStyle
from pytanga.viz.serializer import serialize_entity


def test_circle_point_style_defaults_to_dict() -> None:
    assert CirclePointStyle().to_dict() == {"style_type": "CirclePointStyle"}


def test_circle_point_style_fields() -> None:
    style = CirclePointStyle(
        color="#ffffff",
        opacity=1.0,
        size=4.0,
        thickness=0.5,
        filled=False,
        fill_opacity=0.2,
    )
    assert style.to_dict() == {
        "style_type": "CirclePointStyle",
        "color": "#ffffff",
        "opacity": 1.0,
        "size": 4.0,
        "thickness": 0.5,
        "filled": False,
        "fill_opacity": 0.2,
    }


def test_icon_point_style_defaults_to_dict() -> None:
    assert IconPointStyle().to_dict() == {"style_type": "IconPointStyle"}


def test_icon_point_style_fields() -> None:
    style = IconPointStyle(color="#ffffff", size=4.0, icon="material:open_with")
    assert style.to_dict() == {
        "style_type": "IconPointStyle",
        "color": "#ffffff",
        "size": 4.0,
        "icon": "material:open_with",
    }


def test_circle_point_style_round_trips_through_point_entity() -> None:
    result = serialize_entity(
        Point(1.0, 2.0, 0.0),
        "pt1",
        {"style": CirclePointStyle(size=4.0, filled=True)},
    )
    assert result["style"]["style_type"] == "CirclePointStyle"
    assert result["style"]["size"] == 4.0
    assert result["style"]["filled"] is True


def test_icon_point_style_round_trips_through_point_entity() -> None:
    result = serialize_entity(
        Point(1.0, 2.0, 0.0),
        "pt1",
        {"style": IconPointStyle(icon="material:rotate_right")},
    )
    assert result["style"]["style_type"] == "IconPointStyle"
    assert result["style"]["icon"] == "material:rotate_right"


def test_circle_point_style_screen_space() -> None:
    assert CirclePointStyle(size=4.0, screen_space=True).to_dict() == {
        "style_type": "CirclePointStyle",
        "size": 4.0,
        "screen_space": True,
    }


def test_icon_point_style_screen_space() -> None:
    assert IconPointStyle(size=4.0, screen_space=True).to_dict() == {
        "style_type": "IconPointStyle",
        "size": 4.0,
        "screen_space": True,
    }
