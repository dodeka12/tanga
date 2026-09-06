# Toggle one scene between a 2D and 3D view with a checkbox

**Keywords:** camera · 2D · 3D · checkbox · space_dim · switch view · plot

A single `CoordinateSystem` plot is drawn once.  A `CheckboxView` in a
`GroupView` overlay toggles the scene between a flat 2D orthographic view
(`space_dim=2`) and a tilted 3D perspective view (`space_dim=3`) via
`Visualizer.set_space_dim` — no reload, the same entities are re-framed live.

## Run

```bash
uv run python py/examples/viz/camera/switch_2d_3d.py
```

## Source

[`viz/camera/switch_2d_3d.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/camera/switch_2d_3d.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""switch_2d_3d.py — Toggle one scene between a 2D and 3D view with a checkbox.

A single ``CoordinateSystem`` plot is drawn once.  A ``CheckboxView`` in a
``GroupView`` overlay toggles the scene between a flat 2D orthographic view
(``space_dim=2``) and a tilted 3D perspective view (``space_dim=3``) via
``Visualizer.set_space_dim`` — no reload, the same entities are re-framed live.

Run with:  uv run python py/examples/viz/camera/switch_2d_3d.py

Keywords: camera, 2D, 3D, checkbox, space_dim, switch view, plot
"""

import math

from pytanga.viz import (
    CheckboxView,
    CoordinateSystem,
    EAnchor,
    GroupView,
    PointPathStyle,
    SceneView,
    View3dConfig,
    Visualizer,
)

_XLO, _XHI = 0.0, 2.0 * math.pi
_YLO, _YHI = -1.2, 1.2

viz = Visualizer(
    reuse_existing=False,
    title="Tanga — 2D/3D switch",
    space_dim=2,
    add_default_axes=False,
    add_default_grid=False,
)

scene = viz.scene("plot", space_dim=2, add_axes=False, add_grid=False)
cs = CoordinateSystem(
    scene,
    xlim=(_XLO, _XHI),
    ylim=(_YLO, _YHI),
    labels=("x", "sin(x)"),
)
xs = [0.05 * i for i in range(int(_XHI / 0.05) + 1)]
cs.plot(xs, [math.sin(x) for x in xs], color="#ffcc00", style=PointPathStyle(line_thickness=3))

# The 2D camera the CoordinateSystem fitted (with label margins), and a tilted
# 3D perspective view of the same flat plot plane.
cam_2d = scene.scene.config.camera
cam_3d = View3dConfig(
    point=(0.0, 0.0, 0.0),
    normal=(0.3, 0.4, 1.0),
    extent_u=8.0,
    extent_v=6.0,
    fov=50.0,
)


async def _on_3d(value, _event):
    if value:
        viz.set_space_dim(3, scene_name="plot", camera=cam_3d)
    else:
        viz.set_space_dim(2, scene_name="plot", camera=cam_2d)


layout = SceneView(
    "plot",
    overlay=[
        GroupView(
            "View mode",
            [CheckboxView("mode3d", label="3D", value=False, on_change=_on_3d)],
            position=EAnchor.TOP_LEFT,
        ),
    ],
)

if __name__ == "__main__":
    viz.show(layout=layout)
    print("Toggle the '3D' checkbox to switch the plot between 2D and 3D. Ctrl+C to exit.")
    viz.wait()
````
