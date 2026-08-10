# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""demo_export_figure.py — Presentation figure export with FigureStyle.

Run with:  uv run python py/examples/viz/demo_export_figure.py
"""

from pytanga.geometry import Point, Sphere
from pytanga.viz import FigureStyle, PointStyle, SceneExporter, SphereStyle, Visualizer

viz = Visualizer(title="Sphere Construction")

viz.add(Sphere(Point(0, 0, 0), 2.5), style=SphereStyle(wireframe=True), opacity=0.4, label="$S_1$")
viz.add(Point(0, 0, 0), color="#ffff00", style=PointStyle(size=0.15), label="$O$")

exporter = SceneExporter(viz)

# Set a footer caption with LaTeX math
exporter.figure_config.footer = (
    "**Figure 1:** A sphere of radius $r = 2.5$ centered at $O = (0,0,0)$."
)

exporter.export_figure(
    "sphere_figure.html",
    style=FigureStyle(
        width=800,
        height=600,
        background="transparent",
        auto_rotate=True,
        border_radius="8px",
    ),
)

print("Exported figure snippet to sphere_figure.html")
