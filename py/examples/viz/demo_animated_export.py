# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""demo_animated_export.py — Animated HTML export with JS playback engine.

Run with:  uv run python py/examples/viz/demo_animated_export.py
"""

import math

from pytanga.geometry import Point
from pytanga.viz import AnimStyle, Visualizer

viz = Visualizer(title="Tanga — Animated Export")
viz.show()

point = viz.new(Point(3, 0, 0), color="#ff4444", label="orbit")
viz.flush()

recording = viz.start_animation_recording()

for frame in range(90):
    angle = frame * 0.07
    point.entity = Point(3 * math.cos(angle), 3 * math.sin(angle), 0)
    viz.flush()
    recording.capture_frame()
    viz.sleep_ms(33)

viz.export_snapshot(
    "animated_orbit.html",
    overwrite=True,
    animation=recording,
    anim_style=AnimStyle(fps=30, loop=True, compress=True),
)

print("Exported to animated_orbit.html — open it in any browser.")
viz.stop_server()
