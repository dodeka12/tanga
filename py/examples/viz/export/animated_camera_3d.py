# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""animated_camera_3d.py — 3D animated HTML export with a moving camera.

A point orbits in 3D while the perspective camera orbits the scene on a
counter-rotating path.  Each frame records both the entity state and the
camera, so the exported HTML plays the camera motion back as well.

Run with:  uv run python py/examples/viz/export/animated_camera_3d.py

Keywords: export, HTML, animated, camera, 3D
"""

import math

from pytanga.geometry import Direction, Line, Point
from pytanga.viz import AnimStyle, CameraConfig3d, Visualizer

viz = Visualizer(title="Tanga — 3D Animated Export (moving camera)")
viz.show()

# A fixed reference axis so the camera motion is easy to see.
viz.new(
    Line(origin=Point(0, 0, -4), direction=Direction(0, 0, 1)),
    color="#444466",
    label="z-axis",
)
point = viz.new(Point(3, 0, 0), color="#ff4444", label="orbit")
viz.flush()

recording = viz.start_animation_recording()

for frame in range(90):
    angle = frame * 0.07
    point.entity = Point(3.0 * math.cos(angle), 3.0 * math.sin(angle), 0.0)

    # Orbit the camera in the opposite direction, always looking at the origin.
    cam_angle = -frame * 0.05
    viz.set_camera(
        CameraConfig3d(
            position=(8.0 * math.cos(cam_angle), 4.0, 8.0 * math.sin(cam_angle)),
            target=(0.0, 0.0, 0.0),
            up=(0.0, 1.0, 0.0),
        )
    )
    viz.flush()
    recording.capture_frame()
    viz.sleep_ms(33)

viz.export_snapshot(
    "_output/animated_camera_3d.html",
    overwrite=True,
    animation=recording,
    anim_style=AnimStyle(fps=30, loop=True, compress=True),
)

print("Exported to animated_camera_3d.html — open it in any browser.")
viz.stop_server()
