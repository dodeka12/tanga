# per-object CSG combine modes

**Keywords:** SDF · CSG · combine · polarity

Demonstrates the `combine=`/`polarity=` API across *separate* scene objects
(distinct from `Composed`, which `composed.py` covers): a
positive sphere, a negative sphere carving a cavity, and an intersecting sphere
whose overlap with the base is kept. Each object keeps its own material; a
subtracting object emits no colored surface of its own.

## Run

```bash
uv run python py/examples/viz/sdf/booleans.py
```

## Source

[`viz/sdf/booleans.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/sdf/booleans.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""booleans.py — per-object CSG combine modes.

Demonstrates the ``combine=``/``polarity=`` API across *separate* scene objects
(distinct from :class:`Composed`, which ``composed.py`` covers): a
positive sphere, a negative sphere carving a cavity, and an intersecting sphere
whose overlap with the base is kept. Each object keeps its own material; a
subtracting object emits no colored surface of its own.

Run with:  uv run python py/examples/viz/sdf/booleans.py

Keywords: SDF, CSG, combine, polarity
"""

from pytanga.geometry import Point, Sphere
from pytanga.viz.sdf import SdfVisualizer

viz = SdfVisualizer(title="Tanga SDF — Boolean combine modes")

# Union (the default): the base positive sphere.
viz.add(Sphere(Point(0, 0, 0), 1.6), color="#ffaa00")

# Subtract: a negative sphere carves a concave cavity out of the base.
viz.add(Sphere(Point(0.9, 0.5, 0), 0.8), combine="subtract")

# Intersection: keep only the overlap lens of this sphere with the (carved) base.
viz.add(Sphere(Point(-1.1, 0, 0), 1.2), color="#44aaff", combine="intersection")

print("Boolean combine modes: an orange sphere, a carved cavity (subtract), and")
print("a blue overlap lens (intersection). Try smooth variants with")
print("combine='smooth_subtract'/'smooth_union' and a smoothness= knob.")

viz.show()
viz.wait()
````
