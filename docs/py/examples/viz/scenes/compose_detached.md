# Compose a detached scene subtree, then insert it

**Keywords:** scene graph · compose · VizGroup · VizSceneObject · detached · cylinder

Builds a complete scene-graph subtree — a `VizGroup` of `VizSceneObject`
children (a cylinder hub, radial spokes, and tip points), each carrying its own
resolved style — **before** any `Visualizer` exists, then inserts the whole
thing in one step with `viz.new`.  Children use the default auto-generated
`id` and may carry partial styles; those are backfilled from the scene's
per-kind defaults on insert, exactly as if each child had been added via
`viz.add`.

## Run

```bash
uv run python py/examples/viz/scenes/compose_detached.py
```

## Source

[`viz/scenes/compose_detached.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/scenes/compose_detached.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""compose_detached.py — Compose a detached scene subtree, then insert it.

Builds a complete scene-graph subtree — a ``VizGroup`` of ``VizSceneObject``
children (a cylinder hub, radial spokes, and tip points), each carrying its own
resolved style — **before** any ``Visualizer`` exists, then inserts the whole
thing in one step with ``viz.new``.  Children use the default auto-generated
``id`` and may carry partial styles; those are backfilled from the scene's
per-kind defaults on insert, exactly as if each child had been added via
``viz.add``.

Run with:  uv run python py/examples/viz/scenes/compose_detached.py

Keywords: scene graph, compose, VizGroup, VizSceneObject, detached, cylinder
"""

import math

from pytanga.geometry import Cylinder, Direction, Line, Point
from pytanga.viz import (
    CylinderStyle,
    LineStyle,
    PointStyle,
    Visualizer,
    VizGroup,
    VizSceneObject,
)


def make_flywheel() -> VizGroup:
    """Build a detached "flywheel" subtree (no scene/visualizer needed)."""
    group = VizGroup(name="flywheel")

    # Central hub cylinder along +Z.
    group.add_child(
        VizSceneObject(
            None,
            Cylinder(
                origin=Point(0, 0, 0),
                axis=Direction(0, 0, 1),
                length=1.2,
                radius=0.35,
                align_center=0.5,
            ),
            CylinderStyle(color="#88aaff"),
            kind="Cylinder",
        )
    )

    # Four spokes in the XY plane, each with a tip point at its far end.
    for i in range(4):
        angle = i * math.pi / 2
        direction = Direction(math.cos(angle), math.sin(angle), 0)
        group.add_child(
            VizSceneObject(
                None,
                Line(origin=Point(0, 0, 0), direction=direction, length=1.5),
                LineStyle(color="#ff8855", thickness=3.0),
                kind="Line",
            )
        )
        group.add_child(
            VizSceneObject(
                None,
                Point(1.5 * math.cos(angle), 1.5 * math.sin(angle), 0),
                PointStyle(color="#44ff88", size=0.12),
                kind="Point",
            )
        )

    return group


viz = Visualizer(title="Tanga — Composing a detached subtree")
viz.show()

# Build the object completely detached, then insert it in one step.
flywheel = make_flywheel()
ref = viz.new(flywheel)
ref.translate(0.0, 0.0, 0.5)

viz.flush()

print("A flywheel (cylinder + spokes + tips) was built detached and inserted.")
print("Spinning the group until Ctrl+C...")
frame = 0
for _ in viz.animate(fps=50):
    ref.set_transform(rotation=(0.0, 0.0, frame * 0.03))
    viz.flush()
    frame += 1

print("Animation stopped.")
````
