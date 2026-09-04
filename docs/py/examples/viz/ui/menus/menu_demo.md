# Menus: global hamburger, per-pane overlay, sub-menu, and a bar

**Keywords:** menu · dropdown · sub-menu · bar · overlay · layout

Demonstrates the menu system end-to-end:

- a **global** hamburger menu added with `add_menu()` (no scene name), holding
  a button, checkbox, and slider (auto-styled as flat menu items) plus a nested
  sub-menu;
- a **per-pane** `MenuView` overlaid on one `SceneView` pane; and
- a permanent `mode="bar"` horizontal strip shown at the top of the layout.

## Run

```bash
uv run python py/examples/viz/ui/menus/menu_demo.py
```

## Source

[`viz/ui/menus/menu_demo.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/ui/menus/menu_demo.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""menu_demo.py — Menus: global hamburger, per-pane overlay, sub-menu, and a bar.

Demonstrates the menu system end-to-end:

- a **global** hamburger menu added with ``add_menu()`` (no scene name), holding
  a button, checkbox, and slider (auto-styled as flat menu items) plus a nested
  sub-menu;
- a **per-pane** ``MenuView`` overlaid on one ``SceneView`` pane; and
- a permanent ``mode="bar"`` horizontal strip shown at the top of the layout.

Run with:  uv run python py/examples/viz/ui/menus/menu_demo.py

Keywords: menu, dropdown, sub-menu, bar, overlay, layout
"""

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ButtonView,
    CheckboxView,
    EAnchor,
    EIconMaterial,
    MenuView,
    SceneView,
    Size,
    SliderView,
    SplitView,
    StackView,
    Visualizer,
)

viz = Visualizer(reuse_existing=False, title="Tanga — Menus")

viz.add(
    Sphere(Point(0, 0, 0), radius=2), entity_id="sphere", color="#4488ff", opacity=0.3
)
side = viz.scene("side")
side.add(Point(1, 1, 1), color="#ff4444")


async def _on_fit(_value, _event):
    viz.flush(fit_camera=True)


async def _on_radius(value, _event):
    viz.update_entity("sphere", Sphere(Point(0, 0, 0), radius=float(value)))
    viz.flush()


async def _on_wireframe(value, _event):
    print("Wireframe:", value)


# A global hamburger menu in the full-screen overlay, with a nested sub-menu.
viz.add_menu(
    label="Settings",
    trigger_icon=EIconMaterial.MENU,
    position=EAnchor.TOP_RIGHT,
    children=[
        ButtonView("m_fit", label="Fit camera", on_click=_on_fit),
        SliderView(
            "m_radius",
            label="Radius",
            min=0.1,
            max=5.0,
            value=2.0,
            on_change=_on_radius,
        ),
        CheckboxView(
            "m_wire",
            label="Wireframe",
            value=False,
            on_change=_on_wireframe,
        ),
        MenuView(
            "Sub",
            [
                ButtonView(
                    "m_sub",
                    label="Fit (sub)",
                    on_click=_on_fit,
                ),
            ],
        ),
    ],
)

# A permanent horizontal strip (bar) shown at the top of the layout.
bar = MenuView(
    mode="bar",
    children=[
        ButtonView("bar_fit", label="Fit", on_click=_on_fit),
        ButtonView("bar_reset", label="Reset view", on_click=_on_fit),
    ],
)

layout = StackView(
    "vertical",
    [
        bar,
        SplitView(
            orientation="horizontal",
            sizes=[Size.percent(50), Size.percent(50)],
            children=[
                # Per-pane menu overlaid on the main scene.
                SceneView(
                    "",
                    overlay=[
                        MenuView(
                            "View",
                            [
                                ButtonView(
                                    "v_zoom",
                                    label="Zoom",
                                    on_click=_on_fit,
                                ),
                            ],
                            position=EAnchor.TOP_LEFT,
                        ),
                    ],
                ),
                SceneView("side"),
            ],
        ),
    ],
)

viz.show(layout=layout)
print("Menus are shown at a single URL. Press Ctrl+C to exit.")
viz.wait()
````
