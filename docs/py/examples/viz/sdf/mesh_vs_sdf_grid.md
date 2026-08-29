# every solid object as a mesh next to its SDF twin

**Keywords:** SDF · mesh · comparison

Two rows of the same objects, laid out in a grid:

- **top row**   — the normal vertex/mesh pipeline (`Visualizer` default).
- **bottom row** — the same objects as ray-marched SDF solids via
  `SdfObject` + per-entity `Sdf*Style`.

Each column holds one shape; the mesh twin sits above its SDF twin.  This makes
it easy to compare the mesh and SDF renderings of the same geometry.

## Run

```bash
uv run python py/examples/viz/sdf/mesh_vs_sdf_grid.py
```

## Source

[`viz/sdf/mesh_vs_sdf_grid.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/sdf/mesh_vs_sdf_grid.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""mesh_vs_sdf_grid.py — every solid object as a mesh next to its SDF twin.

Two rows of the same objects, laid out in a grid:

- **top row**   — the normal vertex/mesh pipeline (``Visualizer`` default).
- **bottom row** — the same objects as ray-marched SDF solids via
  ``SdfObject`` + per-entity ``Sdf*Style``.

Each column holds one shape; the mesh twin sits above its SDF twin.  This makes
it easy to compare the mesh and SDF renderings of the same geometry.

Run with:  uv run python py/examples/viz/sdf/mesh_vs_sdf_grid.py

Keywords: SDF, mesh, comparison
"""

import math

from pytanga.geometry import (
    Box,
    Cylinder,
    Direction,
    Disk,
    Ellipse,
    Ellipsoid,
    PartialDisk,
    Point,
    RegularPolygon,
    Sphere,
)
from pytanga.viz import (
    SdfBoxStyle,
    SdfCylinderStyle,
    SdfDiskStyle,
    SdfEllipseStyle,
    SdfEllipsoidStyle,
    SdfPartialDiskStyle,
    SdfRegularPolygonStyle,
    SdfSphereStyle,
    Visualizer,
)
from pytanga.viz.sdf import SdfObject

# Each entry: (name, entity factory taking a center Point, matching SDF style).
_SHAPES = [
    ("Sphere", lambda c: Sphere(c, 0.7), SdfSphereStyle),
    (
        "Cylinder",
        lambda c: Cylinder(
            origin=c,
            axis=Direction(0, 0, 1),
            length=1.4,
            radius=0.35,
            align_center=0.5,
        ),
        SdfCylinderStyle,
    ),
    ("Disk", lambda c: Disk(center=c, radius=0.7), SdfDiskStyle),
    (
        "PartialDisk",
        lambda c: PartialDisk(
            center=c,
            radius=0.7,
            angle=math.pi * 1.3,
            start_direction=Direction(1, 0, 0),
        ),
        SdfPartialDiskStyle,
    ),
    ("Box", lambda c: Box(center=c, size=(1.0, 0.9, 0.7)), SdfBoxStyle),
    (
        "Ellipsoid",
        lambda c: Ellipsoid(center=c, radii=(0.7, 0.5, 0.55)),
        SdfEllipsoidStyle,
    ),
    (
        "Ellipse",
        lambda c: Ellipse(center=c, radius_u=0.7, radius_v=0.45),
        SdfEllipseStyle,
    ),
    (
        "RegularPolygon",
        lambda c: RegularPolygon(center=c, radius=0.65, sides=6),
        SdfRegularPolygonStyle,
    ),
]

_MESH_Y = 2.2  # top row (mesh pipeline)
_SDF_Y = -2.2  # bottom row (ray-marched SDF)
_X_STEP = 2.2
_ORIGIN_X = -(_X_STEP * (len(_SHAPES) - 1)) / 2.0

# A distinct colour per column, shared by the mesh and SDF twins.
_COLORS = [
    "#ff8844",
    "#44aaff",
    "#ffcc44",
    "#44ffaa",
    "#88ccff",
    "#ffaa00",
    "#ff44ff",
    "#66cc99",
]

viz = Visualizer(title="Tanga — Mesh vs SDF (grid)", add_default_grid=False)

# Add everything *before* ``show()`` so the initial scene push already contains
# the full grid (no post-show flush/refresh required).
for col, ((name, make_entity, sdf_style), color) in enumerate(zip(_SHAPES, _COLORS)):
    x = _ORIGIN_X + col * _X_STEP
    mesh_center = Point(x, _MESH_Y, 0)
    sdf_center = Point(x, _SDF_Y, 0)

    # Mesh twin (vertex pipeline).
    viz.add(make_entity(mesh_center), color=color, label=f"{name} (mesh)")

    # SDF twin (ray-marched solid).
    viz.add(
        SdfObject(make_entity(sdf_center), style=sdf_style(color=color)),
        label=f"{name} (SDF)",
    )

print("Each column shows one shape: its mesh twin above, its SDF twin below.")
print("Close the browser window or press Ctrl+C to exit.")

viz.show()
viz.wait()
````
