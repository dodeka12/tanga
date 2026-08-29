# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""animated_camera_2d.py — 2D animated HTML export with a moving camera.

A point sweeps left-to-right while the 2D orthographic camera pans to follow
it.  Each frame records both the entity state and the camera, so the exported
HTML plays the camera motion back as well as the point motion.

Run with:  uv run python py/examples/viz/export/animated_camera_2d.py

Keywords: export, HTML, animated, camera, 2D
"""

import math

from pytanga.geometry import Point
from pytanga.viz import AnimStyle, PointStyle, View2DConfig, Visualizer

viz = Visualizer(space_dim=2, title="Tanga — 2D Animated Export (moving camera)")
viz.show()

mover = viz.new(
    Point(-8, 0, 0), color="#ff4444", label="mover", style=PointStyle(size=0.4)
)
viz.flush()

recording = viz.start_animation_recording()

for frame in range(120):
    x = -8.0 + frame * 0.14
    mover.entity = Point(x, 2.0 * math.sin(frame * 0.05), 0)

    # Pan the orthographic camera so the visible rectangle follows the point.
    viz.set_camera(View2DConfig(xmin=x - 12.0, xmax=x + 12.0, ymin=-8.0, ymax=8.0))
    viz.flush()
    recording.capture_frame()
    viz.sleep_ms(33)

viz.export_snapshot(
    "_output/animated_camera_2d.html",
    overwrite=True,
    animation=recording,
    anim_style=AnimStyle(fps=30, loop=True, compress=True),
)

print("Exported to animated_camera_2d.html — open it in any browser.")
viz.stop_server()
