# a plot on a tilted background plane in 3D

**Keywords:** plotting · 3D · tilted plane

The whole coordinate system (background plane, grid, axes, and the plotted
point path) lives in one group, placed/oriented by `position`/`normal`/
`up` so it can sit anywhere in 3D space.  `vline`/`hline` draw annotation
lines at fixed data values on the same plane.

## Run

```bash
uv run python py/examples/viz/plotting/plot_3d.py
```

## Source

[`viz/plotting/plot_3d.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/plotting/plot_3d.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""plot_3d.py — a plot on a tilted background plane in 3D.

The whole coordinate system (background plane, grid, axes, and the plotted
point path) lives in one group, placed/oriented by ``position``/``normal``/
``up`` so it can sit anywhere in 3D space.  ``vline``/``hline`` draw annotation
lines at fixed data values on the same plane.

Run with:  uv run python py/examples/viz/plotting/plot_3d.py

Keywords: plotting, 3D, tilted plane
"""

import math

from pytanga.viz import CoordinateSystem, PointPathStyle, Visualizer

viz = Visualizer(
    title="Tanga — 3D Plot on a Tilted Plane",
    add_default_axes=True,
    add_default_grid=False,
)

cs = CoordinateSystem(
    viz,
    xlim=(0.0, 4.0 * math.pi),
    ylim=(-1.5, 1.5),
    size=(2.0, 1.0),  # plane is 2×1 world units; data is stretched onto it
    labels=("x", "sin(x)"),
    position=(-2.0, 1.5, -2.0),
    normal=(1.0, 0.0, 1.0),
    up=(0.0, 1.0, 0.0),
    align=(0, 0),
    axis_origin=(0, 0),
)

xs = [0.1 * i for i in range(0, 126)]  # 0 .. 12.5
ys = [math.sin(x) for x in xs]
cs.plot(xs, ys, color="#44ff44", style=PointPathStyle(line_thickness=3))

# Annotation lines at fixed data values (rendered on the tilted plane).
cs.vline(x=math.pi, name="pi", color="#ff5555")
cs.hline(y=0.0, name="zero", color="#8888ff")

viz.show()
viz.wait()
````
