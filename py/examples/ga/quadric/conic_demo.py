# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""conic_demo.py — reconstruct a conic from 5 points and draw its refined entity.

Embeds five points in the 2D projective quadric (conic) space, reconstructs the
conic through them, and refines the raw ``Conic`` to a concrete 2D entity
(``Circle`` / ``Ellipse`` / ``Hyperbola`` / ``Parabola`` / line pair) drawn in
the standard viewer alongside the five points.

Run with:  uv run python py/examples/ga/quadric/conic_demo.py

Keywords: quadric, conic, conic_from_points, refine, analyze
"""

import math
import sys

# from pytanga.basis import BasisQ2
from pytanga.geometry import Geometry, Point, analyze, refine
from pytanga.quadric import BasisQ2, conic_from_points, to_coeffs
from pytanga.viz import ActEventHandler, ActPoint, DragEvent, Visualizer

# Five points on the ellipse  x²/4 + y² = 1  (no three collinear).

Q2 = BasisQ2(opns=True)
geo = Geometry(Q2)
p1 = geo(Point(1, 0, 0))
p1.show("p1")
print(geo(p1))
p2 = geo(Point(-1, 0, 0))
p3 = geo(Point(0, 1, 0))
p4 = geo(Point(0, -1, 0))


on_drag_a: ActEventHandler


async def on_drag_a(event: DragEvent, ap: ActPoint) -> bool:
    return False


ap_a = ActPoint(
    1,
    1,
    0,
    handler=on_drag_a,
)

conic = p1 ^ p2 ^ p3 ^ p4 ^ geo(ap_a.entity)
conic.show("conic")
print(geo(geo(conic)))

viz = Visualizer(title="Tanga — conic through 5 points", space_dim=2)
viz.add(p1)
viz.add(p2)
viz.add(p3)
viz.add(p4)
viz.add(ap_a)
conic_viz = viz.new(conic)
viz.show()
viz.wait()

sys.exit(0)

matrix = conic_from_points(basis, points)
coeffs = to_coeffs(matrix)
mv = basis.multivector({1 << i: coeffs[i] for i in range(6)})

raw = analyze(mv)  # raw Conic (lossless)
specific = refine(raw)  # Ellipse / Circle / Hyperbola / ...

viz = Visualizer(title="Tanga — conic through 5 points", space_dim=2)
viz.add(specific, label=type(specific).__name__)
for p in points:
    viz.add(Point(p[0], p[1], 0.0), label=f"({p[0]:g}, {p[1]:g})")

print(f"Reconstructed conic refined to: {type(specific).__name__}")
viz.show()
viz.wait()
