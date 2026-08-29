# reconstruct a conic from 5 points and draw its refined entity

**Keywords:** quadric · conic · conic_from_points · refine · analyze

Embeds five points in the 2D projective quadric (conic) space, reconstructs the
conic through them, and refines the raw `Conic` to a concrete 2D entity
(`Circle` / `Ellipse` / `Hyperbola` / `Parabola` / line pair) drawn in
the standard viewer alongside the five points.

## Run

```bash
uv run python py/examples/ga/quadric/conic_demo.py
```

## Source

[`ga/quadric/conic_demo.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/ga/quadric/conic_demo.py)

## Code

````python
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

from pytanga.geometry import Point, analyze, refine
from pytanga.quadric import BasisQ2, conic_from_points, to_coeffs
from pytanga.viz import Visualizer

# Five points on the ellipse  x²/4 + y² = 1  (no three collinear).
points = [
    (2.0, 0.0),
    (-2.0, 0.0),
    (0.0, 1.0),
    (0.0, -1.0),
    (math.sqrt(3.0), 0.5),
]

basis = BasisQ2(opns=False)
matrix = conic_from_points(basis, points)
coeffs = to_coeffs(matrix)
mv = basis.multivector({1 << i: coeffs[i] for i in range(6)})

raw = analyze(mv)          # raw Conic (lossless)
specific = refine(raw)     # Ellipse / Circle / Hyperbola / ...

viz = Visualizer(title="Tanga — conic through 5 points", space_dim=2)
viz.add(specific, label=type(specific).__name__)
for p in points:
    viz.add(Point(p[0], p[1], 0.0), label=f"({p[0]:g}, {p[1]:g})")

print(f"Reconstructed conic refined to: {type(specific).__name__}")
viz.show()
viz.wait()
````
