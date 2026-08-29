# Title overlay and Markdown + LaTeX annotation

**Keywords:** title · annotation · Markdown · LaTeX · KaTeX

## Run

```bash
uv run python py/examples/viz/labels/title_annotation.py
```

## Source

[`viz/labels/title_annotation.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/labels/title_annotation.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""title_annotation.py — Title overlay and Markdown + LaTeX annotation.

Run with:  uv run python py/examples/viz/labels/title_annotation.py

Keywords: title, annotation, Markdown, LaTeX, KaTeX
"""

from pytanga.geometry import Point, Sphere
from pytanga.viz import PointStyle, SphereStyle, Visualizer

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

viz.new(Point(1, 2, 3), color="#ff4444", style=PointStyle(size=0.12), label="$P_1$")
viz.new(
    Sphere(Point(0, 0, 0), radius=2.5), style=SphereStyle(wireframe=True), opacity=0.4
)
viz.show()
viz.wait()
````
