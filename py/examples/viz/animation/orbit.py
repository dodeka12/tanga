# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""orbit.py — Frame-by-frame animation at ~60 FPS.

Run with:  uv run python py/examples/viz/animation/orbit.py
"""

import math

from pytanga.geometry import Direction, Line, Point
from pytanga.viz import PointStyle, Visualizer

viz = Visualizer(title="Tanga — Animated Orbit")
viz.show()

# Reference line — z-axis
viz.new(
    Line(origin=Point(0, 0, -3), direction=Direction(0, 0, 1)),
    color="#444466",
    label="z-axis",
)

point = viz.new(Point(3, 0, 0), color="#ff4444", label="orbit")
trail = viz.new(Point(3, 0, 0), color="#ff8844", style=PointStyle(size=0.08))
viz.flush()

print("Animating orbit until Ctrl+C...")
angle = 0.0
for _ in viz.animate(fps=60):
    angle += 0.05  # radians per frame (~3 rad/s at 60 FPS)
    x = 3 * math.cos(angle)
    y = 3 * math.sin(angle)
    point.entity = Point(x, y, 0)

    trail_angle = angle - 0.26  # 15-degree phase offset
    trail.entity = Point(2.8 * math.cos(trail_angle), 2.8 * math.sin(trail_angle), 0)

    viz.flush()

print("Animation stopped.")
