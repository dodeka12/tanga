# intersect two 3D quadrics (Perwass pencil)

**Keywords:** quadric · intersection · pencil · plane pair · conic · curve · Q3

Intersects pairs of quadrics with the GA pencil: each quadric is created with
`geo(...)` (a `PlanePair` or `Sphere` entity, or a raw `Quadric3D`), their
outer product `q1 ^ q2` spans the pencil, and `geo.analyze` resolves its
degenerate members — a plane-pair member yields a `PlaneConicPair` (the four body
diagonals of the cube `x²−y² = y²−z² = 0`), a single-plane member yields a
planar conic (two spheres → a circle), and a cone member yields a sampled
`Curve` (the quartic intersection).  The smooth-elliptic case (no real
degenerate member) raises `NotImplementedError`.

## Run

```bash
uv run python py/examples/ga/quadric/quadric_intersection_demo.py
```

## Source

[`ga/quadric/quadric_intersection_demo.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/ga/quadric/quadric_intersection_demo.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""quadric_intersection_demo.py — intersect two 3D quadrics (Perwass pencil).

Intersects pairs of quadrics with the GA pencil: each quadric is created with
``geo(...)`` (a ``PlanePair`` or ``Sphere`` entity, or a raw ``Quadric3D``), their
outer product ``q1 ^ q2`` spans the pencil, and ``geo.analyze`` resolves its
degenerate members — a plane-pair member yields a ``PlaneConicPair`` (the four body
diagonals of the cube ``x²−y² = y²−z² = 0``), a single-plane member yields a
planar conic (two spheres → a circle), and a cone member yields a sampled
``Curve`` (the quartic intersection).  The smooth-elliptic case (no real
degenerate member) raises ``NotImplementedError``.

Run with:  uv run python py/examples/ga/quadric/quadric_intersection_demo.py

Keywords: quadric, intersection, pencil, plane pair, conic, curve, Q3
"""

import numpy as np

from pytanga.geometry import (
    Direction,
    Geometry,
    Plane,
    PlanePair,
    Point,
    Sphere,
)
from pytanga.quadric import BasisQ3, Quadric3D
from pytanga.viz import Visualizer

viz = Visualizer(title="Quadric intersection (pencil)")

geo = Geometry(BasisQ3(opns=False))

# 1. Two plane pairs (cube) → the four body diagonals.
pair1 = geo(
    PlanePair(
        Plane(Point(0, 0, 0), Direction(1, -1, 0)),  # x − y = 0
        Plane(Point(0, 0, 0), Direction(1, 1, 0)),  # x + y = 0
    )
)
pair2 = geo(
    PlanePair(
        Plane(Point(0, 0, 0), Direction(0, 1, -1)),  # y − z = 0
        Plane(Point(0, 0, 0), Direction(0, 1, 1)),  # y + z = 0
    )
)
result1 = geo.analyze(pair1 ^ pair2)
viz.new(result1)

# 2. Two spheres → a circle in the plane x = 1.
sphere1 = geo(Sphere(Point(0, 0, 0), 2.0))
sphere2 = geo(Sphere(Point(2, 0, 0), 2.0))
result2 = geo.analyze(sphere1 ^ sphere2)
viz.new(result2)

# 3. Two generic quadrics → a sampled quartic curve (cone member).
rng = np.random.default_rng(0)
gen1 = rng.normal(size=(4, 4))
gen1 = gen1 + gen1.T
gen2 = rng.normal(size=(4, 4))
gen2 = gen2 + gen2.T
q1 = geo.create(Quadric3D(gen1))
q2 = geo.create(Quadric3D(gen2))
result3 = geo.analyze(q1 ^ q2)
viz.new(result3)

print(f"cube: {type(result1).__name__}")
print(f"spheres: {type(result2).__name__}")
print(f"generic: {type(result3).__name__}")

viz.show()
````
