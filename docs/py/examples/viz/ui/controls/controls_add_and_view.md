# One control, two ways: add_* and *View

**Keywords:** controls · add_slider · SliderView · facade · GroupView · scene

A single sphere is driven by the **same three controls built two ways**:

- the **panel facade** — bare `viz.add_slider` / `add_checkbox` /
  `add_button` calls, mounted in an implicit bottom-right overlay
  `GroupView`;
- the **declarative view classes** — `SliderView` / `CheckboxView` /
  `ButtonView` placed in an explicit `GroupView` overlay of a `SceneView`.

Both surfaces share one async handler per control and cross-update each other
via `set_control_value`, so dragging either slider (or toggling either
checkbox) moves the sphere and keeps its twin in sync.  This shows the two APIs
are interchangeable: identical parameters, values, and `(value, event)`
handler contract.

## Run

```bash
uv run python py/examples/viz/ui/controls/controls_add_and_view.py
```

## Source

[`viz/ui/controls/controls_add_and_view.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/ui/controls/controls_add_and_view.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""controls_add_and_view.py — One control, two ways: `add_*` and `*View`.

A single sphere is driven by the **same three controls built two ways**:

- the **panel facade** — bare ``viz.add_slider`` / ``add_checkbox`` /
  ``add_button`` calls, mounted in an implicit bottom-right overlay
  ``GroupView``;
- the **declarative view classes** — ``SliderView`` / ``CheckboxView`` /
  ``ButtonView`` placed in an explicit ``GroupView`` overlay of a ``SceneView``.

Both surfaces share one async handler per control and cross-update each other
via ``set_control_value``, so dragging either slider (or toggling either
checkbox) moves the sphere and keeps its twin in sync.  This shows the two APIs
are interchangeable: identical parameters, values, and ``(value, event)``
handler contract.

Run with:  uv run python py/examples/viz/ui/controls/controls_add_and_view.py

Keywords: controls, add_slider, SliderView, facade, GroupView, scene
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

viz = Visualizer(reuse_existing=False, title="Tanga — add_* vs *View")
viz.add(
    Sphere(Point(0, 0, 0), radius=2), entity_id="sphere", color="#4488ff", opacity=0.4
)


async def _on_radius(value, _event):
    """Shared by `add_slider` and `SliderView`; keeps both sliders in sync."""
    radius = float(value)
    viz.update_entity("sphere", Sphere(Point(0, 0, 0), radius=radius))
    viz.flush()
    viz.set_control_value("radius_add", radius)
    viz.set_control_value("radius_view", radius)


async def _on_wireframe(value, _event):
    """Shared by `add_checkbox` and `CheckboxView`; keeps both checkboxes in sync."""
    wire = bool(value)
    viz.update("sphere", wireframe=wire)
    viz.flush()
    viz.set_control_value("wire_add", wire)
    viz.set_control_value("wire_view", wire)


async def _on_reset(_value, _event):
    """Shared by `add_button` and `ButtonView`; resets the sphere and all controls."""
    viz.update_entity("sphere", Sphere(Point(0, 0, 0), radius=2))
    viz.update("sphere", wireframe=False)
    viz.flush()
    viz.set_control_value("radius_add", 2.0)
    viz.set_control_value("radius_view", 2.0)
    viz.set_control_value("wire_add", False)
    viz.set_control_value("wire_view", False)


# ── Panel facade: bare `add_*` → implicit bottom-right overlay GroupView ──
viz.add_slider(
    "radius_add",
    label="Radius (add_slider)",
    min=0.2,
    max=5.0,
    value=2.0,
    on_change=_on_radius,
)
viz.add_checkbox(
    "wire_add",
    label="Wireframe (add_checkbox)",
    value=False,
    on_change=_on_wireframe,
)
viz.add_button("reset_add", label="Reset (add_button)", on_click=_on_reset)

# ── Declarative: the same three controls as `*View` classes ──────────────
layout = SceneView(
    "",
    overlay=[
        GroupView(
            "Declarative",
            [
                SliderView(
                    "radius_view",
                    label="Radius (SliderView)",
                    min=0.2,
                    max=5.0,
                    value=2.0,
                    on_change=_on_radius,
                ),
                CheckboxView(
                    "wire_view",
                    label="Wireframe (CheckboxView)",
                    value=False,
                    on_change=_on_wireframe,
                ),
                ButtonView(
                    "reset_view",
                    label="Reset (ButtonView)",
                    on_click=_on_reset,
                ),
            ],
            icon=EIconMaterial.SETTINGS,
            position=EAnchor.TOP_LEFT,
        ),
    ],
)

viz.show(layout=layout)
print(
    "Same controls via add_* (bottom-right) and *View (top-left). "
    "Press Ctrl+C to exit."
)
viz.wait()
````
