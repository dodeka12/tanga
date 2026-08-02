# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""demo_title_annotation.py — Title overlay and Markdown + LaTeX annotation.

Run with:  uv run python py/examples/viz/demo_title_annotation.py
"""

from pytanga.geometry import Point, Sphere
from pytanga.viz import Visualizer

viz = Visualizer(
    title="PGA3 — Sphere Visualization",
    annotation="""## Sphere at Origin

A sphere of radius $r = 2.5$ centered at the origin.

The equation in PGA3 is: $p \\cdot p = r^2$

In conformal GA (N3), a sphere is represented as a grade-1 vector:
$$S = o - \\frac{1}{2} r^2 \\infty$$

where $o$ is the origin point and $\\infty$ is the point at infinity.
""",
)

viz.add(Point(1, 2, 3), color="#ff4444", size=0.12, label="P₁")
viz.add(Sphere(Point(0, 0, 0), radius=2.5), wireframe=True, opacity=0.4)
viz.run()
