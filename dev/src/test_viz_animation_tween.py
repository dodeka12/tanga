#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Keyframe tweening demo using `animate_to()` and `Timeline`.

Creates a point and a sphere, then runs a sequence of browser‑side animated
transitions:

1. Point moves from (0, 0, 2) to (3, 0, 2) over 2 s (ease‑in‑out)
2. After a 0.5 s pause, the sphere fades to near‑transparent over 1.5 s
3. Simultaneously (parallel), the point fades out and a second point moves in

The server starts, the animations are dispatched, and the script waits
long enough for all tweens to play out before shutting down.

Run with:

    uv run python dev/src/test_viz_animation_tween.py
"""

from __future__ import annotations

import time

from pytanga.basis import BasisN3
from pytanga.geometry import Geometry, Point, Sphere
from pytanga.viz import DefaultPointStyle, ObjVizProps, Visualizer

_P = ObjVizProps


def main() -> None:
    viz = Visualizer(opns=False)
    viz.start()  # non‑blocking server

    # Add a point to move around
    p_id = viz.add(
        Point(0, 0, 2),
        _P(color="#ff4444", style=DefaultPointStyle(size=0.15)),
        label="P",
    )

    # Add a sphere to fade
    b = BasisN3()
    geo = Geometry(b, opns=False)
    s_mv = geo.create(Sphere(Point(0, 2, 0), 1.5))
    s_id = viz.add(s_mv, _P(color="#4488ff", opacity="0.6"), label="S")

    time.sleep(1.0)  # let browser connect and render initial scene

    # ── Demo 1: single animate_to() call ──────────────────
    print("Moving point from (0,0,2) → (3,0,2) over 2 s …")
    viz.animate_to(p_id, position=(3, 0, 2), duration=2.0, easing="ease-in-out")
    time.sleep(2.5)

    # ── Demo 2: fade the sphere ───────────────────────────
    print("Fading sphere to near‑transparent …")
    viz.animate_to(s_id, opacity=0.08, duration=1.5, easing="ease-out")
    time.sleep(2.0)

    # ── Demo 3: Timeline with parallel steps ───────────────
    print("Running timeline: point fades out + second point moves in (parallel) …")
    p2_id = viz.add(
        Point(-3, -1, 2),
        _P(color="#44ff44", style=DefaultPointStyle(size=0.12), opacity=0.0),
        label="Q",
    )
    time.sleep(0.5)

    (
        viz.timeline()
        .animate_to(p_id, opacity=0.1, duration=1.5, easing="ease-in")
        .animate_to(
            p2_id, position=(0, -1, 2), opacity=1.0, duration=1.5, parallel=True
        )
        .play()
    )
    time.sleep(2.5)

    # ── Demo 4: bounce back ───────────────────────────────
    print("Bouncing everything back …")
    (
        viz.timeline()
        .animate_to(p_id, position=(0, 0, 2), opacity=1.0, duration=1.5)
        .wait(0.3)
        .animate_to(s_id, opacity=0.6, duration=1.0)
        .wait(0.3)
        .animate_to(p2_id, position=(-3, -1, 2), opacity=0.2, duration=1.0)
        .play()
    )
    time.sleep(5.0)

    viz.stop()
    print("Done.")


if __name__ == "__main__":
    main()
