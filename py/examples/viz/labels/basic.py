# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""basic.py — Labels with custom styling, dynamic update, and removal.

Run with:  uv run python py/examples/viz/labels/basic.py
"""

import time

from pytanga.geometry import Direction, Plane, Point, Sphere
from pytanga.viz import LabelStyle, PointStyle, Visualizer

viz = Visualizer(title="Tanga — Labels")
viz.show()

# Default label
viz.add(Point(1, 2, 0), color="#ff4444", style=PointStyle(size=0.15), label="$P_1$")

# Rotated label — `rotation` (degrees) tilts the label about its anchor.
viz.add(
    Point(-2, 2, 0),
    color="#44aaff",
    style=PointStyle(size=0.15),
    label="$R_1$ (45°)",
    label_style=LabelStyle(rotation=45),
)

# Custom label style
origin_id = viz.add(
    Point(0, 0, 0),
    color="#ffff00",
    label="Origin",
    label_style=LabelStyle(
        offset_local=(0.0, 1.1, 0.0),
        font_size=18,
        color="#ffff00",
        background="rgba(0, 0, 0, 0.8)",
    ),
)

# Label on a plane
viz.add(
    Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)),
    opacity=0.3,
    label="$\\pi$ (z=3)",
)

# Label on a sphere — positioned above the surface
viz.add(
    Sphere(Point(0, 0, 0), radius=2.5),
    opacity=0.4,
    label="$S_1$",
    label_style=LabelStyle(offset_local=(0.0, 1.05, 0.0)),
)

viz.flush()

# Dynamic label update — remove and re-add the entity with a new label style
print("Updating label in 3 seconds...")
time.sleep(3)
viz.remove(origin_id)
viz.add(
    Point(0, 0, 0),
    entity_id=origin_id,
    color="#ffff00",
    label="O",
    label_style=LabelStyle(
        offset_local=(0.0, 1.1, 0.0),
        font_size=18,
        color="#ff8888",
        background="rgba(0, 0, 0, 0.8)",
    ),
)
viz.flush()

print("Removing label in 3 seconds...")
time.sleep(3)
viz.remove(origin_id)
viz.add(
    Point(0, 0, 0),
    entity_id=origin_id,
    color="#ffff00",
)
viz.flush()

print("Close the browser window or press Ctrl+C to exit.")
viz.sleep_ms(5000)
viz.stop_server()
