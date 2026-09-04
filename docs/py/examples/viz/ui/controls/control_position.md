# Anchor bare add_* controls per scene

**Keywords:** controls · add_slider · control_position · scene · anchor · overlay

Bare `add_slider` / `add_checkbox` / `add_button` controls collect in an
implicit per-scene `GroupView`.  This example shows how to anchor that group:

- the **global default** — `Visualizer(control_position=...)` (bottom-right
  here), used by the base scene and any scene without its own override;
- a **per-scene override** — `viz.scene(name).control_position = ...`, which
  pins just that scene's implicit group;
- a **runtime move** — assigning `viz.control_position` (or the handle's)
  re-anchors the affected groups in place.

Each scene is served at its own URL: the base scene at `/`, the others at
`/detail` and `/extra`.

## Run

```bash
uv run python py/examples/viz/ui/controls/control_position.py
```

## Source

[`viz/ui/controls/control_position.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/ui/controls/control_position.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""control_position.py — Anchor bare add_* controls per scene.

Bare ``add_slider`` / ``add_checkbox`` / ``add_button`` controls collect in an
implicit per-scene ``GroupView``.  This example shows how to anchor that group:

- the **global default** — ``Visualizer(control_position=...)`` (bottom-right
  here), used by the base scene and any scene without its own override;
- a **per-scene override** — ``viz.scene(name).control_position = ...``, which
  pins just that scene's implicit group;
- a **runtime move** — assigning ``viz.control_position`` (or the handle's)
  re-anchors the affected groups in place.

Each scene is served at its own URL: the base scene at ``/``, the others at
``/detail`` and ``/extra``.

Run with:  uv run python py/examples/viz/ui/controls/control_position.py

Keywords: controls, add_slider, control_position, scene, anchor, overlay
"""

from pytanga.geometry import Point, Sphere
from pytanga.viz import EAnchor, Visualizer

# Global default: every scene without an override anchors here.
viz = Visualizer(
    reuse_existing=False,
    title="Tanga — Control Position",
    control_position=EAnchor.BOTTOM_RIGHT,
)

# ── Base scene (``/``) — follows the global default (bottom-right) ──
viz.add(
    Sphere(Point(0, 0, 0), radius=2), entity_id="sphere", color="#4488ff", opacity=0.4
)


async def _on_radius(value, _event):
    viz.update_entity("sphere", Sphere(Point(0, 0, 0), radius=float(value)))
    viz.flush()


viz.add_slider(
    "radius", label="Radius", min=0.2, max=5.0, value=2.0, on_change=_on_radius
)

# ── Named scene (``/detail``) — overrides the anchor to top-left ──
detail = viz.scene("detail")
detail.control_position = EAnchor.TOP_LEFT
detail.add(
    Sphere(Point(0, 0, 0), radius=1.5), entity_id="sphere", color="#ff8844", opacity=0.4
)


async def _on_zoom(value, _event):
    detail.update_entity("sphere", Sphere(Point(0, 0, 0), radius=float(value)))
    detail.flush()


detail.add_slider("zoom", label="Zoom", min=0.2, max=4.0, value=1.5, on_change=_on_zoom)

# ── Named scene (``/extra``) — overrides the anchor to the right edge ──
extra = viz.scene("extra")
extra.control_position = EAnchor.RIGHT
extra.add(
    Sphere(Point(0, 0, 0), radius=1.0), entity_id="sphere", color="#44ff88", opacity=0.4
)


async def _on_reset(_value, _event):
    extra.update_entity("sphere", Sphere(Point(0, 0, 0), radius=1.0))
    extra.flush()


extra.add_checkbox("wire", label="Wireframe", value=False)
extra.add_button("reset", label="Reset", on_click=_on_reset)

viz.show()
print(
    "Controls anchor per scene: base=bottom-right, detail=top-left, extra=right. "
    "Press Ctrl+C to exit."
)
viz.wait()
````
