# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""demo_export_html.py — Self-contained HTML and glTF export.

Run with:  uv run python py/examples/viz/demo_export_html.py
"""

from pytanga.geometry import Direction, Plane, Point, Sphere
from pytanga.viz import SceneExporter, Visualizer

viz = Visualizer(title="Tanga — HTML Export")
viz.add(Point(2, 0, 0), color="#ff4444", size=0.15, label="P₁")
viz.add(Point(0, 2, 0), color="#44ff44", size=0.15, label="P₂")
viz.add(Sphere(Point(0, 0, 0), radius=2.5), wireframe=True, opacity=0.3)
viz.add(Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)), opacity=0.25)

exporter = SceneExporter(viz)
exporter.export_html("scene.html")
print("Exported to scene.html — open it in any browser.")

exporter.export_glb("scene.glb")
print("Exported to scene.glb — open with Blender or <model-viewer>.")

viz.run()
