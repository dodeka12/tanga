# reconstruct a quadric from 9 points and ray-render it

**Keywords:** quadric · quadric_from_points · ray · refine · analyze

Embeds nine points in the 3D projective quadric space, reconstructs the quadric
through them, and draws the raw `Quadric3D` (analytic ray renderer) next to
its refined `Ellipsoid` (standard mesh pipeline).

## Run

```bash
uv run python py/examples/ga/quadric/quadric3d_raycast.py
```

## Source

[`ga/quadric/quadric3d_raycast.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/ga/quadric/quadric3d_raycast.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""quadric3d_raycast.py — reconstruct a quadric from 9 points and ray-render it.

Embeds nine points in the 3D projective quadric space, reconstructs the quadric
through them, and draws the raw ``Quadric3D`` (analytic ray renderer) next to
its refined ``Ellipsoid`` (standard mesh pipeline).

Run with:  uv run python py/examples/ga/quadric/quadric3d_raycast.py

Keywords: quadric, quadric_from_points, ray, refine, analyze
"""

import math

from pytanga.geometry import analyze, refine
from pytanga.quadric import BasisQ3, quadric_from_points, to_coeffs
from pytanga.viz import Visualizer

# Nine points on the ellipsoid  x²/4 + y²/9 + z²/16 = 1.
a, b, c = 2.0, 3.0, 4.0
s = math.sqrt(3.0)
points = [
    (a, 0.0, 0.0),
    (-a, 0.0, 0.0),
    (0.0, b, 0.0),
    (0.0, -b, 0.0),
    (0.0, 0.0, c),
    (0.0, 0.0, -c),
    (a / s, b / s, c / s),
    (a / s, b / s, -c / s),
    (a / s, -b / s, c / s),
]

basis = BasisQ3(opns=False)
matrix = quadric_from_points(basis, points)
coeffs = to_coeffs(matrix)
mv = basis.multivector({1 << i: coeffs[i] for i in range(10)})

raw = analyze(mv)  # raw Quadric3D (rendered via the ray proxy by default)
specific = refine(raw)  # Ellipsoid (mesh pipeline)

viz = Visualizer(title="Tanga — quadric through 9 points")
viz.add(raw, label="Quadric3D (ray)")
viz.add(specific, label="Ellipsoid (mesh)")

print(f"Reconstructed quadric refined to: {type(specific).__name__}")
viz.show()
viz.wait()
````
