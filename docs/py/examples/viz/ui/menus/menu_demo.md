# Menus: per-pane overlay, sub-menus, and sub-sub-menus

**Keywords:** menu · dropdown · sub-menu · sub-sub-menu · bar · overlay · layout

Demonstrates the menu system declaratively:

- a **per-pane** `MenuView` overlaid on one `SceneView` pane, with a nested
  sub-menu, a sub-sub-menu, and a sub-sub-sub-menu (any depth is supported: a
  `MenuView` child of a `MenuView` is rendered as its sub-menu), and
- a permanent `mode="bar"` horizontal strip shown at the top of the layout,
  including its own nested sub-menu.

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

"""menu_demo.py — Menus: per-pane overlay, sub-menus, and sub-sub-menus.

Demonstrates the menu system declaratively:

- a **per-pane** ``MenuView`` overlaid on one ``SceneView`` pane, with a nested
  sub-menu, a sub-sub-menu, and a sub-sub-sub-menu (any depth is supported: a
  ``MenuView`` child of a ``MenuView`` is rendered as its sub-menu), and
- a permanent ``mode="bar"`` horizontal strip shown at the top of the layout,
  including its own nested sub-menu.

Run with:  uv run python py/examples/viz/ui/menus/menu_demo.py

Keywords: menu, dropdown, sub-menu, sub-sub-menu, bar, overlay, layout
"""

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ButtonView,
    CheckboxView,
    EAnchor,
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


def _menu_action(label):
    """Return an async handler that prints which menu item was chosen."""

    async def _handler(_value, _event):
        print(f"[menu] {label}")

    return _handler


# A permanent horizontal strip (bar) shown at the top of the layout, with a
# nested sub-menu (and a sub-sub-menu inside it).
bar = MenuView(
    mode="bar",
    children=[
        ButtonView("bar_fit", label="Fit", on_click=_on_fit),
        ButtonView("bar_reset", label="Reset view", on_click=_on_fit),
        MenuView(
            "Tools",
            [
                ButtonView("bar_tool", label="Tool A", on_click=_menu_action("Tool A")),
                MenuView(
                    "More tools",
                    [
                        ButtonView(
                            "bar_tool_deep",
                            label="Deep tool",
                            on_click=_menu_action("Deep tool"),
                        ),
                    ],
                ),
            ],
        ),
    ],
)

# A per-pane menu overlaid on the main scene, demonstrating three levels of
# nesting: View -> Sub -> Sub-sub -> Deepest.
view_menu = MenuView(
    "View",
    [
        ButtonView("v_zoom", label="Zoom", on_click=_on_fit),
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
                ButtonView("m_sub", label="Fit (sub)", on_click=_on_fit),
                MenuView(
                    "Sub-sub",
                    [
                        ButtonView(
                            "m_subsub",
                            label="Fit (sub-sub)",
                            on_click=_on_fit,
                        ),
                        MenuView(
                            "Deepest",
                            [
                                ButtonView(
                                    "m_deep",
                                    label="Deepest action",
                                    on_click=_menu_action("Deepest action"),
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        MenuView(
            "Other",
            [
                ButtonView(
                    "m_other", label="Other action", on_click=_menu_action("Other")
                ),
            ],
        ),
    ],
    position=EAnchor.TOP_LEFT,
)

layout = StackView(
    "vertical",
    [
        bar,
        SplitView(
            orientation="horizontal",
            sizes=[Size.percent(50), Size.percent(50)],
            children=[
                SceneView("", overlay=[view_menu]),
                SceneView("side"),
            ],
        ),
    ],
)

viz.show(layout=layout)
print("Menus are shown at a single URL. Press Ctrl+C to exit.")
viz.wait()
````
