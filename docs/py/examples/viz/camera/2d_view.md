# 2D orthographic view via View2DConfig

**Keywords:** camera · 2D · View2DConfig · orthographic

Demonstrates the 2D camera input spec:

- `xmin` / `xmax` / `ymin` / `ymax` define the visible data bounds.
- `border_world` adds a fixed world-unit margin (applied in Python).
- `border_px` adds a fixed pixel margin (applied by the frontend, since it
  needs the live viewport size).
- `stretch` selects the framing mode: `"fit"` (letterbox, default),
  `"fill"` (non-uniform stretch-to-fill), `"fill_x"` (x fills, y keeps
  aspect), or `"fill_y"` (y fills, x keeps aspect).

The `View2DConfig` can be passed directly to `Visualizer(camera=...)`.

## Run

```bash
uv run python py/examples/viz/camera/2d_view.py
```

## Source

[`viz/camera/2d_view.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/camera/2d_view.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""2d_view.py — 2D orthographic view via View2DConfig.

Demonstrates the 2D camera input spec:

- ``xmin`` / ``xmax`` / ``ymin`` / ``ymax`` define the visible data bounds.
- ``border_world`` adds a fixed world-unit margin (applied in Python).
- ``border_px`` adds a fixed pixel margin (applied by the frontend, since it
  needs the live viewport size).
- ``stretch`` selects the framing mode: ``"fit"`` (letterbox, default),
  ``"fill"`` (non-uniform stretch-to-fill), ``"fill_x"`` (x fills, y keeps
  aspect), or ``"fill_y"`` (y fills, x keeps aspect).

The ``View2DConfig`` can be passed directly to ``Visualizer(camera=...)``.

Run with:  uv run python py/examples/viz/camera/2d_view.py

Keywords: camera, 2D, View2DConfig, orthographic
"""

from pytanga.geometry import Point
from pytanga.viz import (
    Axes2D,
    Axes2DStyle,
    AxisStyle,
    Grid,
    GridStyle,
    LabelStyle,
    PointStyle,
    View2DConfig,
    Visualizer,
)

# Letterboxed (stretch="fit") with a world-unit margin and a pixel margin.
viz = Visualizer(
    title="Tanga — 2D Camera (View2DConfig, letterboxed)",
    camera=View2DConfig(
        xmin=-1.0,
        xmax=4.0,
        ymin=-1.0,
        ymax=3.0,
        border_world=0.5,
        border_px=40.0,
        stretch="fit",
    ),
)

viz.new(
    Axes2D((0, 0), range_u=(-1, 4), range_v=(-1, 3)),
    style=Axes2DStyle(
        u=AxisStyle(
            color="#ff4444",
            opacity=0.9,
            label_style=LabelStyle(font_size=20, align=(0.5, 0), offset_2d=(10, 20)),
        ),
        v=AxisStyle(
            color="#4488ff",
            opacity=0.9,
            label_style=LabelStyle(font_size=20, align=(1, 0.5), offset_2d=(0, 0)),
        ),
    ),
)
viz.new(
    Grid((0, 0), range_u=(-1, 4), range_v=(-1, 3)), style=GridStyle(color="#29af4b")
)

# Configure per-kind defaults once — no need to pass style/label_style on each add.
viz.styles.kind.merge(Point, PointStyle(size=0.15))
viz.styles.label_kind.merge(Point, LabelStyle(align=(0, 0)))

viz.new(Point(2, 1, 0), color="#ff4444", opacity=1.0, label="$P_1$")
viz.new(Point(-1, 2, 0), color="#44ff44", label="$P_2$")
viz.new(Point(0, -2, 0), color="#4444ff", label="$P_3$")

viz.show()
viz.wait()
````
