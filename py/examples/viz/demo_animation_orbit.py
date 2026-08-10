# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""demo_animation_orbit.py — Frame-by-frame animation at ~60 FPS.

Run with:  uv run python py/examples/viz/demo_animation_orbit.py
"""

import math

from pytanga.geometry import Direction, Line, Point
from pytanga.viz import PointStyle, Visualizer

viz = Visualizer(title="Tanga — Animated Orbit")
viz.start()

# Reference line — z-axis
viz.add(
    Line(origin=Point(0, 0, -3), direction=Direction(0, 0, 1)),
    color="#444466",
    label="z-axis",
)

point_id = viz.add(Point(3, 0, 0), color="#ff4444", label="orbit")
trail_id = viz.add(Point(3, 0, 0), color="#ff8844", style=PointStyle(size=0.08))
viz.flush()

print("Animating for 5 seconds...")
for frame in range(300):
    angle = frame * 0.05
    x = 3 * math.cos(angle)
    y = 3 * math.sin(angle)
    viz.update_entity(point_id, Point(x, y, 0))

    trail_angle = angle - 0.26  # 15-degree phase offset
    viz.update_entity(
        trail_id,
        Point(2.8 * math.cos(trail_angle), 2.8 * math.sin(trail_angle), 0),
    )

    viz.flush()
    viz.sleep_ms(16)

viz.stop()
print("Animation stopped.")
