# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""animated_circle_transform.py — Animated export with transform and content changes.

Records three entities to an animated HTML file so the playback can be checked
for correct per-frame updates:

* a constant ``PointPath`` tracing the orbit — never changes between frames;
* a ``Circle`` whose center moves around that orbit — a *transform-only*
  change (only its ``transform.position`` differs between frames);
* a ``Circle`` whose radius oscillates in place — a *content* change (only
  its ``radius`` differs between frames).

Run with:  uv run python py/examples/viz/export/animated_circle_transform.py

Keywords: export, HTML, animated, transform, Circle, PointPath
"""

import math

from pytanga.geometry import Circle, Point
from pytanga.viz import AnimStyle, PointPath, PointPathStyle, Visualizer

# ── Setup ──────────────────────────────────────────────────
ORBIT_RADIUS = 4.0   # radius of the circular path the moving circle follows
MOVING_RADIUS = 0.3  # fixed radius of the moving circle
FRAMES = 120
FPS = 30

viz = Visualizer(title="Tanga — Animated Transform Update Check")
viz.show()

# Constant reference: the orbit path the moving circle follows.  It is added
# once and never updated, so it should stay fixed for the whole playback.
orbit = PointPath(max_points=64)
for i in range(64):
    angle = 2.0 * math.pi * i / 64
    orbit.add((ORBIT_RADIUS * math.cos(angle), ORBIT_RADIUS * math.sin(angle), 0.0))
viz.new(orbit, color="#445577", style=PointPathStyle(line_thickness=1))

# Circle that moves around the orbit: only its center (transform.position)
# changes each frame, while its radius stays fixed.
moving = viz.new(
    Circle(center=Point(ORBIT_RADIUS, 0.0, 0.0), radius=MOVING_RADIUS),
    color="#ff4444",
    label="moving",
)

# Circle whose radius oscillates in place: its center stays fixed while its
# radius (a content field) changes each frame.
pulsing = viz.new(
    Circle(center=Point(0.0, 0.0, 0.0), radius=1.0),
    color="#44aa44",
    label="radius",
)

viz.flush()

# ── Record ────────────────────────────────────────────────
recording = viz.start_animation_recording()

for frame in range(FRAMES):
    angle = 2.0 * math.pi * frame / FRAMES

    moving.entity = Circle(
        center=Point(
            ORBIT_RADIUS * math.cos(angle),
            ORBIT_RADIUS * math.sin(angle),
            0.0,
        ),
        radius=MOVING_RADIUS,
    )

    radius = 1.0 + 0.6 * math.sin(2.0 * angle)
    pulsing.entity = Circle(center=Point(0.0, 0.0, 0.0), radius=radius)

    viz.flush()
    recording.capture_frame()
    viz.sleep_ms(33)

# Inline the viewer library so the exported HTML is self-contained and can be
# checked locally before the branch is published (no jsDelivr ref to resolve).
viz.export_snapshot(
    "_output/animated_circle_transform.html",
    overwrite=True,
    animation=recording,
    anim_style=AnimStyle(fps=FPS, loop=True, compress=True),
    delivery="inline",
)

print("Exported to _output/animated_circle_transform.html — open it in any browser.")
viz.stop_server()
