# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""demo_cs_annotations.py — annotations in a CoordinateSystem's data frame.

Demonstrates the data-space drawing features of
:class:`~pytanga.viz.CoordinateSystem`:

- ``plot()`` in a 2D coordinate system,
- fixed ``vline``/``hline`` annotations at data values,
- a ``line`` between two data points (tuples or ``Point``s),
- a named, animated ``vline`` (create once, move each frame), and
- drawing a custom ``PointPath`` directly into ``cs.data_group``.

Run with:  uv run python py/examples/viz/demo_cs_annotations.py
"""

import math

from pytanga.geometry.entities import Point
from pytanga.viz import CoordinateSystem, PointPath, PointPathStyle, Visualizer

viz = Visualizer(
    title="Tanga — CoordinateSystem Annotations",
    space_dim=2,
    add_default_axes=False,
    add_default_grid=False,
)

cs = CoordinateSystem(
    viz,
    xlim=(0.0, 4.0 * math.pi),
    ylim=(-1.5, 1.5),
    labels=("x", "sin(x)"),
)

# A sine curve through the normal plot() path.
xs = [0.05 * i for i in range(int(4.0 * math.pi / 0.05) + 1)]
cs.plot(
    xs,
    [math.sin(x) for x in xs],
    color="#44ff44",
    style=PointPathStyle(line_thickness=3),
)

# Fixed annotations at data values.
cs.vline(x=math.pi, name="pi", color="#ff5555")
cs.hline(y=0.0, name="zero", color="#8888ff")

# Line helpers between two data points (accept (x, y) tuples or Point()).
cs.line((1.0, -1.0), (3.0, 1.0), color="#ff88ff")
cs.line(Point(5.0, -1.0), Point(7.0, 1.0), color="#00ffff")

# A custom annotation drawn directly in the data group.
spike = PointPath()
spike.add((0.5, -1.0))
spike.add((0.5, 1.0))
cs.data_group.new(spike, color="#ffffff", style=PointPathStyle(line_thickness=1))

# A moving vertical cursor (created once, updated by name each frame).
cs.vline(x=0.0, name="cursor", color="#ffcc00")

viz.show()
viz.flush()

print("Moving the cursor line until Ctrl+C...")
t = 0.0
for _ in viz.animate(fps=60):
    t += 0.02
    x = t % (4.0 * math.pi)
    cs.vline(x=x, name="cursor")
    viz.flush()

print("Animation stopped.")
