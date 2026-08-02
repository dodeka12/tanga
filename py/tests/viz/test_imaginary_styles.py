# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for imaginary entity subclass dataclasses and their default styles.

Tests all three imaginary entities (ImagCircle, ImagSphere, ImagPointPair)
and their integration with the Visualizer style system.
"""

from copy import copy

import pytest
from pytanga.geometry import (
    Circle,
    Direction,
    ImagCircle,
    ImagPointPair,
    ImagSphere,
    Point,
    PointPair,
    Sphere,
)
from pytanga.viz._style_dict import _kind_to_key, _make_default_styles
from pytanga.viz._styles import (
    _DEFAULT_STYLE_FOR_KIND,
    CircleStyle,
    PointPairStyle,
    SphereStyle,
)
from pytanga.viz.serializer import (
    _serialize_circle,
    _serialize_point_pair,
    _serialize_sphere,
)

# ── Helpers ────────────────────────────────────────────────


def _styles_map():
    """Return a fresh copy of canonical defaults."""
    return {k: copy(v) for k, v in _DEFAULT_STYLE_FOR_KIND.items()}


# ── Subclass construction ──────────────────────────────────


class TestImagEntityConstruction:
    def test_imag_circle_default_is_imaginary(self):
        c = ImagCircle(center=Point(0, 0, 0), normal=Direction(0, 0, 1), radius=2.0)
        assert c.is_imaginary is True

    def test_imag_sphere_default_is_imaginary(self):
        s = ImagSphere(center=Point(0, 0, 0), radius=1.0)
        assert s.is_imaginary is True

    def test_imag_point_pair_default_is_imaginary(self):
        pp = ImagPointPair(point_a=Point(0, 0, 0), point_b=Point(1, 0, 0))
        assert pp.is_imaginary is True

    def test_imag_circle_isinstance_of_circle(self):
        c = ImagCircle(center=Point(0, 0, 0), normal=Direction(0, 0, 1), radius=2.0)
        assert isinstance(c, Circle)

    def test_imag_sphere_isinstance_of_sphere(self):
        s = ImagSphere(center=Point(0, 0, 0), radius=1.0)
        assert isinstance(s, Sphere)

    def test_imag_point_pair_isinstance_of_point_pair(self):
        pp = ImagPointPair(point_a=Point(0, 0, 0), point_b=Point(1, 0, 0))
        assert isinstance(pp, PointPair)

    def test_imag_circle_fields_preserved(self):
        c = ImagCircle(center=Point(1, 2, 3), normal=Direction(0, 0, 1), radius=5.0)
        assert c.center == Point(1, 2, 3)
        assert c.normal == Direction(0, 0, 1)
        assert c.radius == 5.0

    def test_imag_sphere_fields_preserved(self):
        s = ImagSphere(center=Point(4, 5, 6), radius=3.5)
        assert s.center == Point(4, 5, 6)
        assert s.radius == 3.5

    def test_base_circle_is_imaginary_false_by_default(self):
        c = Circle(center=Point(0, 0, 0), normal=Direction(0, 0, 1), radius=2.0)
        assert c.is_imaginary is False


# ── Canonical style defaults ───────────────────────────────


class TestCanonicalDefaults:
    def test_imag_circle_has_style_entry(self):
        assert "ImagCircle" in _DEFAULT_STYLE_FOR_KIND
        style = _DEFAULT_STYLE_FOR_KIND["ImagCircle"]
        assert isinstance(style, CircleStyle)

    def test_imag_sphere_has_style_entry(self):
        assert "ImagSphere" in _DEFAULT_STYLE_FOR_KIND
        style = _DEFAULT_STYLE_FOR_KIND["ImagSphere"]
        assert isinstance(style, SphereStyle)

    def test_imag_point_pair_has_style_entry(self):
        assert "ImagPointPair" in _DEFAULT_STYLE_FOR_KIND
        style = _DEFAULT_STYLE_FOR_KIND["ImagPointPair"]
        assert isinstance(style, PointPairStyle)

    def test_real_and_imag_circle_colors_differ(self):
        real = _DEFAULT_STYLE_FOR_KIND["Circle"]
        imag = _DEFAULT_STYLE_FOR_KIND["ImagCircle"]
        assert real.color != imag.color

    def test_real_and_imag_sphere_colors_differ(self):
        real = _DEFAULT_STYLE_FOR_KIND["Sphere"]
        imag = _DEFAULT_STYLE_FOR_KIND["ImagSphere"]
        assert real.color != imag.color

    def test_real_and_imag_point_pair_colors_differ(self):
        real = _DEFAULT_STYLE_FOR_KIND["PointPair"]
        imag = _DEFAULT_STYLE_FOR_KIND["ImagPointPair"]
        assert real.color != imag.color


# ── _StyleDict class-key access ────────────────────────────


class TestStyleDictClassKeys:
    def test_style_dict_contains_imag_circle(self):
        styles = _make_default_styles()
        assert "ImagCircle" in styles

    def test_style_dict_access_by_class(self):
        styles = _make_default_styles()
        assert styles[ImagCircle].color == _DEFAULT_STYLE_FOR_KIND["ImagCircle"].color

    def test_style_dict_access_by_string(self):
        styles = _make_default_styles()
        assert styles["ImagCircle"].color == _DEFAULT_STYLE_FOR_KIND["ImagCircle"].color

    def test_style_dict_set_by_class(self):
        styles = _make_default_styles()
        styles[ImagCircle] = CircleStyle(color="#ff00ff")
        assert styles["ImagCircle"].color == "#ff00ff"

    def test_style_dict_set_by_string(self):
        styles = _make_default_styles()
        styles["ImagCircle"] = CircleStyle(color="#00ffff")
        assert styles[ImagCircle].color == "#00ffff"

    def test_style_dict_class_access_imag_sphere(self):
        styles = _make_default_styles()
        assert styles[ImagSphere].color == _DEFAULT_STYLE_FOR_KIND["ImagSphere"].color

    def test_style_dict_class_access_imag_point_pair(self):
        styles = _make_default_styles()
        assert (
            styles[ImagPointPair].color
            == _DEFAULT_STYLE_FOR_KIND["ImagPointPair"].color
        )


# ── _kind_to_key mapping ───────────────────────────────────


class TestKindToKey:
    def test_imag_circle_kind(self):
        assert _kind_to_key("imagcircle") == "ImagCircle"

    def test_imag_sphere_kind(self):
        assert _kind_to_key("imagsphere") == "ImagSphere"

    def test_imag_point_pair_kind(self):
        assert _kind_to_key("imagpointpair") == "ImagPointPair"

    def test_real_kinds_still_work(self):
        assert _kind_to_key("circle") == "Circle"
        assert _kind_to_key("sphere") == "Sphere"
        assert _kind_to_key("point_pair") == "PointPair"

    def test_unknown_kind_raises(self):
        with pytest.raises(ValueError, match="Unknown entity kind"):
            _kind_to_key("nonexistent")


# ── Serializer remapping ───────────────────────────────────


class TestSerializerRemapping:
    def test_real_circle_kind_is_circle(self):
        c = Circle(center=Point(0, 0, 0), normal=Direction(0, 0, 1), radius=2.0)
        d = _serialize_circle(c, {}, kind="Circle", styles_map=_styles_map())
        assert d["kind"] == "Circle"
        assert d["isImaginary"] is False

    def test_imag_circle_kind_is_overridden_to_circle(self):
        c = Circle(
            center=Point(0, 0, 0),
            normal=Direction(0, 0, 1),
            radius=2.0,
            is_imaginary=True,
        )
        d = _serialize_circle(c, {}, kind="Circle", styles_map=_styles_map())
        assert d["kind"] == "Circle"
        assert d["isImaginary"] is True

    def test_real_circle_gets_real_defaults(self):
        c = Circle(center=Point(0, 0, 0), normal=Direction(0, 0, 1), radius=2.0)
        d = _serialize_circle(c, {}, kind="Circle", styles_map=_styles_map())
        assert d["style"]["color"] == _DEFAULT_STYLE_FOR_KIND["Circle"].color

    def test_imag_circle_gets_imag_defaults(self):
        c = Circle(
            center=Point(0, 0, 0),
            normal=Direction(0, 0, 1),
            radius=2.0,
            is_imaginary=True,
        )
        d = _serialize_circle(c, {}, kind="Circle", styles_map=_styles_map())
        assert d["style"]["color"] == _DEFAULT_STYLE_FOR_KIND["ImagCircle"].color

    def test_imag_circle_style_differs_from_real(self):
        real = Circle(center=Point(0, 0, 0), normal=Direction(0, 0, 1), radius=2.0)
        imag = Circle(
            center=Point(0, 0, 0),
            normal=Direction(0, 0, 1),
            radius=2.0,
            is_imaginary=True,
        )
        real_d = _serialize_circle(real, {}, kind="Circle", styles_map=_styles_map())
        imag_d = _serialize_circle(imag, {}, kind="Circle", styles_map=_styles_map())
        assert real_d["style"]["color"] != imag_d["style"]["color"]

    def test_real_sphere_kind_is_sphere(self):
        s = Sphere(center=Point(0, 0, 0), radius=1.0)
        d = _serialize_sphere(s, {}, kind="Sphere", styles_map=_styles_map())
        assert d["kind"] == "Sphere"
        assert d["isImaginary"] is False

    def test_imag_sphere_kind_is_overridden_to_sphere(self):
        s = Sphere(center=Point(0, 0, 0), radius=1.0, is_imaginary=True)
        d = _serialize_sphere(s, {}, kind="Sphere", styles_map=_styles_map())
        assert d["kind"] == "Sphere"
        assert d["isImaginary"] is True

    def test_imag_sphere_gets_imag_defaults(self):
        s = Sphere(center=Point(0, 0, 0), radius=1.0, is_imaginary=True)
        d = _serialize_sphere(s, {}, kind="Sphere", styles_map=_styles_map())
        assert d["style"]["color"] == _DEFAULT_STYLE_FOR_KIND["ImagSphere"].color

    def test_imag_sphere_style_differs_from_real(self):
        real = Sphere(center=Point(0, 0, 0), radius=1.0)
        imag = Sphere(center=Point(0, 0, 0), radius=1.0, is_imaginary=True)
        real_d = _serialize_sphere(real, {}, kind="Sphere", styles_map=_styles_map())
        imag_d = _serialize_sphere(imag, {}, kind="Sphere", styles_map=_styles_map())
        assert real_d["style"]["color"] != imag_d["style"]["color"]

    def test_real_point_pair_kind_is_point_pair(self):
        pp = PointPair(point_a=Point(0, 0, 0), point_b=Point(1, 0, 0))
        d = _serialize_point_pair(pp, {}, kind="PointPair", styles_map=_styles_map())
        assert d["kind"] == "PointPair"
        assert d["isImaginary"] is False

    def test_imag_point_pair_kind_is_overridden_to_point_pair(self):
        pp = PointPair(
            point_a=Point(0, 0, 0),
            point_b=Point(1, 0, 0),
            is_imaginary=True,
        )
        d = _serialize_point_pair(pp, {}, kind="PointPair", styles_map=_styles_map())
        assert d["kind"] == "PointPair"
        assert d["isImaginary"] is True

    def test_imag_point_pair_gets_imag_defaults(self):
        pp = PointPair(
            point_a=Point(0, 0, 0),
            point_b=Point(1, 0, 0),
            is_imaginary=True,
        )
        d = _serialize_point_pair(pp, {}, kind="PointPair", styles_map=_styles_map())
        assert d["style"]["color"] == _DEFAULT_STYLE_FOR_KIND["ImagPointPair"].color


# ── Visualizer integration ─────────────────────────────────


class TestVisualizerIntegration:
    def test_set_default_color_imag_circle(self):
        from pytanga.viz import Visualizer

        viz = Visualizer()
        viz.set_default_color("imagcircle", "#ff0000")
        assert viz.default_styles["ImagCircle"].color == "#ff0000"

    def test_set_default_color_imag_sphere(self):
        from pytanga.viz import Visualizer

        viz = Visualizer()
        viz.set_default_color("imagsphere", "#00ff00")
        assert viz.default_styles["ImagSphere"].color == "#00ff00"

    def test_set_default_color_imag_point_pair(self):
        from pytanga.viz import Visualizer

        viz = Visualizer()
        viz.set_default_color("imagpointpair", "#0000ff")
        assert viz.default_styles["ImagPointPair"].color == "#0000ff"

    def test_set_default_color_imag_circle_with_alpha(self):
        from pytanga.viz import Visualizer

        viz = Visualizer()
        viz.set_default_color("imagcircle", (1.0, 0, 0, 0.5))
        assert viz.default_styles["ImagCircle"].color == "#ff0000"
        assert viz.default_styles["ImagCircle"].opacity == 0.5

    def test_default_styles_contains_imag_kinds(self):
        from pytanga.viz import Visualizer

        viz = Visualizer()
        assert "ImagCircle" in viz.default_styles
        assert "ImagSphere" in viz.default_styles
        assert "ImagPointPair" in viz.default_styles

    def test_real_and_imag_defaults_independent(self):
        from pytanga.viz import Visualizer

        viz = Visualizer()
        viz.set_default_color("circle", "#111111")
        viz.set_default_color("imagcircle", "#222222")
        assert viz.default_styles["Circle"].color == "#111111"
        assert viz.default_styles["ImagCircle"].color == "#222222"

    def test_mutating_real_does_not_affect_imag(self):
        from pytanga.viz import Visualizer

        viz = Visualizer()
        original_imag = viz.default_styles["ImagCircle"].color
        viz.default_styles["Circle"].color = "#000000"
        assert viz.default_styles["ImagCircle"].color == original_imag

    def test_imag_sphere_wireframe_default(self):
        from pytanga.viz import Visualizer

        viz = Visualizer()
        assert viz.default_styles["ImagSphere"].wireframe is True
        assert viz.default_styles["ImagSphere"].wireframe is True
