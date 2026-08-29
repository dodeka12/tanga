# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""nested_groups.py — Demonstrate nested ``VizGroup`` hierarchies.

Builds a two-link planar arm out of *nested* scene-graph groups::

    arm1  (top-level group — pivot at the world origin)
    ├── rod1     segment from arm1's origin to its far end
    └── arm2     (group *nested inside* arm1, offset to the end of rod1)
        ├── rod2 segment from arm2's origin to its tip
        └── tip  point at the end of rod2

Each rod rotates about its *own* origin:

* ``arm1`` rotates ``rod1`` (and everything nested under it) about pivot 1.
* ``arm2`` rotates ``rod2`` about pivot 2 — the end of rod1 — which is itself
  carried around by ``arm1``'s rotation, so the two rotations compose.

Only the two group transforms change per frame (the ``transform`` aspect), so
the rod geometry is never re-serialized.

Each rod's label is anchored to the *center* of the line via
``LabelStyle(along=0.5)`` — ``along`` is the fraction along the line's extent
(``0`` = start, ``0.5`` = midpoint, ``1`` = end).

Run with:  uv run python py/examples/viz/scenes/nested_groups.py

Keywords: scenes, VizGroup, hierarchy, nested
"""

import math

from pytanga.geometry import Line, Point
from pytanga.viz import LabelStyle, LineStyle, PointStyle, Visualizer

L1 = 2.0  # length of rod 1
L2 = 1.5  # length of rod 2

viz = Visualizer(title="Tanga — Nested Groups")
viz.show()

# ── arm1: pivot at the world origin ─────────────────────────
arm1 = viz.add_group("arm1")
arm1.new(Point(0, 0, 0), color="#ffaa00", label="pivot1", style=PointStyle(size=0.10))
arm1.new(
    Line.from_points(Point(0, 0, 0), Point(L1, 0, 0)),
    color="#ff5555",
    label="rod1",
    label_style=LabelStyle(along=0.5),  # anchor label at the line's midpoint
    style=LineStyle(thickness=3.0),
)

# ── arm2: nested inside arm1, offset to the end of rod1 ─────
arm2 = arm1.add_group("arm2")
arm2.set_transform(position=(L1, 0.0, 0.0))
arm2.new(Point(0, 0, 0), color="#ffaa00", label="pivot2", style=PointStyle(size=0.09))
arm2.new(
    Line.from_points(Point(0, 0, 0), Point(L2, 0, 0)),
    color="#5599ff",
    label="rod2",
    label_style=LabelStyle(along=0.5),  # anchor label at the line's midpoint
    style=LineStyle(thickness=3.0),
)
arm2.new(Point(L2, 0, 0), color="#44ff44", label="tip", style=PointStyle(size=0.10))

viz.flush()

print("Animating two nested rods until Ctrl+C...")
t = 0.0
for dt in viz.animate(fps=50):
    t += dt

    # arm1 rotates rod1 + arm2 + rod2 about pivot 1 (its own origin).
    arm1.set_transform(rotation=(0.0, 0.0, math.sin(t) * 1.2))

    # arm2 rotates rod2 about its own origin (pivot 2), compounding with arm1.
    arm2.set_transform(rotation=(0.0, 0.0, math.sin(1.7 * t) * 1.5))

    viz.flush()

print("Animation stopped.")
