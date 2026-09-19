# fixed screen-space axes + grid overlay in 2D

**Keywords:** camera · 2D · CoordinateSystem · overlay · underlay · axes · grid

`CoordinateSystem(display_mode="overlay")` draws the coordinate axes as a
fixed overlay frame at the image borders and the grid as an underlay behind the
data, while the plotted data still pans/zooms underneath.  As you pan/zoom the
data with the mouse, the frame stays put and its tick values + grid lines update
to the current visible range (nice 1/2/5 × 10^k steps).

Pan and zoom are bounded by the data range by default; the tick density adapts
to the viewport (`min_tick_spacing_px`).  These can be configured per axis,
e.g.::

    CoordinateSystem(viz, display_mode="overlay",
                     xlim=(0, 1000), ylim=(0, 0.1),
                     x_intervals=[50, 100, 200, 500],
                     y_intervals=[0.01, 0.02, 0.05],
                     pan_xlim=(-200, 1200), pan_ylim=(-0.05, 0.15),
                     min_zoom=0.5, max_zoom=40.0)

## Run

```bash
uv run python py/examples/viz/camera/axes_overlay_2d.py
```

## Source

[`viz/camera/axes_overlay_2d.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/camera/axes_overlay_2d.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""axes_overlay_2d.py — fixed screen-space axes + grid overlay in 2D.

``CoordinateSystem(display_mode="overlay")`` draws the coordinate axes as a
fixed overlay frame at the image borders and the grid as an underlay behind the
data, while the plotted data still pans/zooms underneath.  As you pan/zoom the
data with the mouse, the frame stays put and its tick values + grid lines update
to the current visible range (nice 1/2/5 × 10^k steps).

Pan and zoom are bounded by the data range by default; the tick density adapts
to the viewport (``min_tick_spacing_px``).  These can be configured per axis,
e.g.::

    CoordinateSystem(viz, display_mode="overlay",
                     xlim=(0, 1000), ylim=(0, 0.1),
                     x_intervals=[50, 100, 200, 500],
                     y_intervals=[0.01, 0.02, 0.05],
                     pan_xlim=(-200, 1200), pan_ylim=(-0.05, 0.15),
                     min_zoom=0.5, max_zoom=40.0)

Run with:  uv run python py/examples/viz/camera/axes_overlay_2d.py

Keywords: camera, 2D, CoordinateSystem, overlay, underlay, axes, grid
"""

import math

from pytanga.viz import CoordinateSystem, Visualizer

viz = Visualizer(
    space_dim=2,
    add_default_axes=False,
    add_default_grid=False,
    title="Tanga — 2D Overlay Coordinate System",
    annotation=(
        "## Fixed overlay axes + underlay grid\n\n"
        "The coordinate axes stay at the image borders while the data pans/zooms.\n\n"
        "*Right-drag to pan · scroll to zoom.*"
    ),
)

cs = CoordinateSystem(
    viz,
    display_mode="overlay",
    xlim=(0.0, 2.0 * math.pi),
    ylim=(-1.5, 1.5),
    labels=("x", "sin(x)"),
)

xs = [i * 2.0 * math.pi / 200 for i in range(201)]
cs.plot(xs, [math.sin(x) for x in xs], color="#ff4444")

viz.show()
viz.wait()
````
