# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""controls_add_and_view.py — Declarative controls drive a sphere.

A single sphere is driven by a declarative ``GroupView`` overlay holding a
``SliderView``, ``CheckboxView``, and ``ButtonView`` on a ``SceneView``.  Each
control shares one async ``(value, event)`` handler; dragging the slider or
toggling the checkbox updates the sphere in place.

Run with:  uv run python py/examples/viz/ui/controls/controls_add_and_view.py

Keywords: controls, SliderView, CheckboxView, ButtonView, GroupView, scene
"""

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ButtonView,
    CheckboxView,
    EAnchor,
    EIconMaterial,
    GroupView,
    SceneView,
    SliderView,
    Visualizer,
)

viz = Visualizer(reuse_existing=False, title="Tanga — Declarative controls")
viz.add(
    Sphere(Point(0, 0, 0), radius=2), entity_id="sphere", color="#4488ff", opacity=0.4
)


async def _on_radius(value, _event):
    radius = float(value)
    viz.update_entity("sphere", Sphere(Point(0, 0, 0), radius=radius))
    viz.flush()


async def _on_wireframe(value, _event):
    viz.update("sphere", wireframe=bool(value))
    viz.flush()


async def _on_reset(_value, _event):
    viz.update_entity("sphere", Sphere(Point(0, 0, 0), radius=2))
    viz.update("sphere", wireframe=False)
    viz.flush()


layout = SceneView(
    "",
    overlay=[
        GroupView(
            "Controls",
            [
                SliderView(
                    "radius",
                    label="Radius",
                    min=0.2,
                    max=5.0,
                    value=2.0,
                    on_change=_on_radius,
                ),
                CheckboxView(
                    "wireframe",
                    label="Wireframe",
                    value=False,
                    on_change=_on_wireframe,
                ),
                ButtonView("reset", label="Reset", on_click=_on_reset),
            ],
            icon=EIconMaterial.SETTINGS,
            position=EAnchor.TOP_LEFT,
        ),
    ],
)

viz.show(layout=layout)
print("Declarative controls drive the sphere. Press Ctrl+C to exit.")
viz.wait()
