# Composed SDF objects + the primitive library

**Keywords:** SDF · Composed · primitive library

Builds a "bead": a sphere with a vertical cylinder bored through it, expressed
as a single `Composed` object whose constituents each carry their own
combine mode. A torus and a box drawn from the primitive library sit alongside
for reference.

## Run

```bash
uv run python py/examples/viz/sdf/composed.py
```

## Source

[`viz/sdf/composed.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/sdf/composed.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""composed.py — Composed SDF objects + the primitive library.

Builds a "bead": a sphere with a vertical cylinder bored through it, expressed
as a single :class:`Composed` object whose constituents each carry their own
combine mode. A torus and a box drawn from the primitive library sit alongside
for reference.

Run with:  uv run python py/examples/viz/sdf/composed.py

Keywords: SDF, Composed, primitive library
"""

import math

from pytanga.geometry import Direction, GeneralRotor, Point
from pytanga.viz.sdf import (
    Composed,
    ECompose,
    SdfCompose,
    SdfVisualizer,
    box,
    capped_cylinder,
    sphere,
    torus,
)

viz = SdfVisualizer(title="Tanga SDF — Composed objects")

# A sphere with a vertical cylinder removed (a bead). The whole thing is ONE
# drawable object with ONE material/color; the cylinder is a `subtract`
# constituent that carves a hole.
bead = Composed(
    sphere(0.7, position=(0.0, 0.0, 0.0)),
    SdfCompose(
        capped_cylinder(1.0, 0.45, position=(0.0, 0.0, 0.0)),
        ECompose.SUBTRACT,
    ),
)
viz.add(bead, color="#ffaa00")

# A standalone torus from the primitive library.
viz.add(torus(1.1, 0.12, position=(3.2, 0.0, 0.0)), color="#44ff44")

# A standalone box from the primitive library.
viz.add(box((0.9, 0.9, 0.9), position=(-3.2, 0.0, 0.0)), color="#4499ff")

viz.add(GeneralRotor(math.radians(90), axis=Direction(1, 1, 1), origin=Point(1, 1, 1)))

print("Opening the SDF viewer. An orange bead (sphere with a cylinder bored")
print("out), a green torus, and a blue box should be visible.")
print("Drag to orbit, right/middle-drag to pan, scroll to zoom.")

viz.show()
viz.wait()
````
