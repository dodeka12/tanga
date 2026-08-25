# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""timeline.py — Keyframe timeline with fade-in and move.

Run with:  uv run python py/examples/viz/animation/timeline.py
"""

from pytanga.geometry import Direction, Plane, Point, Sphere
from pytanga.viz import Visualizer

viz = Visualizer(title="Tanga — Keyframe Timeline")
viz.show()

p1 = viz.add(Point(0, 0, 0), color="#ff4444", opacity=0.0, label="$P_1$")
p2 = viz.add(Point(5, 0, 0), color="#44ff44", opacity=0.0, label="$P_2$")
sphere_id = viz.add(
    Sphere(Point(0, 0, 0), radius=1.0),
    wireframe=True,
    opacity=0.0,
    label="S",
)
plane_id = viz.add(
    Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)),
    opacity=0.0,
    label="$\pi$",
)

viz.flush()

viz.timeline().wait(0.5).animate_to(p1, opacity=1.0, duration=0.3).animate_to(
    p2, opacity=1.0, duration=0.3, parallel=True
).wait(0.3).animate_to(
    p1, position=(3, 2, 0), duration=1.5, easing="ease-out"
).animate_to(p2, position=(0, 3, 0), duration=2.0, parallel=True).wait(0.3).animate_to(
    sphere_id, opacity=0.4, duration=0.5
).animate_to(sphere_id, position=(3, 2, 0), duration=1.5, parallel=True).wait(
    0.2
).animate_to(plane_id, opacity=0.2, duration=0.5).play()

viz.sleep_ms(7000)
print("Timeline complete.")
viz.stop_server()
