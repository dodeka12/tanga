#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Minimal smoke-test for the pytanga.viz submodule.

Exercises the core pipeline end-to-end:
    1. Create a Visualizer with default and custom config.
    2. Add geometry entities (Point, Line, Plane, Sphere, ...).
    3. Start the WebSocket server in a non-blocking background thread.
    4. Push the scene state.
    5. Stop the server cleanly.

The script does **not** open a browser or block, so it can be run as part
of an automated test suite without user interaction.

Run with:  uv run python dev/src/test_viz_smoke.py
"""

from __future__ import annotations

import time

from pytanga.viz import CameraConfig, Visualizer
from pytanga.geometry import (
    Circle,
    Direction,
    HPoint,
    Line,
    Plane,
    Point,
    PointPair,
    Space,
    Sphere,
)


def test_default_construction():
    """Basic construction and entity add + flush cycle."""
    print("─" * 60)
    print("Test 1: Default construction + entity lifecycle")
    viz = Visualizer(open_browser=False)

    # Add a few entities
    id_p = viz.add(Point(2, 0, 0), color="#ff4444"style=PointStyle(size=0.12), label="P₁")
    id_l = viz.add(
        Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0)),
        color="#44ff44",
        label="L",
    )
    id_pl = viz.add(
        Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)),
        opacity=0.3,
        label="π",
    )
    id_s = viz.add(
        Sphere(Point(0, 0, 0), radius=2.5),
        wireframe=True,
        opacity=0.4,
        label="S",
    )

    assert isinstance(id_p, str)
    assert isinstance(id_l, str)
    assert isinstance(id_pl, str)
    assert isinstance(id_s, str)
    print(f"  Added 4 entities: {id_p}, {id_l}, {id_pl}, {id_s}")

    # Start server in background thread
    viz.start()
    print("  Server started (background thread)")

    # Wait briefly for server to bind
    time.sleep(0.2)

    # Push scene state
    viz.flush()
    print("  Scene flushed")

    # Remove one entity
    viz.remove(id_s)
    viz.flush()
    print("  Removed sphere, flushed again")

    # Stop server
    viz.stop()
    print("  Server stopped")
    print("  PASSED\n")


def test_all_entity_types():
    """Add one of every supported entity type."""
    print("─" * 60)
    print("Test 2: All entity types")
    viz = Visualizer(open_browser=False)

    viz.add(Point(1, 0, 0), label="Point")
    viz.add(Direction(0, 1, 0), label="Direction")
    viz.add(HPoint(point=Point(0, 0, 0), weight=2.0), label="HPoint")
    viz.add(
        PointPair(point_a=Point(0, 0, 0), point_b=Point(1, 0, 0)),
        label="PtPair",
    )
    viz.add(
        Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0)),
        label="Line",
    )
    viz.add(
        Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)),
        opacity=0.3,
        label="Plane",
    )
    viz.add(
        Circle(center=Point(0, 0, 0), normal=Direction(0, 0, 1), radius=2),
        label="Circle",
    )
    viz.add(Sphere(Point(0, 0, 0), radius=2), style=SphereStyle(wireframe=True), label="Sphere")
    viz.add(Space(), label="Space")

    viz.start()
    time.sleep(0.1)
    viz.flush()
    viz.stop()
    print("  All 9 entity types added and flushed")
    print("  PASSED\n")


def test_all_operator_types():
    """Add one of every supported operator type."""
    print("─" * 60)
    print("Test 3: All operator types")

    from pytanga.geometry.operators import (
        Dilator,
        GeneralDilator,
        GeneralRotor,
        Inversion,
        Motor,
        Reflection,
        Rotor,
        Translator,
    )

    viz = Visualizer(open_browser=False)

    viz.add(Reflection(normal=Direction(0, 0, 1)), label="Refl")
    viz.add(Inversion(origin=Point(0, 0, 0)), label="Inv")
    viz.add(Rotor(angle=0.5, axis=Direction(0, 0, 1)), label="Rotor")
    viz.add(Translator(vector=Direction(1, 0, 0)), label="Transl")
    viz.add(Dilator(factor=2.0), label="Dil")
    viz.add(
        Motor(
            rotor=Rotor(angle=0.5, axis=Direction(0, 0, 1)),
            translator=Translator(vector=Direction(1, 0, 0)),
        ),
        label="Motor",
    )
    viz.add(
        GeneralRotor(
            rotor=Rotor(angle=0.5, axis=Direction(0, 0, 1)),
            translator=Translator(vector=Direction(1, 0, 0)),
        ),
        label="GenRot",
    )
    viz.add(
        GeneralDilator(factor=1.5, translator=Translator(vector=Direction(1, 0, 0))),
        label="GenDil",
    )

    viz.start()
    time.sleep(0.1)
    viz.flush()
    viz.stop()
    print("  All 8 operator types added and flushed")
    print("  PASSED\n")


def test_mv_input():
    """Test adding multivectors (MVs) directly via add()."""
    print("─" * 60)
    print("Test 4: MV input (PGA3)")

    from pytanga.algebra import Algebra

    pga = Algebra.from_name("PGA3")
    viz = Visualizer(open_browser=False)

    # Plane at z=3 (OPNS)
    viz.add(pga.plane(0, 0, 1, 3), opacity=0.3, label="Plane (MV)")

    # Point at (5, 0, 0) in OPNS and IPNS forms
    viz.add(pga.point(5, 0, 0), color="#ff4444", label="Pt OPNS", opns=True)
    viz.add(pga.point(5, 0, 0), color="#44ff44", label="Pt IPNS", opns=False)

    viz.start()
    time.sleep(0.1)
    viz.flush()
    viz.stop()
    print("  MV → Entity pipeline works for Plane and Point (OPNS + IPNS)")
    print("  PASSED\n")


def test_camera_config():
    """Test explicit and partial camera configurations."""
    print("─" * 60)
    print("Test 5: Camera configuration")

    # Full explicit
    viz1 = Visualizer(
        open_browser=False,
        camera=CameraConfig(
            position=(10, 6, 12),
            target=(0, 0, 0),
            fov=45,
            near=0.1,
            far=200,
        ),
    )
    viz1.add(Point(0, 0, 0))
    viz1.start()
    time.sleep(0.1)
    viz1.flush()
    viz1.stop()

    # Partial — position only
    viz2 = Visualizer(
        open_browser=False,
        camera=CameraConfig(position=(5, 10, 5)),
    )
    viz2.add(Point(0, 0, 0))
    viz2.start()
    time.sleep(0.1)
    viz2.flush()
    viz2.stop()

    print("  Full explicit and partial camera config work")
    print("  PASSED\n")


def test_default_rendering_properties():
    """Test set_default_color, set_default_extent, and defaults dict."""
    print("─" * 60)
    print("Test 6: Default rendering properties")

    viz = Visualizer(open_browser=False)

    # Change default colors
    viz.set_default_color("point", (0.0, 1.0, 0.0))
    viz.set_default_color("line", (0.0, 1.0, 1.0))
    viz.set_default_color("plane", "#ff00ff")

    # Change default extents
    viz.set_default_extent(line_length=30.0, plane_extent=15.0)

    # These use global defaults
    viz.add(Point(2, 0, 0), label="green pt")
    viz.add(Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0)), label="cyan line")
    viz.add(
        Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)),
        opacity=0.25,
        label="magenta plane",
    )

    # Per-entity override
    viz.add(Point(5, 0, 0), color="#ff0000", label="red pt (override)")

    viz.start()
    time.sleep(0.1)
    viz.flush()
    viz.stop()

    # Verify defaults dict
    d = viz.defaults
    assert d["color_point"] == "#00ff00"
    assert d["line_length"] == 30.0

    print(f"  color_point = {d['color_point']}, line_length = {d['line_length']}")
    print("  PASSED\n")


def test_scene_config_flags():
    """Test show_grid and show_axes flags."""
    print("─" * 60)
    print("Test 7: Scene config flags")

    viz = Visualizer(
        open_browser=False,
        show_grid=False,
        show_axes=False,
        space_extent=25,
    )
    assert viz._config.show_grid is False
    assert viz._config.show_axes is False
    assert viz._config.space_extent == 25

    viz.add(Point(0, 0, 0))
    viz.start()
    time.sleep(0.1)
    viz.flush()
    viz.stop()
    print("  show_grid=False, show_axes=False, space_extent=25")
    print("  PASSED\n")


def test_custom_port():
    """Test using a non-default port."""
    print("─" * 60)
    print("Test 8: Custom port")

    viz = Visualizer(open_browser=False, port=18766, host="127.0.0.1")
    assert viz._port == 18766
    assert "18766" in viz.url
    viz.add(Point(0, 0, 0))
    viz.start()
    time.sleep(0.1)
    viz.flush()
    viz.stop()
    print(f"  Server started on {viz.url}")
    print("  PASSED\n")


# ── Run all ────────────────────────────────────────────────

if __name__ == "__main__":
    test_default_construction()
    test_all_entity_types()
    test_all_operator_types()
    test_mv_input()
    test_camera_config()
    test_default_rendering_properties()
    test_scene_config_flags()
    test_custom_port()
    print("=" * 60)
    print("All smoke tests PASSED.")