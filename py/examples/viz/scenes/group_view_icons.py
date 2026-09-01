# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""group_view_icons.py — Group view chrome: leading icon, icon-only, borderless fold.

Shows how ``GroupView`` renders an optional leading icon next to its title, an
**icon-only** group (no title text), and the borderless fold/unfold button.  Two
groups are placed as a ``SceneView`` overlay over the default scene: one with a
``SETTINGS`` icon and a title, and one ``icon_only=True`` with a ``TUNE`` icon.
Both start expanded and can be collapsed via the borderless button in the header.

Run with:  uv run python py/examples/viz/scenes/group_view_icons.py

Keywords: scenes, group view, icon, icon_only, fold, overlay
"""

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ButtonView,
    EAnchor,
    EIconMaterial,
    GroupView,
    SceneView,
    SliderView,
    Visualizer,
)

viz = Visualizer(reuse_existing=False, title="Tanga — Group View Icons")

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
            "Settings",
            [
                SliderView(
                    "radius",
                    label="Radius",
                    min=0.1,
                    max=5.0,
                    value=2.0,
                    on_change=_on_radius,
                ),
            ],
            icon=EIconMaterial.SETTINGS,
            position=EAnchor.TOP_LEFT,
        ),
        GroupView(
            "",
            [ButtonView("btn_tune", label="Tune")],
            icon=EIconMaterial.TUNE,
            icon_only=True,
            position=EAnchor.TOP_RIGHT,
        ),
    ],
)

viz.show(layout=layout)
print("Group view icons are shown at a single URL. Press Ctrl+C to exit.")
viz.wait()
