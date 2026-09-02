# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""custom_theme_override.py — A custom theme with a full button/checkbox override.

Adds a ``pastel`` theme whose token sheet re-themes the palette and whose
``overrides`` fully re-style the button (a pill) and checkbox (a switch).
Buttons switch live between the custom ``pastel``, ``light``, and standard
``dark`` themes via ``viz.set_theme(...)``, the checkbox toggles the sphere's
wireframe, and ``viz.export_snapshot(..., theme="pastel")`` packs the override
into a self-contained HTML export.

Run with:  uv run python py/examples/viz/scenes/custom_theme_override.py

Keywords: scenes, theme, custom theme, override, theme switching, button, checkbox, wireframe, light
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

viz = Visualizer(reuse_existing=False, title="Tanga — Custom Theme Override")

viz.add(
    Sphere(Point(0, 0, 0), radius=2), entity_id="sphere", color="#e879a8", opacity=0.3
)
viz.add(Point(1, 1, 1), color="#ff4444")


async def _on_radius(value, _event):
    viz.update_entity("sphere", Sphere(Point(0, 0, 0), radius=float(value)))
    viz.flush()


async def _on_wireframe(value, _event):
    viz.update("sphere", wireframe=bool(value))
    viz.flush()


async def _apply_pastel(_value, _event):
    viz.set_theme("pastel")


async def _apply_light(_value, _event):
    viz.set_theme("light")


async def _apply_standard(_value, _event):
    viz.set_theme("dark")


layout = SceneView(
    "",
    overlay=[
        GroupView(
            "Themes",
            [
                SliderView(
                    "radius",
                    label="Radius",
                    min=0.1,
                    max=5.0,
                    value=2.0,
                    on_change=_on_radius,
                ),
                CheckboxView(
                    "wire", label="Wireframe", value=True, on_change=_on_wireframe
                ),
                ButtonView("btn_pastel", label="Apply Pastel", on_click=_apply_pastel),
                ButtonView("btn_light", label="Apply Light", on_click=_apply_light),
                ButtonView(
                    "btn_standard", label="Apply Standard", on_click=_apply_standard
                ),
            ],
            position=EAnchor.TOP_LEFT,
        ),
    ],
)

# Apply the custom theme up front and pack it into a standalone export.
viz.set_theme("pastel")
viz.show(layout=layout)
viz.export_snapshot("pastel_theme.html", theme="pastel", overwrite=True)
print(
    "Buttons switch between the pastel, light, and standard themes. "
    "Pastel theme exported to pastel_theme.html. Press Ctrl+C to exit."
)
viz.wait()
