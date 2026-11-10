# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""serve-anim-export-smoke.py — serve an exported animated HTML for the smoke.

Builds a representative scene with static entities (axes, grids, point paths,
points, labels) and changing entities (a moving point, a transform-only line, a
growing axis, two grids — one constant-count, one growing-count — and a growing
point path), records 100 frames and exports them with ``delivery="inline"``
into a temp dir, then serves that dir on a free port **without opening a
browser**.  Run this first, then:

    node js/dev/tests/anim-export-smoke.mjs <printed-url>

Run with:  uv run python js/dev/tests/serve-anim-export-smoke.py
"""

from __future__ import annotations

import math
import os
import tempfile
from collections import Counter
from functools import partial
from http import server

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

FRAMES = 100
FPS = 30


def _fill_path(path: PointPath, count: int) -> None:
    for i in range(count):
        path.add((i % 8, i // 8, 0.0))


def main() -> None:
    viz = Visualizer(
        title="Tanga — animated export smoke",
        add_default_axes=False,
        add_default_grid=False,
    )

    # ── Static entities (must never be touched after frame 0) ──
    viz.new(Axes2D((0, 0), range_u=(-5, 5), range_v=(-5, 5)))
    viz.new(
        Grid(dir_u=(1, 0, 0), dir_v=(0, 1, 0), range_u=(-5, 5), range_v=(-5, 5))
    )
    viz.new(Axis(start=(0, 0, 0), end=(5, 0, 0), major_interval=1.0, label="X"))
    viz.new(Axis(start=(0, 0, 0), end=(0, 5, 0), major_interval=1.0, label="Y"))

    path_a = PointPath(max_points=64)
    path_b = PointPath(max_points=64)
    _fill_path(path_a, 64)
    _fill_path(path_b, 64)
    viz.new(path_a, color="#445577", style=PointPathStyle(line_thickness=1))
    viz.new(path_b, color="#774455", style=PointPathStyle(line_thickness=1))

    viz.new(Point(0.5, 0.5, 0.0), color="#44ff44", label="a")
    viz.new(Point(-0.5, 0.5, 0.0), color="#44ff44", label="b")
    viz.new(Point(0.5, -0.5, 0.0), color="#44ff44")
    viz.new(Point(-0.5, -0.5, 0.0), color="#44ff44")

    # ── Changing entities (must update in place, never rebuild) ──
    mover = viz.new(Point(0.0, 0.0, 0.0), color="#ff4444", label="mover")
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
    grow_path = PointPath(max_points=128)
    grow_path.add((0.0, 0.0, 0.5))
    grow_path.add((0.5, 0.0, 0.5))
    viz.new(grow_path, color="#cc8844", style=PointPathStyle(line_thickness=1))

    viz.flush()

    # ── Record ────────────────────────────────────────────────
    recording = viz.start_animation_recording()

    for t in range(FRAMES):
        mover.entity = Point(t * 0.05, math.sin(t * 0.3), 0.0)
        line.set_transform(position=(t * 0.02, 0.0, 0.0))
        grow_axis.entity = Axis(
            start=(0, 0, -1),
            end=(5 + t * 0.02, 0, -1),
            ticks=[(1.0, "1"), (2.0, "2"), (3.0, "3"), (4.0, "4")],
            label="T",
        )
        slide_grid.entity = Grid(
            dir_u=(1, 0, 0),
            dir_v=(0, 1, 0),
            range_u=(-5 + t * 0.01, 5 + t * 0.01),
            range_v=(-5, 5),
        )
        grow_grid.entity = Grid(
            dir_u=(1, 0, 0),
            dir_v=(0, 1, 0),
            range_u=(-5, -5 + t * 0.05),
            range_v=(-5, 5),
        )
        grow_path.add((5 + t * 0.03, math.sin(t * 0.3), 0.5))

        viz.flush()
        recording.capture_frame()

    # ── Export (inline) ───────────────────────────────────────
    out_dir = tempfile.mkdtemp(prefix="tanga-anim-smoke-")
    out_path = os.path.join(out_dir, "smoke.html")
    viz.export_snapshot(
        out_path,
        overwrite=True,
        animation=recording,
        anim_style=AnimStyle(fps=FPS, loop=False, compress=True),
        delivery="inline",
    )

    kinds = Counter(e["kind"] for e in recording.to_diff_dict()["initial"])
    print(f"exported: {out_path} ({os.path.getsize(out_path)} bytes)")
    print(f"initial entities by kind: {dict(sorted(kinds.items()))}")

    handler = partial(server.SimpleHTTPRequestHandler, directory=out_dir)
    httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    url = f"http://127.0.0.1:{httpd.server_address[1]}/smoke.html"
    print(f"ANIM_SMOKE_URL={url}", flush=True)
    print("serving — Ctrl+C to stop", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
