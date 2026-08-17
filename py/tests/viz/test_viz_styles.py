# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the unified style holder (`_viz_styles.py`)."""

from pytanga.geometry.entities import Point
from pytanga.viz import LabelStyle, PointStyle
from pytanga.viz._style_dict import _StyleDict
from pytanga.viz._viz_styles import VizStyles, make_styles


def test_make_styles_has_all_members():
    s = make_styles()
    assert isinstance(s, VizStyles)
    assert isinstance(s.kind, _StyleDict)
    assert isinstance(s.label_kind, _StyleDict)
    assert isinstance(s.tex_label_kind, _StyleDict)
    assert s.label_base is not None
    assert s.annotation is not None
    assert s.tex_label_base is not None
    assert s.act_point is not None
    # Per-kind entity styles are populated.
    assert "Point" in s.kind
    assert s.kind["Point"].color is not None


def test_getitem_delegates_to_kind():
    s = make_styles()
    assert s["Point"] is s.kind["Point"]
    assert s[Point] is s.kind[Point]


def test_setitem_delegates_to_kind():
    s = make_styles()
    style = PointStyle(size=0.25, color="#123456")
    s["Point"] = style
    assert s.kind["Point"] is style
    s[Point] = style
    assert s.kind[Point] is style


def test_label_kind_class_key():
    s = make_styles()
    s.label_kind[Point] = LabelStyle(font_size=18)
    assert s.label_kind["Point"].font_size == 18


def test_copy_is_deep():
    s = make_styles()
    c = s.copy()
    c.kind["Point"].color = "#000000"
    assert s.kind["Point"].color != "#000000"
    c.label_base.color = "#111111"
    assert s.label_base.color != "#111111"
    c.act_point.hover_emissive = "#000000"
    assert s.act_point.hover_emissive != "#000000"


def test_act_point_default():
    s = make_styles()
    assert s.act_point.hover_emissive == "#ffff44"
    assert s.act_point.hover_scale == 1.5
