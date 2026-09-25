# Hide/show a sphere and its controls from a split layout

**Keywords:** hide · show · visible · enable · disable · checkbox · slider · split view · sphere

A horizontal `SplitView` puts a control panel on the left and a sphere in a
`SceneView` pane on the right.  A `CheckboxView` toggles the sphere's
visibility and, at the same time, hides/shows the radius slider (a single
control's state is pushed without re-building the layout).  A second checkbox
disables (greys out) the radius slider to demonstrate the enabled/disabled
state.

## Run

```bash
uv run python py/examples/viz/ui/controls/hide_sphere.py
```

## Source

[`viz/ui/controls/hide_sphere.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/ui/controls/hide_sphere.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""hide_sphere.py — Hide/show a sphere and its controls from a split layout.

A horizontal ``SplitView`` puts a control panel on the left and a sphere in a
``SceneView`` pane on the right.  A ``CheckboxView`` toggles the sphere's
visibility and, at the same time, hides/shows the radius slider (a single
control's state is pushed without re-building the layout).  A second checkbox
disables (greys out) the radius slider to demonstrate the enabled/disabled
state.

Run with:  uv run python py/examples/viz/ui/controls/hide_sphere.py

Keywords: hide, show, visible, enable, disable, checkbox, slider, split view, sphere
"""

from typing import Any

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    CheckboxView,
    ControlEvent,
    GroupView,
    SceneView,
    SliderView,
    SplitView,
    Visualizer,
)

viz = Visualizer(reuse_existing=False, title="Tanga — Hide / show a sphere")

viz.add(
    Sphere(Point(0, 0, 0), radius=2), entity_id="sphere", color="#4488ff", opacity=0.4
)


async def _on_show(value: Any, _event: ControlEvent) -> None:
    show = bool(value)
    # Hide/show the sphere entity …
    viz.set_visible("sphere", show)
    # … and hide/show the radius slider at the same time (no layout re-push).
    viz.set_control_visible("radius", show)
    viz.flush()


async def _on_radius(value: Any, _event: ControlEvent) -> None:
    viz.update_entity("sphere", Sphere(Point(0, 0, 0), radius=float(value)))
    viz.flush()


async def _on_enable_radius(value: Any, _event: ControlEvent) -> None:
    # Disable (grey out) the radius slider without hiding it.
    viz.set_control_enabled("radius", bool(value))


layout = SplitView(
    orientation="horizontal",
    children=[
        GroupView(
            "Controls",
            [
                CheckboxView(
                    "show_sphere", label="Show sphere", value=True, on_change=_on_show
                ),
                SliderView(
                    "radius",
                    label="Radius",
                    min=0.2,
                    max=5.0,
                    value=2.0,
                    on_change=_on_radius,
                ),
                CheckboxView(
                    "enable_radius",
                    label="Enable radius",
                    value=True,
                    on_change=_on_enable_radius,
                ),
            ],
        ),
        SceneView(""),
    ],
)

viz.show(layout=layout)
print("Sphere + controls shown in a split view. Press Ctrl+C to exit.")
viz.wait()
````
