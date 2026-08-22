# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""demo_sdf_entities.py — First vertical slice for the SDF viewer.

Draws a finite ``Line`` and a ``Sphere`` from ``pytanga.geometry`` in the
ray-marched signed-distance-function viewer.

Run with:  uv run python py/examples/viz/demo_sdf_entities.py
"""

from pytanga.geometry import Line, Point, Sphere
from pytanga.viz.sdf import SdfVisualizer

viz = SdfVisualizer(title="Tanga SDF — Line + Sphere")

# A finite line segment (origin + length via from_points).
viz.add(
    Line.from_points(Point(-3, 0, 0), Point(3, 0, 0)),
    color="#44ff44",
    thickness=0.08,
)

# A filled sphere.
viz.add(
    Sphere(Point(0, 1.5, 0), radius=1.5),
    color="#ffaa00",
)

print("Opening the SDF viewer. A green line and an orange sphere should be")
print("visible; drag to orbit, right/middle-drag to pan, scroll to zoom.")

viz.show()
viz.wait()