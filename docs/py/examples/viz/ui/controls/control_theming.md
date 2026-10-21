# One of every control, themed live via a theme dropdown

**Keywords:** controls · theme · set_theme · list_themes · split view · slider · checkbox

A horizontal `SplitView` puts a control panel (`GroupView`) on the left and
the main scene (`SceneView`) on the right.  The panel holds one of each
control kind — slider, value-edit (stepper), text field, text area, dropdown,
color picker, checkbox, and button — plus a theme `DropdownView` that switches
the active theme at runtime.  Its options come from `list_themes()` (`dark`,
`light`, `pastel`, and the dense `compact` variant), and selecting one
calls `viz.set_theme` so every control restyles live without a reload.

## Run

```bash
uv run python py/examples/viz/ui/controls/control_theming.py
```

## Source

[`viz/ui/controls/control_theming.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/ui/controls/control_theming.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""control_theming.py — One of every control, themed live via a theme dropdown.

A horizontal ``SplitView`` puts a control panel (``GroupView``) on the left and
the main scene (``SceneView``) on the right.  The panel holds one of each
control kind — slider, value-edit (stepper), text field, text area, dropdown,
color picker, checkbox, and button — plus a theme ``DropdownView`` that switches
the active theme at runtime.  Its options come from ``list_themes()`` (``dark``,
``light``, ``pastel``, and the dense ``compact`` variant), and selecting one
calls ``viz.set_theme`` so every control restyles live without a reload.

Run with:  uv run python py/examples/viz/ui/controls/control_theming.py

Keywords: controls, theme, set_theme, list_themes, split view, slider, checkbox
"""

from typing import Any

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ButtonView,
    CheckboxView,
    ColorPickerView,
    ControlEvent,
    DropdownView,
    EIconMaterial,
    GroupView,
    SceneView,
    Size,
    SliderView,
    SplitView,
    TextAreaView,
    TextFieldView,
    ValueEditView,
    Visualizer,
    list_themes,
)

viz = Visualizer(reuse_existing=False, title="Tanga — Control Theming")

viz.add(
    Sphere(Point(0, 0, 0), radius=2), entity_id="sphere", color="#4488ff", opacity=0.3
)
viz.add(Point(1, 1, 1), color="#ff4444")


async def _on_radius(value: Any, _event: ControlEvent) -> None:
    viz.update_entity("sphere", Sphere(Point(0, 0, 0), radius=float(value)))
    viz.flush()


async def _on_opacity(value: Any, _event: ControlEvent) -> None:
    viz.update("sphere", opacity=float(value))
    viz.flush()


async def _on_color(value: Any, _event: ControlEvent) -> None:
    viz.update("sphere", color=str(value))
    viz.flush()


async def _on_wireframe(value: Any, _event: ControlEvent) -> None:
    viz.update("sphere", wireframe=bool(value))
    viz.flush()


async def _on_name(value: Any, _event: ControlEvent) -> None:
    viz.set_annotation(f"Name: {value}")


async def _on_notes(value: Any, _event: ControlEvent) -> None:
    viz.set_annotation(f"Notes: {value}")


async def _on_theme(value: Any, _event: ControlEvent) -> None:
    viz.set_theme(str(value))


async def _on_reset(_value: Any, _event: ControlEvent) -> None:
    viz.update_entity("sphere", Sphere(Point(0, 0, 0), radius=2.0))
    viz.update("sphere", color="#4488ff", opacity=0.3, wireframe=False)
    viz.flush()


layout = SplitView(
    orientation="horizontal",
    sizes=[Size.percent(30), Size.percent(70)],
    children=[
        GroupView(
            "Controls",
            [
                DropdownView(
                    "theme",
                    label="Theme",
                    options=list_themes(),
                    value=viz.theme,
                    on_change=_on_theme,
                ),
                SliderView(
                    "radius",
                    label="Radius",
                    min=0.1,
                    max=5.0,
                    value=2.0,
                    on_change=_on_radius,
                ),
                ValueEditView(
                    "opacity",
                    label="Opacity",
                    min=0.0,
                    max=1.0,
                    step=0.05,
                    digits=2,
                    value=0.3,
                    on_change=_on_opacity,
                ),
                ColorPickerView(
                    "color",
                    label="Color",
                    value="#4488ff",
                    on_change=_on_color,
                ),
                CheckboxView(
                    "wireframe", label="Wireframe", value=False, on_change=_on_wireframe
                ),
                TextFieldView(
                    "name",
                    label="Name",
                    value="sphere",
                    placeholder="Type a name…",
                    on_change=_on_name,
                ),
                TextAreaView(
                    "notes",
                    label="Notes",
                    value="",
                    placeholder="Multi-line notes…",
                    rows=2,
                    on_change=_on_notes,
                ),
                ButtonView(
                    "reset",
                    label="Reset",
                    icon=EIconMaterial.REFRESH,
                    on_click=_on_reset,
                ),
            ],
            icon=EIconMaterial.PALETTE,
        ),
        SceneView(""),
    ],
)

viz.show(layout=layout)
print(
    "One of each control, themed live via the Theme dropdown. Press Ctrl+C to exit."
)
viz.wait()
````
