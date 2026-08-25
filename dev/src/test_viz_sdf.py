#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Minimal headless smoke-test for the SDF viewer (``pytanga.viz.sdf``).

Exercises the analytic path end-to-end without opening a browser:
    1. Construct ``SdfVisualizer``.
    2. Add analytic entities (a sphere).
    3. Exercise the boolean combine modes.
    4. Boot the WebSocket server, flush the scene, and stop it cleanly.

Run with:  uv run python dev/src/test_viz_sdf.py
"""

from __future__ import annotations

import time

from pytanga.geometry.entities import Point, Sphere
from pytanga.viz.sdf import SdfVisualizer
from pytanga.viz.sdf.serializer import serialize_entity


def test_analytic_entity() -> None:
    viz = SdfVisualizer(
        open_browser=False, add_default_light=False, add_default_grid=False, add_default_axes=False
    )
    oid = viz.add(Sphere(Point(0, 0, 0), 1.5), color="#ffaa00")
    assert isinstance(oid, str)
    print("  analytic sphere added:", oid)


def test_combine_and_smooth() -> None:
    carved = serialize_entity(
        Sphere(Point(0, 0, 0), 1.0), "s", {"combine": "subtract"}
    )
    assert carved["combine"] == "subtract"
    assert carved["polarity"] == "negative"

    smooth = serialize_entity(
        Sphere(Point(0, 0, 0), 1.0), "s2", {"combine": "smooth_union", "smoothness": 0.2}
    )
    assert smooth["combine"] == "smooth_union"
    assert smooth["smoothness"] == 0.2
    print("  combine/subtract/smooth round-trips")


def test_server_boot_and_flush() -> None:
    viz = SdfVisualizer(open_browser=False, port=18767, host="127.0.0.1")
    viz.add(Sphere(Point(0, 0, 0), 1.0), color="#ffaa00")

    viz.start_server()
    time.sleep(0.3)
    viz.flush()
    assert viz._server is not None
    viz.stop_server()
    print("  server boot + scene flush + clean shutdown")


if __name__ == "__main__":
    test_analytic_entity()
    test_combine_and_smooth()
    test_server_boot_and_flush()
    print("=" * 60)
    print("All SDF smoke tests PASSED.")
