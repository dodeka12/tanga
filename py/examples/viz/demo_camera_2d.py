# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""demo_camera_2d.py — 2D orthographic view via View2DConfig.

Specifies a rectangular viewport with a custom extent and centre point,
then plots a few points inside it.

Run with:  uv run python py/examples/viz/demo_camera_2d.py
"""

from pytanga.geometry import Point
from pytanga.viz import CameraConfig, PointStyle, View2DConfig, Visualizer

viz = Visualizer(
    title="Tanga — 2D Camera (View2DConfig)",
    camera=CameraConfig(
        view_2d=View2DConfig(extent_x=8.0, extent_y=6.0, center=(0.0, 0.0))
    ),
    space_dim=2,
)

viz.add(Point(2, 1, 0), color="#ff4444", style=PointStyle(size=0.15), label="$P_1$")
viz.add(Point(-1, 2, 0), color="#44ff44", style=PointStyle(size=0.15), label="$P_2$")
viz.add(Point(0, -2, 0), color="#4444ff", style=PointStyle(size=0.15), label="$P_3$")

viz.run()