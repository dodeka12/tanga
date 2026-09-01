# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""control_group_overlay.py — Unified control groups: overlay-anchored + 3D-anchored.

Demonstrates the unified ``add_control_group`` API (both groups are now backed by
the single ``GroupView`` path):

- an **overlay-anchored** group (``position="top-right"``) mounted in the global
  overlay, and
- a group **anchored to a 3D object** (``parent_id=...``) that follows the sphere
  via the CSS2D attach path.

Run with:  uv run python py/examples/viz/scenes/control_group_overlay.py

Keywords: control group, add_control_group, overlay, anchor, parent_id, layout
"""

from pytanga.geometry import Point, Sphere
from pytanga.viz import SceneView, StackView, Visualizer

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


viz.add_slider("radius", label="Radius", min=0.2, max=5.0, value=2.0, on_change=_on_radius)
viz.add_slider("opacity", label="Opacity", min=0.05, max=1.0, value=0.4, on_change=_on_opacity)
viz.add_button("reset", label="Reset", on_click=_on_reset)

# Overlay-anchored group: mounted in the full-screen overlay.
viz.add_control_group(
    "overlay_group",
    title="View",
    controls=["radius", "reset"],
    position="top-right",
)

# 3D-anchored group: attaches to the sphere (CSS2D object).
viz.add_control_group(
    "attached_group",
    title="Sphere",
    controls=["opacity"],
    parent_id="sphere",
)

viz.show(layout=StackView("vertical", [SceneView("")]))
print("Overlay and attached control groups shown. Press Ctrl+C to exit.")
viz.wait()
