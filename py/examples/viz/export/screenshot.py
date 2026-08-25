# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""screenshot.py — Programmatic PNG screenshot at custom resolution.

Run with:  uv run python py/examples/viz/export/screenshot.py
"""

from pytanga.geometry import Direction, Plane, Point, Sphere
from pytanga.viz import PointStyle, SceneExporter, SphereStyle, Visualizer

viz = Visualizer(title="Tanga — Screenshot")
viz.show()

viz.new(Point(2, 0, 0), color="#ff4444", style=PointStyle(size=0.15), label="$P_1$")
viz.new(Point(0, 2, 0), color="#44ff44", style=PointStyle(size=0.15), label="$P_2$")
viz.new(
    Sphere(Point(0, 0, 0), radius=2.5), style=SphereStyle(wireframe=True), opacity=0.3
)
viz.new(Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)), opacity=0.25)
viz.flush()

exporter = SceneExporter(viz)
exporter.screenshot("figure.png")
print("Screenshot saved to figure.png")

exporter.screenshot("figure_hd.png", width=1920, height=1080)
print("HD screenshot saved to figure_hd.png")

viz.stop_server()
