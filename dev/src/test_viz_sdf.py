#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Minimal headless smoke-test for the SDF viewer (``pytanga.viz.sdf``).

Exercises the algebra + analytic paths end-to-end without opening a browser:
    1. Construct ``SdfVisualizer``.
    2. Add analytic entities (a sphere) and raw MVs (a PGA3 plane + a P3 line)
       through the algebra path, with calibration.
    3. Exercise the boolean combine modes and the distance/opacity setters.
    4. Boot the WebSocket server, flush the scene, and stop it cleanly.

Run with:  uv run python dev/src/test_viz_sdf.py
"""

from __future__ import annotations

import time

from pytanga.basis.p3 import BasisP3
from pytanga.basis.pga3 import BasisPGA3
from pytanga.geometry import create_entity
from pytanga.geometry.entities import Direction, Line, Plane, Point, Sphere
from pytanga.viz.sdf import SdfVisualizer
from pytanga.viz.sdf.serializer import serialize_entity, serialize_mv


def test_analytic_entity() -> None:
    viz = SdfVisualizer(
        open_browser=False, add_default_light=False, add_default_grid=False, add_default_axes=False
    )
    oid = viz.add(Sphere(Point(0, 0, 0), 1.5), color="#ffaa00")
    assert isinstance(oid, str)
    assert viz.distance == "scalar_pseudo"
    assert viz.opacity == "step"
    print("  analytic sphere added:", oid)


def test_algebra_path_and_calibration() -> None:
    pga3 = BasisPGA3(opns=True)
    plane = create_entity(pga3, Plane(point=Point(0, 0, 0), normal=Direction(0, 0, 1)))
    wire = serialize_mv(plane, "plane", {"calibrate": True, "color": "#44ff44"})
    assert wire["sdfKind"] == "mv_sdf"
    assert wire["algebra"] == "pga3"
    assert wire["scale"] != 1.0  # pga3 plane calibrates to 1/√2

    p3 = BasisP3(opns=True)
    line = create_entity(p3, Line(origin=Point(-2, 0, 0), direction=Direction(1, 0, 0)))
    line_wire = serialize_mv(line, "line", {"calibrate": True})
    assert line_wire["algebra"] == "p3"
    print("  algebra path serialized (pga3 plane scale=%s, p3 line)" % round(wire["scale"], 4))


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


def test_distance_and_opacity_setters() -> None:
    viz = SdfVisualizer(open_browser=False)
    viz.distance = "magnitude"
    assert viz.distance == "magnitude"
    viz.distance = "scalar_pseudo"
    assert viz.distance == "scalar_pseudo"
    viz.opacity = "sigmoid"
    assert viz.opacity == "sigmoid"
    viz.opacity = "step"
    assert viz.opacity == "step"
    print("  distance/opacity setters")


def test_server_boot_and_flush() -> None:
    viz = SdfVisualizer(open_browser=False, port=18767, host="127.0.0.1")
    viz.add(Sphere(Point(0, 0, 0), 1.0), color="#ffaa00")
    pga3 = BasisPGA3(opns=True)
    plane = create_entity(pga3, Plane(point=Point(0, 0, 0), normal=Direction(0, 0, 1)))
    viz.add(plane, color="#44ff44", calibrate=True)

    viz.start_server()
    time.sleep(0.3)
    viz.flush()
    assert viz._server is not None
    viz.stop_server()
    print("  server boot + scene flush + clean shutdown")


if __name__ == "__main__":
    test_analytic_entity()
    test_algebra_path_and_calibration()
    test_combine_and_smooth()
    test_distance_and_opacity_setters()
    test_server_boot_and_flush()
    print("=" * 60)
    print("All SDF smoke tests PASSED.")
