# All geometric entity types in one scene

**Keywords:** entities · Point · Line · Plane · Sphere · all types

## Run

```bash
uv run python py/examples/viz/entities/all_entities.py
```

## Source

[`viz/entities/all_entities.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/entities/all_entities.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""all_entities.py — All geometric entity types in one scene.

Run with:  uv run python py/examples/viz/entities/all_entities.py

Keywords: entities, Point, Line, Plane, Sphere, all types
"""

from pytanga.geometry import (
    Circle,
    Direction,
    HPoint,
    Line,
    Plane,
    Point,
    PointPair,
    Space,
    Sphere,
)
from pytanga.viz import PointStyle, SphereStyle, Visualizer

viz = Visualizer(title="Tanga — All Entity Types")

# Points
viz.new(
    Point(2, 0, 0), color="#ff4444", style=PointStyle(size=0.12), label="$P_1$ (2,0,0)"
)
viz.new(
    Point(0, 2, 0), color="#44ff44", style=PointStyle(size=0.12), label="$P_2$ (0,2,0)"
)
viz.new(
    Point(0, 0, 2), color="#4444ff", style=PointStyle(size=0.12), label="$P_3$ (0,0,2)"
)

# Direction arrow from origin
viz.new(Direction(1, 1, 0), color="#ffffff", label="d")

# Line through origin along X axis
viz.new(
    Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0)),
    color="#44ff44",
    label="L (x-axis)",
)

# Translucent plane at z=3
viz.new(
    Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)),
    opacity=0.25,
    label="$\pi$ (z=3)",
)

# Circle in XY plane
viz.new(
    Circle(center=Point(0, 0, 0), normal=Direction(0, 0, 1), radius=3),
    color="#ff44ff",
    label="C",
)

# Sphere at origin (wireframe)
viz.new(
    Sphere(Point(0, 0, 0), radius=2.5),
    style=SphereStyle(wireframe=True),
    opacity=0.3,
    label="S",
)

# Point pair
viz.new(
    PointPair(point_a=Point(-1, 1, 0), point_b=Point(1, 1, 0)),
    color="#44ff44",
    label="PP",
)

# Homogeneous point
viz.new(HPoint(point=Point(-3, -2, 1)), style=PointStyle(size=0.12), label="H")

# Space — faint bounding outline
viz.new(Space(), opacity=0.08)

print("Scene ready. Close the browser window or press Ctrl+C to exit.")
viz.show()
viz.wait()
````
