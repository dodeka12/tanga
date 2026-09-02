# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""theme_switching.py — Switch the viewer theme at runtime without a reload.

Two buttons call ``viz.set_theme(...)`` from their ``on_click`` handlers, which
pushes a ``theme_define`` message so the connected viewer swaps its theme CSS
live (no page reload).  A slider and a checkbox are included so the change is
visible across controls.  The theme layers live under
``pytanga/viz/templates/themes/`` (``base.css`` + per-theme ``tokens.css``).

Run with:  uv run python py/examples/viz/scenes/theme_switching.py

Keywords: scenes, theme, set_theme, runtime, controls, light, dark
"""

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ButtonView,
    CheckboxView,
    EAnchor,
    GroupView,
    SceneView,
    SliderView,
    Visualizer,
)

viz = Visualizer(reuse_existing=False, title="Tanga — Theme Switching")

viz.add(
    Sphere(Point(0, 0, 0), radius=2), entity_id="sphere", color="#4488ff", opacity=0.3
)
viz.add(Point(1, 1, 1), color="#ff4444")


async def _on_radius(value, _event):
    viz.update_entity("sphere", Sphere(Point(0, 0, 0), radius=float(value)))
    viz.flush()


async def _set_dark(_value, _event):
    viz.set_theme("dark")


async def _set_light(_value, _event):
    viz.set_theme("light")


layout = SceneView(
    "",
    overlay=[
        GroupView(
            "Theme",
            [
                SliderView(
                    "radius",
                    label="Radius",
                    min=0.1,
                    max=5.0,
                    value=2.0,
                    on_change=_on_radius,
                ),
                CheckboxView("wire", label="Wireframe", value=False),
                ButtonView("btn_dark", label="Dark", on_click=_set_dark),
                ButtonView("btn_light", label="Light", on_click=_set_light),
            ],
            position=EAnchor.TOP_LEFT,
        ),
    ],
)

viz.show(layout=layout)
print("Click the buttons to switch themes live. Press Ctrl+C to exit.")
viz.wait()
