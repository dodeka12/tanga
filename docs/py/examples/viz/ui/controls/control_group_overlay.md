# Declarative control groups: overlay + 3D-anchored

**Keywords:** control group · GroupView · overlay · anchor · parent_id · layout

Two `GroupView` overlays declared on the base `SceneView` (the unified
`GroupView` path):

- an **overlay-anchored** group (`position="top-right"`), and
- a group **anchored to a 3D object** (`parent_id=...`) that follows the sphere
  via the CSS2D attach path.

## Run

```bash
uv run python py/examples/viz/ui/controls/control_group_overlay.py
```

## Source

[`viz/ui/controls/control_group_overlay.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/ui/controls/control_group_overlay.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""control_group_overlay.py — Declarative control groups: overlay + 3D-anchored.

Two ``GroupView`` overlays declared on the base ``SceneView`` (the unified
``GroupView`` path):

- an **overlay-anchored** group (``position="top-right"``), and
- a group **anchored to a 3D object** (``parent_id=...``) that follows the sphere
  via the CSS2D attach path.

Run with:  uv run python py/examples/viz/ui/controls/control_group_overlay.py

Keywords: control group, GroupView, overlay, anchor, parent_id, layout
"""

from pytanga.geometry import Point, Sphere
from pytanga.viz import ButtonView, GroupView, SceneView, SliderView, StackView, Visualizer

viz = Visualizer(reuse_existing=False, title="Tanga — Control Groups")
viz.add(
    Sphere(Point(0, 0, 0), radius=2), entity_id="sphere", color="#4488ff", opacity=0.4
)


async def _on_radius(value, _event):
    viz.update_entity("sphere", Sphere(Point(0, 0, 0), radius=float(value)))
    viz.flush()


async def _on_opacity(value, _event):
    viz.update("sphere", opacity=float(value))
    viz.flush()


async def _on_reset(_value, _event):
    viz.update_entity("sphere", Sphere(Point(0, 0, 0), radius=2))
    viz.update("sphere", opacity=0.4)
    viz.flush()


viz.show(
    layout=StackView(
        "vertical",
        [
            SceneView(
                "",
                overlay=[
                    GroupView(
                        "View",
                        [
                            SliderView(
                                "radius", label="Radius", min=0.2, max=5.0, value=2.0,
                                on_change=_on_radius,
                            ),
                            ButtonView("reset", label="Reset", on_click=_on_reset),
                        ],
                        position="top-right",
                    ),
                    GroupView(
                        "Sphere",
                        [
                            SliderView(
                                "opacity", label="Opacity", min=0.05, max=1.0, value=0.4,
                                on_change=_on_opacity,
                            ),
                        ],
                        parent_id="sphere",
                    ),
                ],
            )
        ],
    )
)
print("Overlay and attached control groups shown. Press Ctrl+C to exit.")
viz.wait()
````
