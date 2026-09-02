# A tour of StackView/SplitView spacing, alignment, and flex

**Keywords:** layout · sizing · stack view · split view · gap · align · justify · flex · fr · Size

Builds one layout that exercises the declarative sizing options end to end:

- **`gap`** — spacing between a container's children, in pixels. `None` uses
  the default `4` px; `0` removes the spacing; a positive `int` sets it.
- **`align`** — cross-axis alignment of children: `"start"`, `"center"`,
  `"end"`, or `"stretch"` (default). A vertical stack aligns along the
  horizontal axis; a horizontal stack aligns along the vertical axis.
- **`justify`** — main-axis packing of children: `"start"` (default),
  `"center"`, `"end"`, `"space-between"`, `"space-around"`, or
  `"space-evenly"`.
- **Flex sizing** — a child's `preferred_width`/`preferred_height` along the
  container's main axis maps to CSS flex: `Size.fr(n)` grows to fill leftover
  space (weighted by `n`), `Size.px(v)`/`Size.percent(v)` set a fixed
  basis, and `None`/`Size.auto()` keep the natural size.
- **Control size floors** — control views default to `min_width=Size.px(120)`
  and `min_height=Size.px(32)`; pass `min_width=None`/`min_height=None` to
  disable them.
- **`SpacerView`** — an empty filler that grows along a flow container's main
  axis (`flex: 1 1 0`).
- **Fixed split panes** — a pane with `min == max` keeps its size, and a
  splitter now trades space between the *nearest non-fixed* panes on each side
  (so `[A, fixed_B, C]` keeps both splitters movable while `fixed_B` never
  changes).

## Run

```bash
uv run python py/examples/viz/scenes/layout_sizing.py
```

## Source

