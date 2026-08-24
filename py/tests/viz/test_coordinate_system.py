# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the CoordinateSystem plotting helper."""

import math

import numpy as np
import pytest

from pytanga.geometry.entities import Direction, Plane, Point
from pytanga.viz import PointPath, Visualizer
from pytanga.viz._coordinate_system import CoordinateSystem
from pytanga.viz._scale import LinearScale, LogScale
from pytanga.viz.camera import CameraConfig2d, View2DConfig


class TestCoordinateSystem2D:
    def test_auto_span_from_camera(self):
        viz = Visualizer(
            add_default_axes=False,
            add_default_grid=False,
            space_dim=2,
            camera=View2DConfig(xmin=-2.0, xmax=2.0, ymin=-1.0, ymax=1.0),
        )
        cs = CoordinateSystem(viz)
        assert cs.space_dim == 2
        assert cs.xlim == (-2.0, 2.0)
        assert cs.ylim == (-1.0, 1.0)

    def test_default_camera_with_border(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
        CoordinateSystem(
            viz, xlim=(0.1, 100.0), ylim=(0.1, 100.0), xscale="log", yscale="log"
        )
        cam = viz._scenes[""].config.camera
        assert isinstance(cam, CameraConfig2d)
        assert cam.border_px == 60.0
        # span = log10(100) - log10(0.1) = 2 - (-1) = 3
        assert cam.xmin == pytest.approx(-1.5)
        assert cam.xmax == pytest.approx(1.5)

    def test_camera_false_does_not_set(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
        CoordinateSystem(viz, xlim=(-5, 5), ylim=(-5, 5), camera=False)
        assert viz._scenes[""].config.camera is None

    def test_xlim_update_in_place(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
        cs = CoordinateSystem(viz, xlim=(-5, 5), ylim=(-5, 5), camera=False)
        ids_before = {key: ref.id for key, ref in cs._refs.items()}
        cs.xlim = (0.0, 10.0)
        ids_after = {key: ref.id for key, ref in cs._refs.items()}
        assert ids_before == ids_after
        grid = cs._refs["grid"].entity
        assert grid.range_u == (0.0, 10.0)

    def test_log_axes_emit_ticks(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
        cs = CoordinateSystem(
            viz,
            xlim=(0.1, 100),
            ylim=(1, 1000),
            xscale="log",
            yscale="log",
            camera=False,
        )
        x_axis = cs._refs["x"].entity
        labels = [label for _, label in x_axis.ticks]
        assert labels == ["0.1", "1", "10", "100"]
        y_axis = cs._refs["y"].entity
        assert [label for _, label in y_axis.ticks] == ["1", "10", "100", "1000"]

    def test_transform_and_plot(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
        cs = CoordinateSystem(viz, xlim=(0, 10), ylim=(0, 10), camera=False)
        # centred: cx = cy = 5, so local coords are data - 5.
        pts = cs.transform([1, 2], [3, 4])
        flat = [v for p in pts for v in p]
        assert flat == pytest.approx([-4.0, -2.0, 0.0, -3.0, -1.0, 0.0])
        ref = cs.plot([1, 2], [3, 4], color="#ff0000")
        assert ref.id in viz._scenes[""]._nodes

    def test_default_axis_label_styles(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
        cs = CoordinateSystem(
            viz,
            xlim=(0.1, 100),
            ylim=(1, 1000),
            xscale="log",
            yscale="log",
            camera=False,
        )
        axes = {
            d["label"]: d["style"]
            for d in cs.handle.scene.full_state()
            if d.get("kind") == "Axis" and d.get("label")
        }
        # X: value labels below the axis, name label further down.
        assert axes["x"]["value_style"]["align"] == [0.5, 0.0]
        assert axes["x"]["value_style"]["offset_2d"] == [0.0, 6.0]
        assert axes["x"]["label_style"]["offset_2d"] == [0.0, 28.0]
        # Y: value labels left + right-aligned, name label rotated 90°.
        assert axes["y"]["value_style"]["align"] == [1.0, 0.5]
        assert axes["y"]["value_style"]["offset_2d"] == [-8.0, 0.0]
        assert axes["y"]["label_style"]["rotation"] == -90.0

    def test_2d_size_manual_placement_no_camera(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
        cs = CoordinateSystem(
            viz, xlim=(0, 10), ylim=(0, 10), size=(2, 1), position=(1, 0, 0)
        )
        assert viz._scenes[""].config.camera is None
        assert cs.group.transform.position == (1.0, 0.0, 0.0)

    def test_2d_size_up_rotates_plane(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
        cs = CoordinateSystem(
            viz,
            xlim=(0, 10),
            ylim=(0, 10),
            size=(2, 1),
            position=(0, 0, 0),
            up=(1, 0, 0),
        )
        m = cs.group.world_matrix
        # The plot's local +y maps to world +x (the given `up`).
        world_up = m[:3, :3] @ np.array([0.0, 1.0, 0.0])
        assert world_up == pytest.approx(np.array([1.0, 0.0, 0.0]))

    def test_axis_origin(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
        cs = CoordinateSystem(
            viz, xlim=(-5, 5), ylim=(-5, 5), axis_origin=(0, 0), camera=False
        )
        x_axis = cs._refs["x"].entity
        y_axis = cs._refs["y"].entity
        assert x_axis.start[1] == pytest.approx(0.0)  # x-axis crosses at y=0
        assert x_axis.end[1] == pytest.approx(0.0)
        assert y_axis.start[0] == pytest.approx(0.0)  # y-axis crosses at x=0
        assert y_axis.end[0] == pytest.approx(0.0)

    def test_axis_origin_default_spine(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
        cs = CoordinateSystem(viz, xlim=(-5, 5), ylim=(-5, 5), camera=False)
        x_axis = cs._refs["x"].entity
        y_axis = cs._refs["y"].entity
        assert x_axis.start[1] == pytest.approx(-5.0)  # bottom spine
        assert y_axis.start[0] == pytest.approx(-5.0)  # left spine


class TestCoordinateSystem3D:
    def test_plane_and_transform(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=3)
        cs = CoordinateSystem(
            viz,
            xlim=(0, 4),
            ylim=(0, 2),
            position=(1, 2, 3),
            normal=(0, 0, 1),
            up=(0, 1, 0),
            camera=False,
        )
        assert cs.space_dim == 3
        plane = cs._refs["plane"].entity
        assert isinstance(plane, Plane)
        assert plane.span_u.x == pytest.approx(4.0)
        assert plane.span_v.y == pytest.approx(2.0)
        assert cs.group.transform.position == (1.0, 2.0, 3.0)

    def test_normal_orients_group(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=3)
        cs = CoordinateSystem(
            viz,
            xlim=(-1, 1),
            ylim=(-1, 1),
            normal=(1, 0, 0),
            up=(0, 0, 1),
            camera=False,
        )
        m = cs.group.world_matrix
        world_normal = m[:3, :3] @ np.array([0.0, 0.0, 1.0])
        assert world_normal == pytest.approx(np.array([1.0, 0.0, 0.0]))

    def test_3d_does_not_set_camera(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=3)
        CoordinateSystem(viz, xlim=(0, 4), ylim=(0, 2), position=(1, 2, 3))
        assert viz._scenes[""].config.camera is None

    def test_external_size(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=3)
        cs = CoordinateSystem(
            viz,
            xlim=(0.0, 4.0 * math.pi),
            ylim=(-4.0, 3.0),
            size=(2.0, 1.0),
            position=(1, 2, 3),
            camera=False,
        )
        plane = cs._refs["plane"].entity
        # Plane extents are the external size, not the data range.
        assert plane.span_u.x == pytest.approx(2.0)
        assert plane.span_v.y == pytest.approx(1.0)
        # Data max x (4π) maps to the right edge of the 2-wide plane.
        lx, ly = cs.to_local(4.0 * math.pi, 0.0)
        assert lx == pytest.approx(1.0)
        assert ly == pytest.approx(4.0 / 7.0 - 0.5)

    def test_to_world_applies_group_transform(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=3)
        cs = CoordinateSystem(
            viz,
            xlim=(-1, 1),
            ylim=(-1, 1),
            position=(1, 2, 3),
            normal=(0, 0, 1),
            up=(0, 1, 0),
            camera=False,
        )
        # The data centre (0, 0) maps to the plane centre = `position`.
        assert cs.to_world(0.0, 0.0) == pytest.approx((1.0, 2.0, 3.0))

    def test_align_bottom_left(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=3)
        cs = CoordinateSystem(
            viz,
            xlim=(0, 4),
            ylim=(0, 2),
            size=(2, 1),
            align=(0.0, 0.0),
            position=(1, 2, 3),
            camera=False,
        )
        # Bottom-left corner (data 0, 0) sits at `position`.
        assert cs.to_world(0.0, 0.0) == pytest.approx((1.0, 2.0, 3.0))
        # Top-right corner sits at position + (2, 1) in the plane.
        assert cs.to_world(4.0, 2.0) == pytest.approx((3.0, 3.0, 3.0))

    def test_align_top_right(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=3)
        cs = CoordinateSystem(
            viz,
            xlim=(0, 4),
            ylim=(0, 2),
            size=(2, 1),
            align=(1.0, 1.0),
            position=(1, 2, 3),
            camera=False,
        )
        assert cs.to_world(4.0, 2.0) == pytest.approx((1.0, 2.0, 3.0))

    def test_position_accepts_point_and_direction(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=3)
        cs = CoordinateSystem(
            viz,
            xlim=(0, 4),
            ylim=(0, 2),
            size=(2, 1),
            position=Point(1, 2, 3),
            normal=Direction(0, 0, 1),
            up=(0, 1, 0),
            camera=False,
        )
        assert cs.group.transform.position == (1.0, 2.0, 3.0)
        # The data centre (2, 1) maps to the plane centre = `position`.
        assert cs.to_world(2.0, 1.0) == pytest.approx((1.0, 2.0, 3.0))


class TestCoordinateSystemPlots:
    def test_add_plot_and_update(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=3)
        cs = CoordinateSystem(
            viz,
            xlim=(0, 10),
            ylim=(-2, 2),
            size=(2, 1),
            position=(1, 2, 3),
            camera=False,
        )
        path = PointPath()
        path.add((0.0, 0.0))
        path.add((1.0, 1.0))
        ref = cs.add_plot(path, color="#ffcc00", auto_x=True)
        # Min span 5 centred on [0, 1] → [-2, 3].
        assert cs.xlim == pytest.approx((-2.0, 3.0))
        path.add((9.0, -1.0))
        cs.update_plots()
        assert cs.xlim == pytest.approx((0.0, 9.0))
        render = ref.entity
        assert len(render.points) == 3
        # x = 9 maps to the right edge of the 2-wide plane.
        assert render.points[-1][0] == pytest.approx(1.0)

    def test_add_plot_without_auto_x_keeps_xlim(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
        cs = CoordinateSystem(viz, xlim=(-5, 5), ylim=(-5, 5), camera=False)
        path = PointPath()
        path.add((0.0, 0.0))
        cs.add_plot(path, color="#ff0000", auto_x=False)
        path.add((100.0, 0.0))
        cs.update_plots()
        assert cs.xlim == (-5.0, 5.0)


class TestCoordinateSystemScales:
    def test_scale_types(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
        cs = CoordinateSystem(
            viz, xlim=(1, 100), ylim=(1, 100), xscale="log", camera=False
        )
        assert isinstance(cs.xscale, LogScale)
        assert isinstance(cs.yscale, LinearScale)
        cs.xscale = "linear"
        assert isinstance(cs.xscale, LinearScale)
