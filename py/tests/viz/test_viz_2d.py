# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Phase 7.6 tests — 2D visualization integration tests.

Tests Visualizer, SceneConfig, FigureConfig, and VisualizerApp with space_dim=2.
"""

from __future__ import annotations

import json

import pytest
from pytanga.geometry.entities import Direction, Line, Point
from pytanga.viz._figure import FigureConfig
from pytanga.viz.scene import SceneConfig
from pytanga.viz.visualizer import Visualizer


class TestSceneConfig2D:
    def test_space_dim_in_to_dict(self):
        sc = SceneConfig()
        d = sc.to_dict()
        assert d["space_dim"] == 3  # default

    def test_explicit_space_dim_2(self):
        from pytanga.viz.scene import SceneConfig

        sc = SceneConfig()
        sc.space_dim = 2
        d = sc.to_dict()
        assert d["space_dim"] == 2

    def test_json_serializable_2d(self):
        sc = SceneConfig()
        sc.space_dim = 2
        json.dumps(sc.to_dict())


class TestVisualizer2D:
    def test_construction_with_space_dim(self):
        viz = Visualizer(space_dim=2)
        assert viz._config.space_dim == 2

    def test_default_title_2d(self):
        viz = Visualizer(space_dim=2)
        assert viz._config.title == "Tanga 2D Viewer"

    def test_custom_title_preserved(self):
        viz = Visualizer(title="My 2D", space_dim=2)
        assert viz._config.title == "My 2D"

    def test_add_point_returns_id(self):
        viz = Visualizer(space_dim=2)
        eid = viz.add(Point(3, 4, 0))
        assert isinstance(eid, str)

    def test_add_direction_returns_id(self):
        viz = Visualizer(space_dim=2)
        eid = viz.add(Direction(1, 0, 0))
        assert isinstance(eid, str)

    def test_add_line_returns_id(self):
        viz = Visualizer(space_dim=2)
        eid = viz.add(Line(Point(0, 0, 0), Direction(1, 0, 0)))
        assert isinstance(eid, str)

    def test_entity_serializes_with_z_zero(self):
        viz = Visualizer(space_dim=2, add_default_axes=False, add_default_grid=False)
        viz.add(Point(3, 4, 0))
        dirty, _ = viz._scene.flush()
        assert dirty[0]["position"] == [3, 4, 0]

    def test_main_scene_has_space_dim(self):
        viz = Visualizer(space_dim=2)
        assert viz.main_scene.config.space_dim == 2

    def test_sub_scene_inherits_space_dim(self):
        viz = Visualizer(space_dim=2)
        sub = viz.scene("sub")
        assert sub.scene.config.space_dim == 2

    def test_sub_scene_omits_space_dim_when_default(self):
        viz = Visualizer()
        sub = viz.scene("sub")
        d = sub.scene.config.to_dict()
        assert d.get("space_dim", 3) == 3


class TestFigureConfig2D:
    def test_default_space_dim(self):
        fc = FigureConfig()
        assert fc.space_dim == 3

    def test_explicit_space_dim_2(self):
        fc = FigureConfig(space_dim=2)
        assert fc.space_dim == 2

    def test_to_dict_includes_space_dim(self):
        fc = FigureConfig(space_dim=2)
        d = fc.to_dict()
        assert d["space_dim"] == 2

    def test_json_serializable(self):
        fc = FigureConfig(space_dim=2)
        json.dumps(fc.to_dict())
