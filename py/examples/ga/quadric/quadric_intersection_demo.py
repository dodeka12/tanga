# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""quadric_intersection_demo.py — intersect two 3D quadrics (Perwass pencil).

Intersects pairs of quadrics via the pencil's degenerate members: a plane-pair
member yields a ``PlaneConicPair`` (two plane-conics — e.g. the four body
diagonals of the cube ``x²−y² = y²−z² = 0``), a single-plane member yields a
planar conic (two spheres → a circle), and a cone member yields a sampled
``Curve`` (the quartic intersection).  The smooth-elliptic case (no real
degenerate member) raises ``NotImplementedError`` for now.

Run with:  uv run python py/examples/ga/quadric/quadric_intersection_demo.py

Keywords: quadric, intersection, pencil, plane pair, conic, curve, Q3
"""

import numpy as np

from pytanga.quadric import intersect_quadrics
from pytanga.viz import Visualizer

viz = Visualizer(title="Quadric intersection (pencil)")

# 1. Two plane pairs (cube) → the four body diagonals.
cube1 = np.diag([1.0, -1.0, 0.0, 0.0])  # x² − y²
cube2 = np.diag([0.0, 1.0, -1.0, 0.0])  # y² − z²
viz.new(intersect_quadrics(cube1, cube2))

# 2. Two spheres → a circle in the plane x = 1.
sphere1 = np.diag([1.0, 1.0, 1.0, -4.0])
sphere2 = np.array(
    [[1.0, 0, 0, -2.0], [0, 1.0, 0, 0], [0, 0, 1.0, 0], [-2.0, 0, 0, 0.0]]
)
viz.new(intersect_quadrics(sphere1, sphere2))

# 3. Two generic quadrics → a sampled quartic curve (cone member).
rng = np.random.default_rng(0)
gen1 = rng.normal(size=(4, 4))
gen1 = gen1 + gen1.T
gen2 = rng.normal(size=(4, 4))
gen2 = gen2 + gen2.T
viz.new(intersect_quadrics(gen1, gen2))

for name, q1, q2 in (
    ("cube", cube1, cube2),
    ("spheres", sphere1, sphere2),
    ("generic", gen1, gen2),
):
    result = intersect_quadrics(q1, q2)
    print(f"{name}: {type(result).__name__}")

viz.show()
