# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""control_group_single.py — Declarative control groups on a single-scene page.

Same as ``control_group_overlay.py``, but shown on the plain single-scene URL
(``/``).  Two ``GroupView`` overlays declared on the base ``SceneView``:

- an **overlay-anchored** group (``position="top-right"``), and
- a group **anchored to a 3D object** (``parent_id=...``) that follows the sphere
  via the CSS2D attach path.

Run with:  uv run python py/examples/viz/ui/controls/control_group_single.py

Keywords: control group, GroupView, overlay, anchor, parent_id, single scene
"""

from pytanga.geometry import Point, Sphere
from pytanga.viz import ButtonView, GroupView, SceneView, SliderView, Visualizer

viz = Visualizer(reuse_existing=False, title="Tanga — Control Groups (single scene)")
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


viz.set_layout(
    SceneView(
        "",
        overlay=[
            GroupView(
                "View",
                [
                    SliderView(
                        "radius",
                        label="Radius",
                        min=0.2,
                        max=5.0,
                        value=2.0,
                        on_change=_on_radius,
                    ),
                    ButtonView("reset", label="Reset", on_click=_on_reset),
                ],
                position="top-right",
            ),
            # BUG: The following group is not shown on the single-scene page. Why?
            GroupView(
                "Sphere",
                [
                    SliderView(
                        "opacity",
                        label="Opacity",
                        min=0.05,
                        max=1.0,
                        value=0.4,
                        on_change=_on_opacity,
                    ),
                ],
                parent_id="sphere",
            ),
        ],
    )
)

viz.show()
print(
    "Overlay and attached control groups shown on the single-scene page. Press Ctrl+C to exit."
)
viz.wait()