[`viz/scenes/layout_sizing.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/scenes/layout_sizing.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""layout_sizing.py — A tour of StackView/SplitView spacing, alignment, and flex.

Builds one layout that exercises the declarative sizing options end to end:

- **`gap`** — spacing between a container's children, in pixels. ``None`` uses
  the default ``4`` px; ``0`` removes the spacing; a positive ``int`` sets it.
- **`align`** — cross-axis alignment of children: ``"start"``, ``"center"``,
  ``"end"``, or ``"stretch"`` (default). A vertical stack aligns along the
  horizontal axis; a horizontal stack aligns along the vertical axis.
- **`justify`** — main-axis packing of children: ``"start"`` (default),
  ``"center"``, ``"end"``, ``"space-between"``, ``"space-around"``, or
  ``"space-evenly"``.
- **Flex sizing** — a child's ``preferred_width``/``preferred_height`` along the
  container's main axis maps to CSS flex: ``Size.fr(n)`` grows to fill leftover
  space (weighted by ``n``), ``Size.px(v)``/``Size.percent(v)`` set a fixed
  basis, and ``None``/``Size.auto()`` keep the natural size.
- **Control size floors** — control views default to ``min_width=Size.px(120)``
  and ``min_height=Size.px(32)``; pass ``min_width=None``/``min_height=None`` to
  disable them.
- **`SpacerView`** — an empty filler that grows along a flow container's main
  axis (``flex: 1 1 0``).
- **Fixed split panes** — a pane with ``min == max`` keeps its size, and a
  splitter now trades space between the *nearest non-fixed* panes on each side
  (so ``[A, fixed_B, C]`` keeps both splitters movable while ``fixed_B`` never
  changes).

Run with:  uv run python py/examples/viz/scenes/layout_sizing.py

Keywords: layout, sizing, stack view, split view, gap, align, justify, flex, fr, Size
"""

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ButtonView,
    CameraConfig3d,
    CheckboxView,
    DropdownView,
    GroupView,
    SceneView,
    Size,
    SliderView,
    SpacerView,
    SplitView,
    StackView,
    TextAreaView,
    Visualizer,
)

viz = Visualizer(reuse_existing=False, title="Tanga — Layout Sizing")

# -- Scene content -----------------------------------------------------------
# The default scene (name "") is shown in the top pane; two named scenes are
# shown side-by-side in the bottom split.
viz.add(
    Sphere(Point(0, 0, 0), radius=2), entity_id="sphere", color="#4488ff", opacity=0.3
)
viz.add(Point(1, 1, 1), color="#ff4444")

side = viz.scene("side")
side.add(Point(2, 0, 0), color="#44ff44")

detail = viz.scene("detail")
detail.add(Sphere(Point(-2, 1, 0), radius=1), color="#ffcc00", opacity=0.8)


# -- Control handlers --------------------------------------------------------
async def _on_radius(value, _event):
    viz.update_entity("sphere", Sphere(Point(0, 0, 0), radius=float(value)))
    viz.flush()


async def _on_enable(value, _event):
    viz.update("sphere", opacity=0.3 if bool(value) else 0.05)
    viz.flush()


async def _on_mode(value, _event):
    viz.set_annotation(f"Mode: {value}")


async def _on_fit(_value, _event):
    viz.flush(fit_camera=True)


async def _on_reset(_value, _event):
    viz.set_camera(CameraConfig3d(position=(0.0, 0.0, 8.0), target=(0.0, 0.0, 0.0)))


# -- Sidebar -----------------------------------------------------------------
# A horizontal toolbar row. `align="center"` centers the buttons on the cross
# axis (vertically) instead of stretching them to the row's height, and
# `justify="space-between"` pushes them to the opposite ends of the main axis.
# `gap=4` sets 4 px between them.
toolbar = StackView(
    "horizontal",
    [
        ButtonView("btn_fit", label="Fit", on_click=_on_fit),
        ButtonView("btn_reset", label="Reset", on_click=_on_reset),
    ],
    gap=4,
    align="center",
    justify="space-between",
)

# A `SpacerView` grows along the main axis, so it pushes the surrounding
# buttons apart — here it fills the leftover width between them (equivalent in
# effect to `justify="space-between"`, but explicit).
spacer_row = StackView(
    "horizontal",
    [
        ButtonView("btn_left", label="Left"),
        SpacerView(),
        ButtonView("btn_right", label="Right"),
    ],
    gap=4,
    align="center",
)

# A multi-line text area with `preferred_height=Size.fr(1)` — it grows to fill
# the leftover vertical space in the sidebar (weighted 1).
notes = TextAreaView(
    "notes",
    label="Notes",
    value="Type notes here…",
    preferred_height=Size.fr(1),
)

# A button whose control floor is disabled (`min_width=None`), so it can shrink
# below the default 120 px minimum when a flex parent needs it to.
compact_button = ButtonView(
    "btn_compact",
    label="No min floor",
    min_width=None,
)

# The sidebar is a titled vertical `GroupView` (a `StackView` with chrome).
# `gap=8` spaces its children by 8 px; `align="stretch"` (the default) lets
# every child fill the available width.
sidebar = GroupView(
    "Sizing playground",
    [
        SliderView(
            "radius",
            label="Radius",
            min=0.2,
            max=5.0,
            value=2.0,
            on_change=_on_radius,
        ),
        DropdownView(
            "mode",
            label="Mode",
            options=["Wire", "Solid"],
            value="Wire",
            on_change=_on_mode,
        ),
        CheckboxView(
            "cb_enable", label="Enable sphere opacity", value=True, on_change=_on_enable
        ),
        toolbar,
        spacer_row,
        notes,
        compact_button,
    ],
    gap=8,
    align="stretch",
    justify="start",
)


# -- Scene area: a vertical split with a fixed middle pane -------------------
# A pane is *fixed* along an axis when its min == max.  `min_height ==
# max_height == 85 px` pins this banner to its natural content height (title
# bar + button + panel padding), and the splitters above and below it stay
# draggable: dragging trades space between the nearest non-fixed panes on each
# side, so the banner never resizes.
fixed_banner = GroupView(
    "Fixed banner",
    [ButtonView("btn_banner", label="This pane is fixed")],
    min_height=Size.px(85),
    max_height=Size.px(85),
)

# The bottom split: two named scenes side-by-side, 50/50 by preferred size.
bottom_split = SplitView(
    orientation="horizontal",
    sizes=[Size.percent(50), Size.percent(50)],
    children=[SceneView("side"), SceneView("detail")],
)

# Vertical split: top scene, fixed middle banner, bottom horizontal split.
# (No `sizes` passed — the non-fixed panes share the leftover space equally.)
scene_area = SplitView(
    orientation="vertical",
    children=[
        SceneView(""),
        fixed_banner,
        bottom_split,
    ],
)

# -- Root layout: control sidebar beside the scene area ----------------------
layout = SplitView(
    orientation="horizontal",
    sizes=[Size.percent(30), Size.percent(70)],
    children=[sidebar, scene_area],
)

viz.show(layout=layout)
print(
    "Layout sizing playground is shown at a single URL. "
    "Drag the splitters and resize the window to explore the sizing options; "
    "press Ctrl+C to exit."
)
viz.wait()
````
