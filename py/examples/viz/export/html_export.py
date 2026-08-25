# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""html_export.py — Self-contained HTML and glTF export.

Run with:  uv run python py/examples/viz/export/html_export.py
"""

from pytanga.geometry import Direction, Plane, Point, Sphere
from pytanga.viz import PointStyle, SphereStyle, Visualizer

viz = Visualizer(title="Tanga — HTML Export")
viz.new(Point(2, 0, 0), color="#ff4444", style=PointStyle(size=0.15), label="$P_1$")
viz.new(Point(0, 2, 0), color="#44ff44", style=PointStyle(size=0.15), label="$P_2$")
viz.new(
    Sphere(Point(0, 0, 0), radius=2.5), style=SphereStyle(wireframe=True), opacity=0.3
)
viz.new(Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)), opacity=0.25)

# Static exports read directly from the in-memory scene — no server needed.
# flush() ensures any pending dirty state is resolved before export.
viz.flush()

viz.export_snapshot("scene.html", overwrite=True)
print("Exported to scene.html — open it in any browser.")

viz.export_glb("scene.glb", overwrite=True)
print("Exported to scene.glb — open with Blender or <model-viewer>.")
