# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""demo_point_path_trail.py — Moving point with a color-gradient trail.

A point orbits in a circle while a ``PointPath`` with ``pop_colors=False``
draws its trailing path.  The trail uses a fixed red-to-orange gradient
so that the head is bright and the tail fades to dark red.

Run with:  uv run python py/examples/viz/demo_point_path_trail.py
"""

import math

from pytanga.geometry import Point
from pytanga.viz import PointPath, PointPathStyle, Visualizer, gradient_colors

# ── Setup ──────────────────────────────────────────────────
viz = Visualizer(title="Tanga — PointPath Trail Demo")
viz.start()

TRAIL_LENGTH = 150

# Create a 150-color gradient: dark red at the tail → bright orange at the head
trail_gradient = gradient_colors("#440000", "#ffaa00", TRAIL_LENGTH)

# PointPath with anchored colors (pop_colors=False):
# points shift through a fixed color gradient — the tail is always dark,
# the head is always bright
trail = PointPath(max_points=TRAIL_LENGTH, pop_colors=False,
                  default_colors=trail_gradient)

# Pre-fill the trail with the origin so it draws immediately
# (otherwise it needs 2+ points to render)
for _ in range(TRAIL_LENGTH):
    trail.add((0, 0, 0))

trail_id = viz.add(trail, style=PointPathStyle(line_thickness=0.04))

# The moving object itself
point_id = viz.add(Point(3, 0, 0), color="#ffaa00", size=0.12, label="object")

viz.flush()

# ── Animation loop ─────────────────────────────────────────
print("Animating circular orbit with gradient trail for 10 seconds...")

for frame in range(600):
    angle = frame * 0.04  # radians per frame
    x = 3 * math.cos(angle)
    y = 3 * math.sin(angle)
    z = math.sin(angle * 0.5) * 0.5  # slight vertical oscillation

    # Move the object
    viz.update_entity(point_id, Point(x, y, z))

    # Extend the trail
    trail.add((x, y, z))
    viz.update_entity(trail_id, trail)

    viz.flush()
    viz.sleep_ms(16)

viz.stop()
print("Animation stopped.")