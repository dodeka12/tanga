# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""control_theming.py — Controls styled from the extracted theme CSS files.

Renders a ``GroupView`` (a slider, a checkbox, and a borderless icon-only
button) as a ``SceneView`` overlay over the default scene.  Control appearance
now comes from the theme CSS under ``pytanga/viz/templates/themes/`` —
``base.css`` design tokens plus one sheet per control — and the JS factories
only assign stable class names.  The borderless icon button and the
token-driven colors below therefore come straight from CSS, not inline styles.

Run with:  uv run python py/examples/viz/ui/controls/control_theming.py

Keywords: controls, theme, css, button, slider, checkbox, icon_only
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

viz = Visualizer(reuse_existing=False, title="Tanga — Control Theming")

viz.add(
    Sphere(Point(0, 0, 0), radius=2), entity_id="sphere", color="#4488ff", opacity=0.3
)
viz.add(Point(1, 1, 1), color="#ff4444")


async def _on_radius(value, _event):
    viz.update_entity("sphere", Sphere(Point(0, 0, 0), radius=float(value)))
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
                    min=0.1,
                    max=5.0,
                    value=2.0,
                    on_change=_on_radius,
                ),
                CheckboxView("wire", label="Wireframe", value=False),
                ButtonView(
                    "btn_settings",
                    label="Settings",
                    icon=EIconMaterial.SETTINGS,
                    icon_only=True,
                ),
            ],
            icon=EIconMaterial.PALETTE,
            position=EAnchor.TOP_LEFT,
        ),
    ],
)

viz.show(layout=layout)
print("Controls are styled from the theme CSS files. Press Ctrl+C to exit.")
viz.wait()
