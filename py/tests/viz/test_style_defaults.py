# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the bundled style-defaults holder (`_style_defaults.py`)."""

from pytanga.geometry.entities import Point
from pytanga.viz._style_defaults import VizStyleDefaults, make_defaults
from pytanga.viz._style_dict import _StyleDict
from pytanga.viz.scene import Scene
from pytanga.viz.visualizer import Visualizer


def test_make_defaults_has_all_fields():
    d = make_defaults()
    assert d.default_styles is not None
    assert d.default_label_style is not None
    assert d.default_label_styles is not None
    assert d.default_annotation_style is not None
    assert d.default_tex_label_style is not None
    assert d.default_tex_label_styles is not None
    # Per-kind styles are populated.
    assert "Point" in d.default_styles
    assert d.default_styles["Point"].color is not None


def test_copy_is_deep():
    d = make_defaults()
    c = d.copy()
    # Mutating the copy's nested per-kind style leaves the original untouched.
    c.default_styles["Point"].color = "#000000"
    assert d.default_styles["Point"].color != "#000000"


def test_scene_receives_independent_copy():
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    scene = viz.main_scene

    # Scene holds its own holder, independent of the Visualizer's.
    assert scene.style_defaults is not viz._style_defaults
    scene.default_styles["Point"].color = "#000000"
    assert viz.default_styles["Point"].color != "#000000"

    # And mutating the Visualizer holder doesn't change the scene's copy.
    viz.default_styles["Point"].color = "#111111"
    assert scene.default_styles["Point"].color == "#000000"


def test_scene_default_fallback():
    s = Scene()
    assert isinstance(s.style_defaults, VizStyleDefaults)
    assert "Point" in s.default_styles


def test_visualizer_backcompat_properties():
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    assert isinstance(viz.default_styles, _StyleDict)
    assert viz.default_styles[Point].color is not None
    assert viz.default_label_style.color is not None
    assert isinstance(viz.default_label_styles, _StyleDict)
    assert viz.default_annotation_style.color is not None
    assert isinstance(viz.default_tex_label_style, _StyleDict)