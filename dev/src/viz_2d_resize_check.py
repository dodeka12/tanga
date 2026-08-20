#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Manual smoke-test for the default (no explicit camera) 2D viewer framing.

Opens a live 2D viewer with a few entities and **no** ``camera=`` config, then
auto-fits, for manually verifying the ResizeObserver-based camera framing fixes
(see ``dev/todos/viz-2d-camera-resize.md``):

1. Resize the browser window — the 2D view letterboxes (keeps its aspect
   ratio) and must not stretch/distort.
2. Stop the server (Ctrl+C) and resize again — still letterboxes, no
   distortion (previously this distorted until you clicked/reconnected).
3. Reload the page in a background tab / resize during load — the camera
   self-corrects without needing a click.

Run with:  uv run python dev/src/viz_2d_resize_check.py
"""

from pytanga.geometry import Circle, Direction, Line, Point
from pytanga.viz import Visualizer


def main() -> None:
    # Default 2D viewer — no `camera=` config, so the camera is the auto-fit
    # (default) 2D path under test (not an explicit View2DConfig).
    viz = Visualizer(
        space_dim=2,
        title="Tanga — 2D Resize Check (default camera)",
        annotation=(
            "## 2D resize check (default camera)\n\n"
            "1. Resize the window — the scene should **letterbox**, not distort.\n"
            "2. Stop the server, then resize — it should **still** letterbox.\n"
            "3. Reload in a background tab — the camera should self-correct.\n\n"
            "*Right-drag to pan · scroll to zoom.*"
        ),
    )

    # Entities spread off-centre so any aspect-ratio/distortion issue is
    # obvious: the circle must stay round, the line must stay straight.
    viz.add(Point(2, 1, 0), color="#ff4444", label="P1")
    viz.add(Point(-2, 3, 0), color="#44ff44", label="P2")
    viz.add(Point(0, -3, 0), color="#4444ff", label="P3")
    viz.add(
        Line(origin=Point(-3, -1, 0), direction=Direction(6, 2, 0)),
        color="#ffaa00",
        label="line",
    )
    viz.add(
        Circle(center=Point(1, 1, 0), normal=Direction(0, 0, 1), radius=1.5),
        color="#ff88ff",
        opacity=0.3,
        label="circle",
    )

    # Serve + open the browser (waits for the connection), then auto-fit the
    # default 2D camera to the entities (the default camera does not auto-fit
    # on its own).
    viz.show()
    viz.flush(fit_camera=True)

    print()
    print("2D resize check running.")
    print("  1. Resize the window and confirm the scene letterboxes (no stretch).")
    print("  2. Press Ctrl+C to stop the server, then resize again and confirm")
    print("     it still letterboxes without reconnecting.")
    print("  3. Reload in a background tab to check startup self-correction.")
    print()

    viz.wait()


if __name__ == "__main__":
    main()
