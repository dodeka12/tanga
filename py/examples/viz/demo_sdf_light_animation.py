# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""demo_sdf_light_animation.py — Animate a directional light around a sphere.

Adds a bright key light whose direction orbits a sphere (moving the highlight
and soft shadow), plus a dim static fill light. Demonstrates adding lights via
``add()``, mutating a light's ``direction`` in place, and ``flush()`` +
``sleep_ms()`` for the frame loop.

Run with:  uv run python py/examples/viz/demo_sdf_light_animation.py
"""

import math

from pytanga.geometry import Point, Sphere
from pytanga.viz.sdf import DirectionalLight, SdfVisualizer

viz = SdfVisualizer(title="Tanga SDF — Moving light", add_default_light=False)
viz.show()

viz.add(Sphere(Point(0, 0, 0), 1.5), color="#ffaa00")
viz.add(Sphere(Point(2, 0, 1), 0.5), color="#d2250a")

# A bright key light (orbited in the loop) + a dim static fill light.
key = DirectionalLight(direction=(4.0, 0.0, 3.0), color="#ffffff", intensity=1.2)
viz.add(key)
viz.add(DirectionalLight(direction=(-2.0, -1.0, 1.0), color="#8899ff", intensity=0.35))

viz.set_ambient_light(color="#ffffff", intensity=0.3)

print("Animating a light around the sphere until Ctrl+C...")
t = 0.0
while True:
    t += 0.03
    key.direction = (math.cos(t) * 4.0, math.sin(t) * 4.0, 3.0)
    viz.flush()
    if not viz.sleep_ms(16):
        break

viz.stop_server()
print("Animation stopped.")
