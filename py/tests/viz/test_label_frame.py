# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for label anchor/position computation (``_label_frame.py``)."""

from pytanga.geometry import Direction, Line, Point
from pytanga.geometry.operators import ReflectionLine
from pytanga.viz._label_frame import compute_label_position


class TestLabelPosition:
    def test_finite_line_label_at_midpoint(self):
        pos = compute_label_position(Line.from_points(Point(1, 0, 0), Point(5, 0, 0)))
        assert pos == (3.0, 0.0, 0.0)

    def test_diagonal_line_midpoint(self):
        pos = compute_label_position(Line.from_points(Point(0, 0, 0), Point(2, 2, 0)))
        assert pos == (1.0, 1.0, 0.0)

    def test_infinite_line_label_at_midpoint(self):
        pos = compute_label_position(Line(Point(0, 0, 0), Direction(1, 0, 0)))
        assert pos == (10.0, 0.0, 0.0)

    def test_reflection_line_label_at_midpoint(self):
        rl = ReflectionLine(Line.from_points(Point(0, 0, 0), Point(6, 0, 0)))
        assert compute_label_position(rl) == (3.0, 0.0, 0.0)

    def test_point_label_unchanged(self):
        # A point's local origin IS its position, so the anchor stays (0,0,0).
        assert compute_label_position(Point(3, 3, 3)) == (0.0, 0.0, 0.0)

    def test_viz_line_label_serialized_at_midpoint(self):
        from pytanga.viz import Visualizer

        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        viz.add(Line.from_points(Point(0, 0, 0), Point(4, 0, 0)), label="L")
        labels = [o for o in viz._scene.full_state() if o.get("kind") == "label"]
        assert len(labels) == 1
        assert labels[0]["position"] == [2.0, 0.0, 0.0]

    def test_update_label_recomputes_on_along_change(self):
        from pytanga.viz import Visualizer
        from pytanga.viz._styles import LabelStyle

        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        eid = viz.add(Line.from_points(Point(0, 0, 0), Point(4, 0, 0)), label="L")
        label_id = viz.main_scene.get_label_ids(eid)[0]

        viz.main_scene.update_label(label_id, style=LabelStyle(along=0.0))
        labels = [o for o in viz.main_scene.full_state() if o.get("kind") == "label"]
        assert labels[0]["position"] == [0.0, 0.0, 0.0]

        viz.main_scene.update_label(label_id, style=LabelStyle(along=1.0))
        labels = [o for o in viz.main_scene.full_state() if o.get("kind") == "label"]
        assert labels[0]["position"] == [4.0, 0.0, 0.0]
