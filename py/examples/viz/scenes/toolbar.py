# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""toolbar.py — A horizontal control toolbar nested inside a vertical stack.

Builds a ``SplitView`` layout with a control pane beside a 3D scene.  The
control pane is a vertical :class:`~pytanga.viz.StackView` whose first element
is a **horizontal toolbar** — another :class:`~pytanga.viz.StackView` with
``direction="horizontal"`` holding a row of buttons and a dropdown.  This shows
two things at once:

- controls can be stacked **horizontally** (a toolbar row);
- a horizontal stack nests inside a vertical stack (stacks compose to any depth).

Toolbar controls are just views with the usual ``on_click``/``on_change``
handlers: the buttons fit/reset the camera and the dropdown updates the
annotation.

Run with:  uv run python py/examples/viz/scenes/toolbar.py

Keywords: scenes, stack view, toolbar, horizontal, layout, controls
"""

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ButtonView,
    CameraConfig3d,
    DropdownView,
    SceneView,
    Size,
    SliderView,
    SplitView,
    StackView,
    Visualizer,
)

viz = Visualizer(reuse_existing=False, title="Tanga — Toolbar")

# Main scene content (the default scene, name "").
viz.add(
    Sphere(Point(0, 0, 0), radius=2), entity_id="sphere", color="#4488ff", opacity=0.3
)
viz.add(Point(1, 1, 1), color="#ff4444")


async def _on_radius(value, _event):
    viz.update_entity("sphere", Sphere(Point(0, 0, 0), radius=float(value)))
    viz.flush()


async def _on_fit(_value, _event):
    viz.flush(fit_camera=True)


async def _on_reset(_value, _event):
    viz.set_camera(CameraConfig3d(position=(0.0, 0.0, 8.0), target=(0.0, 0.0, 0.0)))


async def _on_mode(value, _event):
    viz.set_annotation(f"Mode: {value}")


# A horizontal toolbar: a row of controls (buttons + a dropdown).
toolbar = StackView(
    "horizontal",
    [
        ButtonView("btn_fit", label="Fit camera", on_click=_on_fit),
        ButtonView("btn_reset", label="Reset view", on_click=_on_reset),
        DropdownView(
            "dd_mode",
            label="Mode",
            options=["Wire", "Solid"],
            value="Wire",
            on_change=_on_mode,
        ),
    ],
)

# The control pane: a vertical stack whose first element is the toolbar row.
controls = StackView(
    "vertical",
    [
        toolbar,
        SliderView(
            "radius",
            label="Radius",
            min=0.1,
            max=5.0,
            value=2.0,
            on_change=_on_radius,
        ),
    ],
)

layout = SplitView(
    orientation="horizontal",
    sizes=[Size.percent(35), Size.percent(65)],
    children=[
        controls,
        SceneView(""),
    ],
)

viz.show(layout=layout)
print("Toolbar layout is shown at a single URL. Press Ctrl+C to exit.")
viz.wait()
