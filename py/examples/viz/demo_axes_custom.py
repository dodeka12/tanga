# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""demo_axes_custom.py — Custom axes and grid as explicit scene objects.

Creates a pair of axes with custom intervals, value labels, and ticks,
plus a grid in the XY plane.  Axes and grids are ordinary scene objects
now — no hard-coded helpers.

Run with:  uv run python py/examples/viz/demo_axes_custom.py
"""

from pytanga.geometry import Point
from pytanga.viz import Axis, Grid, PointStyle, Visualizer

viz = Visualizer(title="Tanga — Custom Axes & Grid")

# Custom X axis: major ticks every 2 units, value labels at each major tick.
viz.add(Axis(start=(0, 0, 0), end=(10, 0, 0), major_interval=2.0, label="X"))

# Custom Y axis: major ticks every 1 unit plus minor ticks every 0.5.
viz.add(
    Axis(
        start=(0, 0, 0),
        end=(0, 6, 0),
        major_interval=1.0,
        minor_interval=0.5,
        label="Y",
    )
)

# Grid in the XY plane with 1-unit spacing and a 10×6 extent.
viz.add(Grid(dir_u=(1, 0, 0), dir_v=(0, 1, 0), range_u=10.0, range_v=6.0))

viz.add(Point(3, 2, 0), color="#ffcc00", style=PointStyle(size=0.12), label="P")

viz.run()