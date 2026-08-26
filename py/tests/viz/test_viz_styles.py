# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the unified style holder (`_viz_styles.py`)."""

from pytanga.geometry import (
    Arc,
    Box,
    Cylinder,
    Direction,
    Disk,
    Ellipse,
    Ellipsoid,
    Line,
    PartialDisk,
    Point,
    RegularPolygon,
)
from pytanga.viz import (
    ArcStyle,
    BoxStyle,
    CylinderLineStyle,
    CylinderStyle,
    DiskStyle,
    EllipseStyle,
    EllipsoidStyle,
    LabelStyle,
    LineStyle,
    PartialDiskStyle,
    PointStyle,
    RegularPolygonStyle,
    Visualizer,
)
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


# ── Visualizer wiring ────────────────────────────────────────


def test_viz_styles_is_main_scene_holder():
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    assert viz.styles is viz.main_scene.styles


def test_viz_styles_mutation_affects_new_entity():
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    viz.styles["Line"] = CylinderLineStyle(thickness=0.05)
    viz.add(Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0)))
    line = [o for o in viz.main_scene.full_state() if o.get("kind") == "Line"][0]
    assert line["style"]["style_type"] == "CylinderLineStyle"
    assert line["style"]["thickness"] == 0.05


def test_global_styles_independent_of_main_scene():
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    viz.styles["Line"] = CylinderLineStyle(thickness=0.05)
    assert isinstance(viz.global_styles["Line"], LineStyle)


def test_new_scene_copies_global_styles():
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    viz.global_styles["Line"] = CylinderLineStyle(thickness=0.07)
    detail = viz.scene("detail")
    assert isinstance(detail.styles["Line"], CylinderLineStyle)
    assert isinstance(viz.styles["Line"], LineStyle)


def test_named_scene_styles_independent():
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    detail = viz.scene("detail")
    detail.styles["Point"].color = "#000000"
    assert viz.styles["Point"].color != "#000000"


# ── Viz-only entities (Cylinder / Arc) ────────────────────────


def test_viz_entity_style_defaults_registered():
    s = make_styles()
    assert "Cylinder" in s.kind
    assert "Arc" in s.kind
    assert s.kind["Cylinder"].color is not None
    assert s.kind["Arc"].color is not None


def test_cylinder_style_to_dict_omits_unset_fields():
    d = CylinderStyle(color="#123456").to_dict()
    assert d["style_type"] == "CylinderStyle"
    assert d["color"] == "#123456"
    assert "opacity" not in d


def test_arc_style_to_dict_omits_unset_fields():
    d = ArcStyle(color="#123456").to_dict()
    assert d["style_type"] == "ArcStyle"
    assert d["color"] == "#123456"
    assert "opacity" not in d


def test_viz_entity_style_class_key_access():
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    assert viz.styles[Cylinder] is viz.styles["Cylinder"]
    assert viz.styles[Arc] is viz.styles["Arc"]


def test_new_entity_style_defaults_registered() -> None:
    s = make_styles()
    for kind in ("Disk", "PartialDisk", "Box", "Ellipsoid", "Ellipse", "RegularPolygon"):
        assert kind in s.kind
        assert s.kind[kind].color is not None


def test_new_entity_style_to_dict_omits_unset_fields() -> None:
    assert DiskStyle(color="#123456").to_dict() == {
        "style_type": "DiskStyle",
        "color": "#123456",
    }
    assert BoxStyle(color="#123456").to_dict() == {
        "style_type": "BoxStyle",
        "color": "#123456",
    }


def test_new_entity_style_thickness_serialized() -> None:
    assert PartialDiskStyle(thickness=0.05).to_dict()["thickness"] == 0.05
    assert EllipseStyle(thickness=0.05).to_dict()["thickness"] == 0.05
    assert RegularPolygonStyle(thickness=0.05).to_dict()["thickness"] == 0.05


def test_new_entity_style_class_key_access() -> None:
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    for entity in (Disk, PartialDisk, Box, Ellipsoid, Ellipse, RegularPolygon):
        assert viz.styles[entity] is viz.styles[entity.__name__]
