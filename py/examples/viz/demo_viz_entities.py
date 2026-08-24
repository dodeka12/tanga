# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""demo_viz_entities.py — the visualization-only Cylinder and Arc entities.

Demonstrates the two entities that exist purely for rendering and have no
multivector representation:

- a solid :class:`~pytanga.geometry.Cylinder` (both `align_center` modes),
- a partial :class:`~pytanga.geometry.Arc` with a cone arrow tip at its end,
- a full-torus :class:`~pytanga.geometry.Arc` (default ``2π`` radians).

Run with:  uv run python py/examples/viz/demo_viz_entities.py
"""

import math

from pytanga.geometry import Arc, Cylinder, Direction, Point
from pytanga.viz import Visualizer

viz = Visualizer(
    title="Tanga — Viz-only Entities (Cylinder & Arc)",
    add_default_axes=False,
    add_default_grid=False,
)

# Solid cylinder starting at the origin (align_center=0, the default).
viz.new(
    Cylinder(
        origin=Point(0, 0, 0),
        axis=Direction(0, 0, 1),
        length=2.0,
        radius=0.2,
    ),
    color="#44aaff",
    label="Cylinder (base at origin)",
)

# Solid cylinder centered on the origin (align_center=0.5).
viz.new(
    Cylinder(
        origin=Point(3, 0, 0),
        axis=Direction(0, 0, 1),
        length=2.0,
        radius=0.2,
        align_center=0.5,
    ),
    color="#44ffaa",
    label="Cylinder (centered)",
)

# Partial arc (3/4 turn) with a cone arrow tip at its end.
viz.new(
    Arc(
        origin=Point(0, 0, 0),
        axis=Direction(0, 0, 1),
        radius=1.5,
        tube_radius=0.05,
        angle=math.pi * 1.5,
        show_arrow=True,
    ),
    color="#ffcc44",
    label="Arc + arrow",
)

# Full torus (default angle = 2π radians).
viz.new(
    Arc(origin=Point(0, 0, 3), axis=Direction(0, 0, 1), radius=2.0, tube_radius=0.04),
    color="#ff8844",
    label="Torus",
)

print("Scene ready. Close the browser window or press Ctrl+C to exit.")
viz.show()
viz.wait()
