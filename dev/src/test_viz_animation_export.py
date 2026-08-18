#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Animated HTML export: two intersecting spheres with their IPNS intersection circle.

A fixed sphere S₁ sits at the origin (radius 1.0).  A second sphere S₂
(radius 1.3) oscillates along the x‑axis between −3 and +3.
The outer product S₁ ∧ S₂ (IPNS) gives the intersection circle, which is
also updated every frame.

The animation is recorded in Python and exported as two self-contained
HTML files — no server needed to play them back:

  - ``_output/anim_figure.html``  — embeddable snippet for presentations
  - ``_output/anim_standalone.html`` — full-page document

Run with:

    uv run python dev/src/test_viz_animation_export.py
"""

from __future__ import annotations

import math
import time

from pytanga.basis import BasisN3
from pytanga.geometry import Geometry, Point, Sphere
from pytanga.viz import AnimStyle, FigureStyle, Visualizer


def main() -> None:
    viz = Visualizer(title="Sphere intersection $S_1 \\wedge S_2$", opns=False)
    viz.set_annotation(
        "## Hello World\n\nRecording sphere intersection $S_1 \\wedge S_2$."
    )

    viz.show()  # non‑blocking — server runs in background thread

    # ── Geometry setup (IPNS) ──────────────────────────────
    b = BasisN3()
    geo = Geometry(b, opns=False)

    # Fixed sphere at origin
    s1_fixed = Sphere(Point(0.0, 0.0, 0.0), 1.0)
    s1_mv = geo.create(s1_fixed)
    s1_id = viz.add(s1_mv, color="#ff4444", opacity="0.3", label="$S_1$ (fixed)")

    # First placement of the moving sphere
    s2_current = Sphere(Point(3.0, 0.0, 0.0), 1.3)
    s2_mv = geo.create(s2_current)
    s2_id = viz.add(s2_mv, color="#4488ff", opacity="0.3", label="$S_2$ (moving)")

    # Initial intersection circle
    ci_mv = s1_mv ^ s2_mv
    ci_ana = geo.which_entity(ci_mv)
    print(f"Intersection analysis: {ci_ana}")
    ci_id = viz.add(ci_mv, color="#ffcc00", label="$S_1 ∧ S_2$")

    time.sleep(1.0)  # let the browser connect and receive initial scene

    # ── Animation recording ────────────────────────────────
    t_start = time.monotonic()
    duration = 5.0  # seconds

    recording = viz.start_animation_recording()

    while (time.monotonic() - t_start) < duration:
        elapsed = time.monotonic() - t_start
        # Oscillate x‑coordinate sinusoidally between −3 and +3
        x = 3.0 * math.sin(elapsed * 1.2)

        # Update moving sphere
        s2_new = Sphere(Point(x, 0.0, 0.0), 1.3)
        s2_mv = geo.create(s2_new)
        viz.update_entity(s2_id, s2_mv)

        # Re‑compute intersection
        ci_mv = s1_mv ^ s2_mv
        viz.update_entity(ci_id, ci_mv)

        # Push all dirty entities over WebSocket
        viz.flush()

        # Record the current entity state for the animated HTML export
        recording.capture_frame()

        time.sleep(1.0 / 60.0)

    print(f"Recorded {recording.frame_count} frames.")

    # ── Export ─────────────────────────────────────────────
    viz.export_figure(
        "_output/anim_figure.html",
        animation=recording,
        style=FigureStyle(auto_rotate=True, background="transparent"),
        anim_style=AnimStyle(fps=30, loop=True, compress=True),
        overwrite=True,
    )
    print("Exported: _output/anim_figure.html (embeddable snippet)")

    viz.export_snapshot(
        "_output/anim_standalone.html",
        animation=recording,
        anim_style=AnimStyle(fps=30, loop=True, compress=True),
        overwrite=True,
    )
    print("Exported: _output/anim_standalone.html (standalone full-page)")

    viz.stop_server()
    print("Done.")


if __name__ == "__main__":
    main()
