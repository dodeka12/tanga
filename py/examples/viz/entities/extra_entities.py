# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""extra_entities.py — the Disk, PartialDisk, Box, Ellipsoid, Ellipse, and
RegularPolygon visualization-only entities.

Demonstrates the six extra geometric entities that exist purely for rendering
and have no multivector representation:

- a solid :class:`~pytanga.geometry.Disk` and a partial (pie-slice)
  :class:`~pytanga.geometry.PartialDisk`,
- an axis-aligned :class:`~pytanga.geometry.Box` and a
  :class:`~pytanga.geometry.Ellipsoid`,
- a filled :class:`~pytanga.geometry.Ellipse`,
- a :func:`~pytanga.geometry.regular_polygon` (hexagon).

Run with:  uv run python py/examples/viz/entities/extra_entities.py

Keywords: entities, Disk, PartialDisk, Box, Ellipsoid, Ellipse
"""

import math

from pytanga.geometry import (
    Box,
    Direction,
    Disk,
    Ellipse,
    Ellipsoid,
    PartialDisk,
    Point,
    regular_polygon,
)
from pytanga.viz import Visualizer

viz = Visualizer(
    title="Tanga — Extra Viz-only Entities",
    add_default_axes=True,
    add_default_grid=True,
)

# Filled disk in the xy-plane.
viz.new(Disk(center=Point(0, 0, 0), radius=1.2), color="#ff8844", label="Disk")

# Partial disk (3/4 turn pie slice) in the xy-plane.
viz.new(
    PartialDisk(
        center=Point(3, 0, 0),
        radius=1.2,
        angle=math.pi * 1.5,
        start_direction=Direction(1, 0, 0),
    ),
    color="#ffcc44",
    label="PartialDisk",
)

# Axis-aligned box.
viz.new(
    Box(center=Point(0, 3, 0), size=(1.5, 1.0, 1.0)),
    color="#88ccff",
    label="Box",
)

# Ellipsoid.
viz.new(
    Ellipsoid(center=Point(3, 3, 0), radii=(1.0, 0.5, 0.75)),
    color="#ffaa00",
    label="Ellipsoid",
)

# Filled ellipse in the xy-plane.
viz.new(
    Ellipse(center=Point(0, 6, 0), radius_u=1.2, radius_v=0.6),
    color="#ff44ff",
    label="Ellipse",
)

# Regular hexagon in the xy-plane.
viz.new(
    regular_polygon(6, radius=1.0, center=Point(3, 6, 0)),
    color="#44ffaa",
    label="Hexagon",
)

print("Scene ready. Close the browser window or press Ctrl+C to exit.")
viz.show()
viz.wait()
