# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""demo_labels.py — Labels with custom styling, dynamic update, and removal.

Run with:  uv run python py/examples/viz/demo_labels.py
"""

import time

from pytanga.geometry import Direction, Plane, Point, Sphere
from pytanga.viz import LabelStyle, Visualizer

viz = Visualizer(title="Tanga — Labels")
viz.start()

# Default label
viz.add(Point(1, 2, 0), color="#ff4444", size=0.15, label="P₁")

# Custom label style
origin_id, origin_label = viz.add(
    Point(0, 0, 0),
    color="#ffff00",
    size=0.2,
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
    label="π (z=3)",
)

# Label on a sphere — positioned above the surface
viz.add(
    Sphere(Point(0, 0, 0), radius=2.5),
    wireframe=True,
    opacity=0.4,
    label="S₁",
    label_style=LabelStyle(offset_local=(0.0, 1.05, 0.0)),
)

viz.flush()

# Dynamic label update
print("Updating label in 3 seconds...")
time.sleep(3)
viz.update_label(origin_label, text="O", style=LabelStyle(color="#ff8888"))
viz.flush()

print("Removing label in 3 seconds...")
time.sleep(3)
viz.update_label(origin_label, text="")
viz.flush()

print("Close the browser window or press Ctrl+C to exit.")
viz.sleep_ms(5000)
viz.stop()
