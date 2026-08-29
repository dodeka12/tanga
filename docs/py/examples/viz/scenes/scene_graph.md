# Demonstrate VizGroup + direct transforms

**Keywords:** scenes · VizGroup · transforms · scene graph

Builds a compound "spinner" (a group of points and lines), then animates it as
a unit via transform-only aspect patches while an independent element moves on
its own.  Transform-only changes re-serialize only the `transform` aspect —
no child geometry is recomputed or re-sent.

## Run

```bash
uv run python py/examples/viz/scenes/scene_graph.py
```

## Source

[`viz/scenes/scene_graph.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/scenes/scene_graph.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""scene_graph.py — Demonstrate ``VizGroup`` + direct transforms.

Builds a compound "spinner" (a group of points and lines), then animates it as
a unit via transform-only aspect patches while an independent element moves on
its own.  Transform-only changes re-serialize only the ``transform`` aspect —
no child geometry is recomputed or re-sent.

Run with:  uv run python py/examples/viz/scenes/scene_graph.py

Keywords: scenes, VizGroup, transforms, scene graph
"""

import math

from pytanga.geometry import Direction, Line, Point
from pytanga.geometry.operators import Translator
from pytanga.viz import PointStyle, Visualizer

viz = Visualizer(title="Tanga — Scene Graph")
viz.show()

# ── Compound object: a "spinner" group ──────────────────────
spinner = viz.add_group("spinner")
spinner.new(Point(0, 0, 0), color="#ff4444", label="hub")
spinner.new(
    Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0)),
    color="#44aaff",
)
spinner.new(
    Line(origin=Point(0, 0, 0), direction=Direction(0, 1, 0)),
    color="#44ff44",
)
spinner.new(Point(1.5, 0, 0), color="#ffaa00", label="tip", style=PointStyle(size=0.10))

# ── Independent element for contrast ────────────────────────
roamer = viz.new(Point(0, 0, 3), color="#ffffff", label="roamer")
viz.flush()

print("Animating the scene graph until Ctrl+C...")
frame = 0
for _ in viz.animate(fps=50):
    angle = frame * 0.03

    # Group-only transform aspect — children are NOT re-serialized.
    spinner.set_transform(rotation=(0.0, 0.0, angle))

    # Independent element moves in place (absolute position).
    roamer.set_transform(
        position=(
            1.5 * math.sin(frame * 0.02),
            0.0,
            3 + 1.5 * math.cos(frame * 0.02),
        )
    )

    # Showcase the operator-based transform API once per revolution.
    if frame % 120 == 0:
        spinner.apply_transform(Translator(vector=Direction(0.0, 0.0, 0.1)))

    viz.flush()
    frame += 1

print("Animation stopped.")
````
