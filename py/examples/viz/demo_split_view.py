# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""demo_split_view.py — A single page showing multiple scenes in split panes.

Builds a nested ``SplitView`` layout and displays it under one URL
(``/?view=<name>``).  The layout is:

- a horizontal split with a ``GroupView`` control sidebar on the left and
  everything else on the right,
- a vertical split (70/30) between the main scene and a horizontal split of
  two more scenes.

The sidebar is a ``GroupView`` of control views (a slider + buttons), composed
directly in the layout — controls are just views.  The main scene also has a
small ``GroupView`` overlaid on its canvas.  The bottom split shows the main
scene a second time from a different initial camera, demonstrating the
per-pane ``camera=`` override (same scene, independent viewpoint).  A sidebar
button moves the top pane's camera at runtime via
``Visualizer.set_view_camera``.

Run with:  uv run python py/examples/viz/demo_split_view.py
"""

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ButtonView,
    CameraConfig3d,
    GroupView,
    SceneView,
    Size,
    SliderView,
    SplitView,
    Visualizer,
)

viz = Visualizer(reuse_existing=False, title="Tanga — Split View")


async def _on_radius(value, _event):
    # Resize the main sphere.
    viz.update_entity("sphere", Sphere(Point(0, 0, 0), radius=float(value)))
    viz.flush()


async def _on_fit(_value, _event):
    # Auto-fit the camera to the scene contents.
    viz.flush(fit_camera=True)


async def _on_reset(_value, _event):
    # Re-apply a fixed default camera.
    viz.set_camera(CameraConfig3d(position=(0.0, 0.0, 8.0), target=(0.0, 0.0, 0.0)))


async def _on_topdown(_value, _event):
    # Move the top pane's camera at runtime (per-pane, not scene-wide).
    viz.set_view_camera(
        main_view, CameraConfig3d(position=(0.0, 8.0, 0.0), target=(0.0, 0.0, 0.0))
    )


# Main scene (the default scene, name "") — content in the top pane.
viz.add(
    Sphere(Point(0, 0, 0), radius=2), entity_id="sphere", color="#4488ff", opacity=0.3
)
viz.add(Point(1, 1, 1), color="#ff4444")

side = viz.scene("side")
side.add(Point(2, 0, 0), color="#44ff44")

# The top pane — kept as a variable so a button can target it at runtime.
main_view = SceneView(
    "",
    overlay=[
        GroupView(
            "Overlay",
            [ButtonView("btn_ov", label="Overlay action")],
            position="top-left",
        ),
    ],
)

layout = SplitView(
    orientation="horizontal",
    children=[
        GroupView(
            "Actions",
            [
                SliderView(
                    "radius",
                    label="Radius",
                    min=0.1,
                    max=5.0,
                    default=2.0,
                    on_change=_on_radius,
                ),
                ButtonView("btn_fit", label="Fit camera", on_click=_on_fit),
                ButtonView("btn_reset", label="Reset view", on_click=_on_reset),
                ButtonView("btn_topdown", label="Top-down", on_click=_on_topdown),
            ],
        ),
        SplitView(
            orientation="vertical",
            sizes=[Size.percent(50), Size.percent(50)],
            children=[
                main_view,
                SplitView(
                    orientation="horizontal",
                    children=[
                        SceneView("side"),
                        # The main scene again, from a different initial camera —
                        # each pane keeps its own orbit/zoom and viewpoint.
                        SceneView(
                            "",
                            camera=CameraConfig3d(
                                position=(8.0, 0.0, 0.0), target=(0.0, 0.0, 0.0)
                            ),
                        ),
                    ],
                ),
            ],
        ),
    ],
)

viz.show(layout=layout)
print("Split view is shown at a single URL. Press Ctrl+C to exit.")
viz.wait()
