# Map a dict/dataclass to a two-column table of controls

**Keywords:** params view · controls · dict · dataclass · param_ui · theme · set_theme

A horizontal `SplitView` puts four `ParamsView` instances on the left and a
sphere in the `SceneView` on the right.  Each `ParamsView` renders every key
as a title on the left and a matching control on the right, and fires one
`on_change` with the full state.  Four ways to describe the UI are shown: a
plain `dict` with a `styles` dict of `ControlUI` specs, a plain `dict`
with no `styles` (controls inferred from the value types), a `@dataclass`
using the `param_ui()` helper, and a `@dataclass` using raw
`dataclasses.field(metadata={"param_ui": …})`.  A theme `DropdownView` at the
top switches the active theme live across every built-in theme, and a shared
`PARAMS_MIN_WIDTH` sets a fixed minimum width on every `ParamsView`
(overriding the theme's `--tanga-params-min-width` default).

## Run

```bash
uv run python py/examples/viz/ui/controls/params_view.py
```

## Source

[`viz/ui/controls/params_view.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/ui/controls/params_view.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""params_view.py — Map a dict/dataclass to a two-column table of controls.

A horizontal ``SplitView`` puts four ``ParamsView`` instances on the left and a
sphere in the ``SceneView`` on the right.  Each ``ParamsView`` renders every key
as a title on the left and a matching control on the right, and fires one
``on_change`` with the full state.  Four ways to describe the UI are shown: a
plain ``dict`` with a ``styles`` dict of ``ControlUI`` specs, a plain ``dict``
with no ``styles`` (controls inferred from the value types), a ``@dataclass``
using the ``param_ui()`` helper, and a ``@dataclass`` using raw
``dataclasses.field(metadata={"param_ui": …})``.  A theme ``DropdownView`` at the
top switches the active theme live across every built-in theme, and a shared
``PARAMS_MIN_WIDTH`` sets a fixed minimum width on every ``ParamsView``
(overriding the theme's ``--tanga-params-min-width`` default).

Run with:  uv run python py/examples/viz/ui/controls/params_view.py

Keywords: params view, controls, dict, dataclass, param_ui, theme, set_theme
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    CheckboxUI,
    ColorPickerUI,
    ControlEvent,
    DropdownUI,
    DropdownView,
    GroupView,
    ParamsView,
    SceneView,
    Size,
    SliderUI,
    SplitView,
    StackView,
    Visualizer,
    list_themes,
    param_ui,
)

viz = Visualizer(reuse_existing=False, title="Tanga — ParamsView")

viz.add(
    Sphere(Point(0, 0, 0), radius=2), entity_id="sphere", color="#4488ff", opacity=0.3
)
viz.add(Point(1, 1, 1), color="#ff4444")


def _as_dict(state: Any) -> dict[str, Any]:
    if isinstance(state, dict):
        return state
    return {f.name: getattr(state, f.name) for f in dataclasses.fields(state)}


async def _on_change(state: Any, _event: ControlEvent) -> None:
    d = _as_dict(state)
    if "radius" in d:
        viz.update_entity("sphere", Sphere(Point(0, 0, 0), radius=float(d["radius"])))
    if "wireframe" in d:
        viz.update("sphere", wireframe=bool(d["wireframe"]))
    if "color" in d:
        viz.update("sphere", color=str(d["color"]))
    if "mode" in d:
        viz.update("sphere", opacity={"solid": 0.3, "wire": 0.15}.get(str(d["mode"]), 0.3))
    viz.flush()


async def _on_theme(value: Any, _event: ControlEvent) -> None:
    viz.set_theme(str(value))


#: Fixed minimum width applied to every ParamsView below.  Remove the
#: ``min_width=`` arguments to fall back to the theme's ``--tanga-params-min-width``.
PARAMS_MIN_WIDTH = Size.px(280)


# ── 1. dict mode — `styles` is a dict of `ControlUI` specs ───────────────────
dict_view = ParamsView(
    {"radius": 2.0, "wireframe": False},
    styles={
        "radius": SliderUI(title="Radius", min=0.1, max=5.0, step=0.05),
        "wireframe": CheckboxUI(title="Wireframe"),
    },
    min_width=PARAMS_MIN_WIDTH,
    on_change=_on_change,
)


# ── 2. dataclass mode via the param_ui() helper ──────────────────────────────
@dataclass
class SphereParams:
    radius: float = param_ui(
        2.0, ui=SliderUI(title="Radius", min=0.1, max=5.0, step=0.05)
    )
    wireframe: bool = param_ui(False, ui=CheckboxUI(title="Wireframe"))
    color: str = param_ui("#4488ff", ui=ColorPickerUI(title="Color"))
    mode: str = param_ui("solid", ui=DropdownUI(title="Mode", options=["solid", "wire"]))


# ── 3. dataclass mode via raw field(metadata=…) (no helper) ──────────────────
@dataclass
class RawParams:
    radius: float = field(
        default=2.0,
        metadata={"param_ui": SliderUI(title="Radius", min=0.1, max=5.0, step=0.05)},
    )


layout = SplitView(
    orientation="horizontal",
    sizes=[Size.percent(35), Size.percent(65)],
    children=[
        StackView(
            "vertical",
            [
                GroupView(
                    "Theme",
                    [
                        DropdownView(
                            "theme",
                            label="Theme",
                            options=list_themes(),
                            value=viz.theme,
                            on_change=_on_theme,
                        ),
                    ],
                ),
                GroupView("Dict mode", [dict_view]),
                GroupView(
                    "Dict mode (inferred)",
                    [
                        ParamsView(
                            {
                                "count": 3,
                                "ratio": 0.5,
                                "name": "sphere",
                                "color": "#4488ff",
                                "wireframe": False,
                            },
                            min_width=PARAMS_MIN_WIDTH,
                            on_change=_on_change,
                        ),
                    ],
                ),
                GroupView("Dataclass (param_ui)", [ParamsView(SphereParams(), min_width=PARAMS_MIN_WIDTH, on_change=_on_change)]),
                GroupView("Dataclass (field metadata)", [ParamsView(RawParams(), min_width=PARAMS_MIN_WIDTH, on_change=_on_change)]),
            ],
        ),
        SceneView(""),
    ],
)

viz.show(layout=layout)
print("Each ParamsView maps a value to a control. Press Ctrl+C to exit.")
viz.wait()
````
