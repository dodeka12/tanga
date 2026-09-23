# intersect two 2D conics (a point tuple)

**Keywords:** quadric · conic · intersection · pencil · PointSet · Q2

Builds two conics as IPNS grade-1 blades with `geo.create(Conic(m))`, takes
their outer product (the pencil `c1 ^ c2`), and analyzes it: the intersection
of two conics is a **point tuple** — a `PointSet` of up to four points,
recovered via the pencil method.

## Run

```bash
uv run python py/examples/ga/quadric/conic_intersection_demo.py
```

## Source

[`ga/quadric/conic_intersection_demo.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/ga/quadric/conic_intersection_demo.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""conic_intersection_demo.py — intersect two 2D conics (a point tuple).

Builds two conics as IPNS grade-1 blades with ``geo.create(Conic(m))``, takes
their outer product (the pencil ``c1 ^ c2``), and analyzes it: the intersection
of two conics is a **point tuple** — a ``PointSet`` of up to four points,
recovered via the pencil method.

Run with:  uv run python py/examples/ga/quadric/conic_intersection_demo.py

Keywords: quadric, conic, intersection, pencil, PointSet, Q2
"""

import numpy as np

from typing import Any

from pytanga.geometry import Geometry
from pytanga.quadric import BasisQ2, Conic
from pytanga.viz import Visualizer

geo = Geometry(BasisQ2(opns=False))


def _intersect(m1: np.ndarray, m2: np.ndarray) -> Any:
    """Intersect two 3×3 conic matrices via the GA pencil ``c1 ^ c2``."""
    c1 = geo.create(Conic(m1))
    c2 = geo.create(Conic(m2))
    return geo.analyze(c1 ^ c2)


# Two ellipses → four intersection points.
a = np.diag([0.25, 1.0, -1.0])  # x²/4 + y² = 1
b = np.diag([1.0, 0.25, -1.0])  # x² + y²/4 = 1
result = _intersect(a, b)
print(f"two ellipses: {len(result)} point(s)")
for p in result:
    print(f"  ({p.x:.4f}, {p.y:.4f})")

viz = Visualizer(title="Tanga — conic intersection (point tuple)", space_dim=2)
viz.add(result, label="conic ∩ conic")
viz.show()
viz.wait()
````
