# degenerate quadric (plane pair) analysis + rendering

**Keywords:** quadric · plane pair · degenerate · refine · analyze · Q3

A rank-2 quadric is a degenerate quadric: the union of two planes (a "plane
pair"), the 3D analogue of a degenerate conic's line pair.  This demo builds an
intersecting and a parallel plane pair, shows them in the viewer, and
round-trips each through `create` → `analyze` → `refine` using Perwass's
degenerate-conic method (the two planes are recovered from the quadric's
eigen-decomposition as `√λ₊·v₊ ± √(−λ₋)·v₋`).

## Run

```bash
uv run python py/examples/ga/quadric/plane_pair_demo.py
```

## Source

[`ga/quadric/plane_pair_demo.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/ga/quadric/plane_pair_demo.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""plane_pair_demo.py — degenerate quadric (plane pair) analysis + rendering.

A rank-2 quadric is a degenerate quadric: the union of two planes (a "plane
pair"), the 3D analogue of a degenerate conic's line pair.  This demo builds an
intersecting and a parallel plane pair, shows them in the viewer, and
round-trips each through ``create`` → ``analyze`` → ``refine`` using Perwass's
degenerate-conic method (the two planes are recovered from the quadric's
eigen-decomposition as ``√λ₊·v₊ ± √(−λ₋)·v₋``).

Run with:  uv run python py/examples/ga/quadric/plane_pair_demo.py

Keywords: quadric, plane pair, degenerate, refine, analyze, Q3
"""

from pytanga.geometry import (
    Direction,
    Geometry,
    Plane,
    PlanePair,
    ParallelPlanePair,
    Point,
    refine,
)
from pytanga.quadric import BasisQ3
from pytanga.viz import Visualizer

geo = Geometry(BasisQ3(opns=True))
viz = Visualizer(title="Plane pair (degenerate quadric)")

# Two intersecting planes: x = 0 and y = 0.
pair = PlanePair(
    Plane(Point(0, 0, 0), Direction(1, 0, 0)),
    Plane(Point(0, 0, 0), Direction(0, 1, 0)),
)
viz.new(pair)

# Two parallel planes: x = 1 and x = -1.
parallel = ParallelPlanePair(
    Plane(Point(1, 0, 0), Direction(1, 0, 0)),
    Plane(Point(-1, 0, 0), Direction(1, 0, 0)),
)
viz.new(parallel)

# Round-trip: entity → MV → analyze → refine recovers the same pair.
for pair in (pair, parallel):
    quadric = geo.analyze(geo(pair))
    recovered = refine(quadric)
    print(f"kind={quadric.kind}  refine -> {type(recovered).__name__}")

viz.show()
````
