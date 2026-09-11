# A 2×2 grid of 2D plots, one stretch mode per pane

**Keywords:** split view · panes · plotting · CoordinateSystem · fit_view2d · stretch · 2D

Four named scenes, each rendered by its own `CoordinateSystem` in a 2×2
`SplitView`.  Every pane embeds its camera via
`fit_view2d(..., stretch=...)` with a different mode, so the four framing
behaviours are visible side by side:

- `"fit"`    — letterbox: preserve aspect; one axis fills, the other is
  centred with empty space.
- `"fill"`   — stretch both axes to fill the pane (non-uniform).
- `"fill_x"` — x fills the pane, y keeps aspect (may overflow).
- `"fill_y"` — y fills the pane, x keeps aspect (may overflow).

The `CoordinateSystem` uses `camera=False` so it does not re-own the
camera — the per-pane `fit_view2d` camera is authoritative.

## Run

```bash
uv run python py/examples/viz/plotting/multi_plot.py
```

## Source

[`viz/plotting/multi_plot.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/plotting/multi_plot.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""multi_plot.py — A 2×2 grid of 2D plots, one stretch mode per pane.

Four named scenes, each rendered by its own ``CoordinateSystem`` in a 2×2
``SplitView``.  Every pane embeds its camera via
``fit_view2d(..., stretch=...)`` with a different mode, so the four framing
behaviours are visible side by side:

- ``"fit"``    — letterbox: preserve aspect; one axis fills, the other is
  centred with empty space.
- ``"fill"``   — stretch both axes to fill the pane (non-uniform).
- ``"fill_x"`` — x fills the pane, y keeps aspect (may overflow).
- ``"fill_y"`` — y fills the pane, x keeps aspect (may overflow).

The ``CoordinateSystem`` uses ``camera=False`` so it does not re-own the
camera — the per-pane ``fit_view2d`` camera is authoritative.

Run with:  uv run python py/examples/viz/plotting/multi_plot.py

Keywords: split view, panes, plotting, CoordinateSystem, fit_view2d, stretch, 2D
"""

import math

from pytanga.viz import (
    CoordinateSystem,
    PointPathStyle,
    SceneView,
    Size,
    SplitView,
    Visualizer,
    fit_view2d,
)

viz = Visualizer(
    reuse_existing=False,
    title="Tanga — Multi-Plot Split",
    space_dim=2,
    add_default_axes=False,
    add_default_grid=False,
)

# ── Top-left: fit (letterbox) ───────────────────────────────
fit = viz.scene("fit", space_dim=2, add_axes=False, add_grid=False)
fit_cs = CoordinateSystem(
    fit, xlim=(0, 2 * math.pi), ylim=(-1.2, 1.2), labels=("x", "sin(x)"), camera=False
)
fit_xs = [0.05 * i for i in range(int(2 * math.pi / 0.05) + 1)]
fit_cs.plot(
    fit_xs,
    [math.sin(x) for x in fit_xs],
    color="#ffcc00",
    style=PointPathStyle(line_thickness=2),
)

# ── Top-right: fill (stretch both axes) ─────────────────────
fill = viz.scene("fill", space_dim=2, add_axes=False, add_grid=False)
fill_cs = CoordinateSystem(
    fill, xlim=(-5, 5), ylim=(0, 25), labels=("x", "x^2"), camera=False
)
fill_xs = [0.1 * i for i in range(-50, 51)]
fill_cs.plot(
    fill_xs,
    [x * x for x in fill_xs],
    color="#44ff44",
    style=PointPathStyle(line_thickness=2),
)

# ── Bottom-left: fill_x (x fills, y keeps aspect) ───────────
fillx = viz.scene("fill_x", space_dim=2, add_axes=False, add_grid=False)
fillx_cs = CoordinateSystem(
    fillx, xlim=(0, 5), ylim=(0, 25), labels=("x", "x^2"), camera=False
)
fillx_xs = [0.1 * i for i in range(51)]
fillx_cs.plot(
    fillx_xs,
    [x * x for x in fillx_xs],
    color="#ff44cc",
    style=PointPathStyle(line_thickness=2),
)

# ── Bottom-right: fill_y (y fills, x keeps aspect) ──────────
filly = viz.scene("fill_y", space_dim=2, add_axes=False, add_grid=False)
filly_cs = CoordinateSystem(
    filly,
    xlim=(0, 40),
    ylim=(1.0, 1_000_000.0),
    yscale="log",
    labels=("x", "x^2 + x"),
    camera=False,
)
filly_xs = list(range(40))
filly_cs.plot(
    filly_xs,
    [x * x + x + 0.1 for x in filly_xs],
    color="#4488ff",
    style=PointPathStyle(line_thickness=2),
)

# A 2×2 grid: two rows, each a horizontal split of two panes.
layout = SplitView(
    orientation="vertical",
    sizes=[Size.percent(50), Size.percent(50)],
    children=[
        SplitView(
            orientation="horizontal",
            sizes=[Size.percent(50), Size.percent(50)],
            children=[
                SceneView(
                    "fit", camera=fit_view2d((0, 2 * math.pi), (-1.2, 1.2), stretch="fit")
                ),
                SceneView(
                    "fill", camera=fit_view2d((-5, 5), (0, 25), stretch="fill")
                ),
            ],
        ),
        SplitView(
            orientation="horizontal",
            sizes=[Size.percent(50), Size.percent(50)],
            children=[
                SceneView(
                    "fill_x", camera=fit_view2d((0, 5), (0, 25), stretch="fill_x")
                ),
                SceneView(
                    "fill_y",
                    camera=fit_view2d(
                        (0, 40), (1.0, 1_000_000.0), yscale="log", stretch="fill_y"
                    ),
                ),
            ],
        ),
    ],
)

viz.show(layout=layout)
print("2×2 plots, one stretch mode per pane. Press Ctrl+C to exit.")
viz.wait()
````
