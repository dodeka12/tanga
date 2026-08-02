# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""demo_animated_export.py — Animated HTML export with JS playback engine.

Run with:  uv run python py/examples/viz/demo_animated_export.py
"""

import math

from pytanga.geometry import Point
from pytanga.viz import SceneExporter, Visualizer

viz = Visualizer(title="Tanga — Animated Export")
viz.start()

point_id = viz.add(Point(3, 0, 0), color="#ff4444", label="orbit")
viz.flush()

exporter = SceneExporter(viz)
recording = exporter.start_animation_recording()

for frame in range(90):
    angle = frame * 0.07
    viz.update_entity(
        point_id,
        Point(3 * math.cos(angle), 3 * math.sin(angle), 0),
    )
    viz.flush()
    recording.capture_frame()
    viz.sleep_ms(33)

exporter.export_animated_html(
    "animated_orbit.html",
    recording,
    fps=30,
    loop=True,
)

print("Exported to animated_orbit.html — open it in any browser.")
viz.stop()
