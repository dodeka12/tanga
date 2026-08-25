# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""axes_grid_2d.py — 2D camera, axes, and grid basics.

A minimal introduction to the three core 2D scene-building blocks:

* :class:`~pytanga.viz.View2DConfig` — an orthographic camera view defined
  by a visible world rectangle (min/max bounds).
* :class:`~pytanga.viz.Axes2D` — the two coordinate axes, controlled via a
  single convenience object.
* :class:`~pytanga.viz.Grid` — a coordinate grid in the XY plane.

Run with:  uv run python py/examples/viz/camera/axes_grid_2d.py
"""

from pytanga.geometry import Point
from pytanga.viz import (
    Axes2D,
    Axes2DStyle,
    AxisStyle,
    Grid,
    GridStyle,
    PointStyle,
    View2DConfig,
    Visualizer,
)

# 1. Camera: orthographic view of an 8×6 rectangle centred at the origin.
viz = Visualizer(
    title="Tanga — 2D Camera, Axes & Grid",
    camera=View2DConfig(xmin=-4.0, xmax=4.0, ymin=-3.0, ymax=3.0),
)

# 2. Axes: X and Y axes spanning the same extent as the camera view.
#    Each direction gets its own AxisStyle via Axes2DStyle.
viz.new(
    Axes2D(
        origin=(0.0, 0.0),
        dir_u=(1.0, 0.0, 0.0),
        dir_v=(0.0, 1.0, 0.0),
        range_u=(-4.0, 4.0),
        range_v=(-3.0, 3.0),
        major_interval=1.0,
        labels=("X", "Y"),
    ),
    style=Axes2DStyle(
        u=AxisStyle(color="#ff6666", opacity=0.9),
        v=AxisStyle(color="#6666ff", opacity=0.9),
    ),
)

# 3. Grid: unit-spaced lines across the full 8×6 view rectangle.
viz.new(
    Grid(
        origin=(0.0, 0.0, 0.0),
        dir_u=(1.0, 0.0, 0.0),
        dir_v=(0.0, 1.0, 0.0),
        range_u=(-4.0, 4.0),
        range_v=(-3.0, 3.0),
        interval_u=1.0,
        interval_v=1.0,
    ),
    style=GridStyle(color="#3a3a3a", line_thickness=1),
)

# A few points to make the scene interesting.
viz.new(Point(2, 1, 0), color="#ff4444", style=PointStyle(size=0.15), label="$P_1$")
viz.new(Point(-1, 2, 0), color="#44ff44", style=PointStyle(size=0.15), label="$P_2$")
viz.new(Point(0, -2, 0), color="#4444ff", style=PointStyle(size=0.15), label="$P_3$")

viz.show()
viz.wait()
