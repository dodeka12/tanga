# Smooth CSG in the standard viewer

**Keywords:** SDF · smooth CSG · smooth_union · smooth_intersection · smoothness

Shows the smooth combinators (`smooth_union`/`smooth_intersection` with a
per-member `smoothness` blend radius) on the standard viewer's unified SDF
object model: a sphere and a vertical cylinder are joined with a smooth union,
and the result is intersected with a second (offset) cylinder using a smooth
intersection — one ray-marched solid with rounded fillets instead of hard seams.

## Run

```bash
uv run python py/examples/viz/sdf/smooth_csg.py
```

## Source

[`viz/sdf/smooth_csg.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/sdf/smooth_csg.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""smooth_csg.py — Smooth CSG in the standard viewer.

Shows the smooth combinators (``smooth_union``/``smooth_intersection`` with a
per-member ``smoothness`` blend radius) on the standard viewer's unified SDF
object model: a sphere and a vertical cylinder are joined with a smooth union,
and the result is intersected with a second (offset) cylinder using a smooth
intersection — one ray-marched solid with rounded fillets instead of hard seams.

Run with:  uv run python py/examples/viz/sdf/smooth_csg.py

Keywords: SDF, smooth CSG, smooth_union, smooth_intersection, smoothness
"""

from pytanga.viz import SdfStyle, Visualizer
from pytanga.viz.sdf import Composed, ECompose, SdfCompose, capped_cylinder, sphere

viz = Visualizer(title="Tanga — Smooth CSG")
viz.show()

# (sphere ∪ column) ∩ cutter, with rounded fillets between every member.
# `capped_cylinder` is the bounded form of a cylinder along +Y.
piece = Composed(
    sphere(1.1, id="ball"),
    SdfCompose(
        capped_cylinder(1.6, 0.5, id="column"),
        ECompose.SMOOTH_UNION,
        smoothness=0.2,
    ),
    SdfCompose(
        capped_cylinder(1.6, 0.75, position=(0.35, 0.0, 0.0), id="cutter"),
        ECompose.SMOOTH_INTERSECTION,
        smoothness=0.2,
    ),
)

viz.add(piece, style=SdfStyle(color="#ffaa00"), label="smooth CSG solid")

viz.flush()

print("A sphere and a cylinder are smoothly united, then smoothly intersected")
print("with an offset cylinder — one ray-marched solid with rounded fillets.")
print("Close the browser window or press Ctrl+C to exit.")

viz.wait()
````
