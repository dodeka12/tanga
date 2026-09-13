# Q3 point tuples (1–7 points) in distinct colors

**Keywords:** quadric · point tuple · PointSet · join · analyze · Q3 · Cayley-Bacharach

Joins `k` points (`k = 1…7`) in the 3D quadric space and analyzes each join
back into a point tuple: a single `Point` for `k = 1`, a `PointSet` for
`k ≥ 2`.  Each tuple is translated into its own quadrant of a 5×5×5 cube
before embedding, so the tuples do not overlap, and each is drawn in its own
color.  The 7-point tuple recovers eight points — the seven joined points plus
their Cayley–Bacharach partner (see `dev/theory/quadric-point-tuples.md`).

## Run

```bash
uv run python py/examples/ga/quadric/point_tuples_demo.py
```

## Source

[`ga/quadric/point_tuples_demo.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/ga/quadric/point_tuples_demo.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""point_tuples_demo.py — Q3 point tuples (1–7 points) in distinct colors.

Joins ``k`` points (``k = 1…7``) in the 3D quadric space and analyzes each join
back into a point tuple: a single ``Point`` for ``k = 1``, a ``PointSet`` for
``k ≥ 2``.  Each tuple is translated into its own quadrant of a 5×5×5 cube
before embedding, so the tuples do not overlap, and each is drawn in its own
color.  The 7-point tuple recovers eight points — the seven joined points plus
their Cayley–Bacharach partner (see ``dev/theory/quadric-point-tuples.md``).

Run with:  uv run python py/examples/ga/quadric/point_tuples_demo.py

Keywords: quadric, point tuple, PointSet, join, analyze, Q3, Cayley-Bacharach
"""

from typing import Any
from pytanga.geometry import Direction, Geometry, Point
from pytanga.quadric import BasisQ3
from pytanga.viz import Visualizer

# Seven base points in general position (each tuple uses the first k).
POINTS = (
    Point(0.1, 0.2, 0.3),
    Point(0.9, 0.1, -0.2),
    Point(-0.4, 0.7, 0.1),
    Point(0.3, -0.5, 0.8),
    Point(-0.6, -0.3, 0.5),
    Point(0.8, 0.6, -0.7),
    Point(-0.9, 0.5, -0.4),
)

# Seven quadrants of a 5×5×5 cube (octant centers at ±1.25), one per tuple.
TRANSLATIONS = (
    Direction(-1.25, -1.25, -1.25),
    Direction(-1.25, -1.25, 1.25),
    Direction(-1.25, 1.25, -1.25),
    Direction(-1.25, 1.25, 1.25),
    Direction(1.25, -1.25, -1.25),
    Direction(1.25, -1.25, 1.25),
    Direction(1.25, 1.25, -1.25),
)

# Okabe–Ito colorblind-safe palette (first seven).
COLORS = (
    "#e69f00",
    "#56b4e9",
    "#009e73",
    "#f0e442",
    "#0072b2",
    "#d55e00",
    "#cc79a7",
)


def _count(entity: Any) -> int:
    """Number of points an analyzed tuple displays (``Point`` → 1)."""
    points = getattr(entity, "points", None)
    return len(points) if points is not None else 1


Q3 = BasisQ3()
geo = Geometry(Q3)
viz = Visualizer(title="Tanga — Q3 point tuples (1–7)", space_dim=3)

for k in range(1, 8):
    translation = TRANSLATIONS[k - 1]
    pts = [p + translation for p in POINTS[:k]]
    mv = geo(pts[0])
    for p in pts[1:]:
        mv = mv ^ geo(p)
    entity = geo(mv)
    viz.new(entity, color=COLORS[k - 1], label=f"{k} point{'s' if k != 1 else ''}")
    print(f"k={k}: {type(entity).__name__} → {_count(entity)} point(s)")

viz.set_annotation(
    "Point tuples of size 1–7, each in its own color and its own quadrant of the "
    "5×5×5 cube.  The 7-point tuple recovers an eighth point (Cayley–Bacharach)."
)
viz.show()
viz.wait()
````
