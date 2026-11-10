# Export animated HTML and verify it uses in-place frame updates

**Keywords:** export · HTML · animated · in-place update · frame skip · PointPath · Grid

Builds a scene that mixes static entities (axes, a grid, point paths, points
and labels) with entities that change every frame (a moving point, a
transform-only line, a growing axis, two grids and a growing point path), then
records and exports it with `delivery="inline"`.  After exporting, it reads
the generated HTML back and reports whether the incremental-rendering features
are actually bundled:

* `_reconcileFrame` skips unchanged entities by source-object identity;
* `frame-pump.js` serializes frame application;
* `updatePointPath` / `updateAxis` / `updateAxes2D` / `updateAxes3D` /
  `updateGrid` rewrite geometry in place instead of rebuilding the mesh.

The feature check is a plain substring scan of the exported file, so it needs
no browser and no JS toolchain.  For the full behavioural check (frame churn
counters: `created`/`updated`/`removed` per frame), run:

    node js/dev/tests/anim-export-smoke.mjs <printed-url>

## Run

```bash
uv run python js/dev/tests/serve-anim-export-smoke.py
```

## Source

[`viz/export/animated_inplace_update_check.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/export/animated_inplace_update_check.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""animated_inplace_update_check.py — Export animated HTML and verify it uses in-place frame updates.

Builds a scene that mixes static entities (axes, a grid, point paths, points
and labels) with entities that change every frame (a moving point, a
transform-only line, a growing axis, two grids and a growing point path), then
records and exports it with ``delivery="inline"``.  After exporting, it reads
the generated HTML back and reports whether the incremental-rendering features
are actually bundled:

* ``_reconcileFrame`` skips unchanged entities by source-object identity;
* ``frame-pump.js`` serializes frame application;
* ``updatePointPath`` / ``updateAxis`` / ``updateAxes2D`` / ``updateAxes3D`` /
  ``updateGrid`` rewrite geometry in place instead of rebuilding the mesh.

The feature check is a plain substring scan of the exported file, so it needs
no browser and no JS toolchain.  For the full behavioural check (frame churn
counters: ``created``/``updated``/``removed`` per frame), run:

    uv run python js/dev/tests/serve-anim-export-smoke.py
    node js/dev/tests/anim-export-smoke.mjs <printed-url>

Run with:  uv run python py/examples/viz/export/animated_inplace_update_check.py

Keywords: export, HTML, animated, in-place update, frame skip, PointPath, Grid
"""

from __future__ import annotations

import math
import os

from pytanga.geometry import Direction, Line, Point
from pytanga.viz import (
    AnimStyle,
    Axis,
    Axes2D,
    Grid,
    PointPath,
    PointPathStyle,
    Visualizer,
)

FRAMES = 120
FPS = 30
OUT_PATH = "_output/animated_inplace_update_check.html"

# Feature marker -> human description.  The exported inline HTML embeds both the
# stripped library (renderer + frame-pump modules) and the playback bootstrap
# (`_reconcileFrame` / `_requestFrame`), so a substring match proves the feature
# made it into the file.
_FEATURES = {
    "mesh.userData._src === ent": "skip unchanged entities by identity",
    "createFramePump(_playFrame)": "serialized frame application (frame pump)",
    "function _requestFrame(": "fire-and-forget frame requests",
    "function updatePointPath(": "PointPath updates in place",
    "function updateAxis(": "Axis updates in place",
    "function updateAxes2D(": "Axes2D updates in place",
    "function updateAxes3D(": "Axes3D updates in place",
    "function updateGrid(": "Grid updates in place",
    "function applyOpacityUpdate(": "opacity-only style pass",
    "function clearGroupChildren(": "in-place group refill helper",
}

def main() -> None:
    viz = Visualizer(
        title="Tanga — In-place update check",
        add_default_axes=False,
        add_default_grid=False,
    )

    # ── Static entities (must never be rebuilt after frame 0) ──
    viz.new(Axes2D((0, 0), range_u=(-5, 5), range_v=(-5, 5)))
    viz.new(
        Grid(dir_u=(1, 0, 0), dir_v=(0, 1, 0), range_u=(-5, 5), range_v=(-5, 5))
    )
    viz.new(Axis(start=(0, 0, 0), end=(5, 0, 0), major_interval=1.0, label="X"))

    orbit = PointPath(max_points=64)
    for i in range(64):
        angle = 2.0 * math.pi * i / 64
        orbit.add((3.0 * math.cos(angle), 3.0 * math.sin(angle), 0.0))
    viz.new(orbit, color="#445577", style=PointPathStyle(line_thickness=1))

    viz.new(Point(0.5, 0.5, 0.0), color="#44ff44", label="a")
    viz.new(Point(-0.5, -0.5, 0.0), color="#44ff44")

    # ── Changing entities (must update in place, never rebuild) ──
    mover = viz.new(Point(3.0, 0.0, 0.0), color="#ff4444", label="mover")
    line = viz.new(
        Line(origin=Point(0, 0, -2), direction=Direction(0, 0, 1)),
        color="#4488ff",
    )
    grow_axis = viz.new(
        Axis(
            start=(0, 0, -1),
            end=(5, 0, -1),
            ticks=[(1.0, "1"), (2.0, "2"), (3.0, "3"), (4.0, "4")],
            label="T",
        )
    )
    slide_grid = viz.new(
        Grid(dir_u=(1, 0, 0), dir_v=(0, 1, 0), range_u=(-5, 5), range_v=(-5, 5))
    )
    grow_grid = viz.new(
        Grid(dir_u=(1, 0, 0), dir_v=(0, 1, 0), range_u=(-5, -5), range_v=(-5, 5))
    )
    trace = PointPath(max_points=128)
    trace.add((3.0, 0.0, 0.5))
    trace.add((3.0, 0.1, 0.5))
    viz.new(trace, color="#cc8844", style=PointPathStyle(line_thickness=1))

    viz.flush()

    # ── Record ────────────────────────────────────────────────
    recording = viz.start_animation_recording()

    for frame in range(FRAMES):
        angle = 2.0 * math.pi * frame / FRAMES
        mover.entity = Point(3.0 * math.cos(angle), 3.0 * math.sin(angle), 0.0)
        line.set_transform(position=(frame * 0.01, 0.0, 0.0))
        grow_axis.entity = Axis(
            start=(0, 0, -1),
            end=(5 + frame * 0.01, 0, -1),
            ticks=[(1.0, "1"), (2.0, "2"), (3.0, "3"), (4.0, "4")],
            label="T",
        )
        slide_grid.entity = Grid(
            dir_u=(1, 0, 0),
            dir_v=(0, 1, 0),
            range_u=(-5 + frame * 0.005, 5 + frame * 0.005),
            range_v=(-5, 5),
        )
        grow_grid.entity = Grid(
            dir_u=(1, 0, 0),
            dir_v=(0, 1, 0),
            range_u=(-5, -5 + frame * 0.04),
            range_v=(-5, 5),
        )
        trace.add((3.0 * math.cos(angle), 3.0 * math.sin(angle), 0.5))

        viz.flush()
        recording.capture_frame()

    # ── Export (inline) ───────────────────────────────────────
    os.makedirs("_output", exist_ok=True)
    viz.export_snapshot(
        OUT_PATH,
        overwrite=True,
        animation=recording,
        anim_style=AnimStyle(fps=FPS, loop=True, compress=True),
        delivery="inline",
    )

    # ── Verify the exported HTML carries the new features ─────
    with open(OUT_PATH, encoding="utf-8") as fh:
        html = fh.read()
    print(f"Exported: {OUT_PATH} ({os.path.getsize(OUT_PATH)} bytes)\n")
    print("Incremental-rendering feature check:")
    all_ok = True
    for marker, description in _FEATURES.items():
        present = marker in html
        all_ok = all_ok and present
        print(f"  [{'✓' if present else '✗'}] {description}")
    print()
    if all_ok:
        print("All incremental-rendering features are present in the export.")
    else:
        print("Some features are missing — the export does not use the new path.")
    print(
        "Open the file in a browser to watch it; for per-frame churn counters run\n"
        "the smoke: uv run python js/dev/tests/serve-anim-export-smoke.py"
    )


if __name__ == "__main__":
    main()
````
