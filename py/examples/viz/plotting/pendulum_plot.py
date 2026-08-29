# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pendulum_plot.py — a swinging pendulum with a live angle-vs-time plot.

A damped pendulum swings in the 3D scene while a ``PointPath`` trail records
its angle over time on a plot plane behind it.  The plot's x axis (time)
auto-scales to the trail's current time range, with a minimum span of a few
seconds (``min_x_span``).

Each frame the trail is appended and :meth:`~pytanga.viz.CoordinateSystem.update_plots`
re-syncs the path and the x axis, then ``flush()`` pushes the update.

Run with:  uv run python py/examples/viz/plotting/pendulum_plot.py

Keywords: plotting, pendulum, live plot, angle vs time
"""

import math

from pytanga.geometry import Line, Point
from pytanga.viz import (
    CoordinateSystem,
    LineStyle,
    PointPath,
    PointPathStyle,
    PointStyle,
    Visualizer,
)

# ── Pendulum parameters ───────────────────────────────────────
L = 2.0  # rod length (world units)
AMPLITUDE = 0.9  # initial angle (radians)
OMEGA = 2.0  # angular frequency (rad/s)
DAMPING = 0.15  # per-second exponential decay
FPS = 60
TRAIL_SECONDS = 12.0

viz = Visualizer(title="Tanga — Pendulum with Live Angle Plot")
viz.show()

# ── Pendulum: pivot + a rotating arm (rod + bob) ──────────────
arm = viz.add_group("arm")
arm.new(Point(0, 0, 0), color="#ffaa00", label="pivot", style=PointStyle(size=0.12))
arm.new(
    Line.from_points(Point(0, 0, 0), Point(0, -L, 0)),
    color="#ff5555",
    label="rod",
    style=LineStyle(thickness=3.0),
)
arm.new(Point(0, -L, 0), color="#44ff44", label="bob", style=PointStyle(size=0.16))

# ── Plot plane behind the pendulum: angle (rad) vs time (s) ───
plot = CoordinateSystem(
    viz,
    xlim=(0.0, TRAIL_SECONDS),
    ylim=(-1.2, 1.2),
    size=(3.0, 1.6),
    labels=("time (s)", "angle (rad)"),
    position=(0.0, 1.2, -2.5),
    normal=(0.0, 0.0, 1.0),
    up=(0.0, 1.0, 0.0),
)

trail = PointPath(max_points=int(TRAIL_SECONDS * FPS))
plot.add_plot(
    trail, color="#ffcc00", style=PointPathStyle(line_thickness=2), auto_x=True
)

viz.flush()

# ── Animation loop ────────────────────────────────────────────
print("Swinging the pendulum and plotting its angle until Ctrl+C...")
t = 0.0
dt = 1.0 / FPS
for _ in viz.animate(fps=FPS):
    t += dt
    theta = AMPLITUDE * math.cos(OMEGA * t) * math.exp(-DAMPING * t)

    arm.set_transform(rotation=(0.0, 0.0, theta))

    trail.add((t, theta))
    plot.update_plots()

    viz.flush()

print("Animation stopped.")
