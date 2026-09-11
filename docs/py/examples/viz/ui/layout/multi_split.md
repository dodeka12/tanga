# Three scenes side-by-side in one horizontal split

**Keywords:** split view · panes · layout · multi-pane

A single `SplitView` can hold any number of children in one direction: three
panes make two draggable splitters (N panes → N − 1 splitters).  This shows
three named scenes arranged in one horizontal row; the outer panes are slightly
larger than the middle one via per-child `sizes`.

## Run

```bash
uv run python py/examples/viz/ui/layout/multi_split.py
```

## Source

[`viz/ui/layout/multi_split.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/ui/layout/multi_split.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""multi_split.py — Three scenes side-by-side in one horizontal split.

A single ``SplitView`` can hold any number of children in one direction: three
panes make two draggable splitters (N panes → N − 1 splitters).  This shows
three named scenes arranged in one horizontal row; the outer panes are slightly
larger than the middle one via per-child ``sizes``.

Run with:  uv run python py/examples/viz/ui/layout/multi_split.py

Keywords: split view, panes, layout, multi-pane
"""

from pytanga.geometry import Point, Sphere
from pytanga.viz import SceneView, Size, SplitView, Visualizer

viz = Visualizer(reuse_existing=False, title="Tanga — Three-Way Split")

left = viz.scene("left")
left.add(Sphere(Point(-2, 0, 0), radius=1), color="#4488ff", opacity=0.3)

middle = viz.scene("middle")
middle.add(Sphere(Point(0, 0, 0), radius=1), color="#44ff44", opacity=0.3)

right = viz.scene("right")
right.add(Sphere(Point(2, 0, 0), radius=1), color="#ffcc00", opacity=0.3)

# One flat SplitView with three children — not nested 2-way splits.
layout = SplitView(
    orientation="horizontal",
    sizes=[Size.percent(35), Size.percent(30), Size.percent(35)],
    children=[SceneView("left"), SceneView("middle"), SceneView("right")],
)

viz.show(layout=layout)
print("Three panes share one URL with two draggable splitters. Press Ctrl+C to exit.")
viz.wait()
````
