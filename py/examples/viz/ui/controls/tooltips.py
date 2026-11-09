# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""tooltips.py — Tooltips on controls, groups, and menus, plus a global switch.

A horizontal ``SplitView`` puts a control panel on the left and a sphere in a
``SceneView`` pane on the right.  Every control in the panel is created with a
``tooltip=`` text, the panel group itself carries one, and an icon-only button
demonstrates the accessible hover fallback (its tooltip doubles as the
``aria-label`` when tooltips are switched off).  Two runtime actions complete
the picture:

- **Rewrite tooltip** changes the radius slider's tooltip to the current value
  with ``Visualizer.set_control_tooltip`` — no layout re-push, the new text is
  pushed as a single ``control_state`` message.
- **Show tooltips** switches every framework tooltip on/off page-wide through
  ``Visualizer.set_tooltips_enabled``; a newly connected browser starts with
  that same setting.

A ``MenuView`` overlaid on the scene shows that menus take a tooltip too.

Run with:  uv run python py/examples/viz/ui/controls/tooltips.py

Keywords: tooltip, tooltips, help, group, button, menu, checkbox, slider
"""

from typing import Any

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ButtonView,
    CheckboxView,
    ControlEvent,
    EAnchor,
    GroupView,
    MenuView,
    SceneView,
    SliderView,
    SplitView,
    Visualizer,
)

viz = Visualizer(reuse_existing=False, title="Tanga — Tooltips")

_radius = 2.0
viz.add(
    Sphere(Point(0, 0, 0), radius=_radius),
    entity_id="sphere",
    color="#4488ff",
    opacity=0.4,
)


async def _on_radius(value: Any, _event: ControlEvent) -> None:
    global _radius
    _radius = float(value)
    viz.update_entity("sphere", Sphere(Point(0, 0, 0), radius=_radius))
    viz.flush()


async def _on_explain(_value: Any, _event: ControlEvent) -> None:
    print(f"[explain] sphere radius = {_radius:.2f}")


async def _on_show_tooltips(value: Any, _event: ControlEvent) -> None:
    # Page-wide switch: hides/shows every framework tooltip on all browsers.
    viz.set_tooltips_enabled(bool(value))


async def _on_retitle(_value: Any, _event: ControlEvent) -> None:
    # Runtime update of one control's tooltip — no layout re-push.
    viz.set_control_tooltip("radius", f"Radius = {_radius:.2f}")


async def _on_menu_action(_value: Any, _event: ControlEvent) -> None:
    print("[menu] help topic chosen")


# Menu tooltips: shown on the hamburger trigger of a dropdown menu.
help_menu = MenuView(
    "Help",
    [
        ButtonView("help_intro", label="Introduction", on_click=_on_menu_action),
        ButtonView("help_keys", label="Keyboard shortcuts", on_click=_on_menu_action),
    ],
    tooltip="Help topics",
    position=EAnchor.TOP_RIGHT,
)

layout = SplitView(
    orientation="horizontal",
    children=[
        GroupView(
            "Controls",
            [
                SliderView(
                    "radius",
                    label="Radius",
                    min=0.2,
                    max=5.0,
                    value=_radius,
                    tooltip="Radius of the sphere in model units",
                    on_change=_on_radius,
                ),
                ButtonView(
                    "explain",
                    icon="material:help",
                    icon_only=True,
                    tooltip="Explain the current setup",
                    on_click=_on_explain,
                ),
                ButtonView(
                    "retitle",
                    label="Rewrite tooltip",
                    tooltip="Replace the slider tooltip with its current value",
                    on_click=_on_retitle,
                ),
                CheckboxView(
                    "show_tooltips",
                    label="Show tooltips",
                    value=True,
                    tooltip="Switch every framework tooltip on or off",
                    on_change=_on_show_tooltips,
                ),
            ],
            tooltip="Sphere controls — hover a control for its tooltip",
        ),
        SceneView("", overlay=[help_menu]),
    ],
)

viz.show(layout=layout)
print("Hover the controls for tooltips. Press Ctrl+C to exit.")
viz.wait()
