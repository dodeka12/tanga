# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""demo_camera_config.py — Auto-fit, explicit, and partial camera modes.

Run with:  uv run python py/examples/viz/demo_camera_config.py
"""

from pytanga.geometry import Direction, Plane, Point, Sphere
from pytanga.viz import CameraConfig, PointStyle, SphereStyle, Visualizer

# ── Scene 1: Auto-fit camera (default) ─────────────────────
print("Scene 1: Auto-fit camera (default)")
viz1 = Visualizer(title="Tanga — Auto-fit Camera")
viz1.add(Point(2, 0, 0), color="#ff4444", style=PointStyle(size=0.15))
viz1.add(Point(0, 2, 0), color="#44ff44", style=PointStyle(size=0.15))
viz1.add(Point(0, 0, 2), color="#4444ff", style=PointStyle(size=0.15))
viz1.add(Sphere(Point(0, 0, 0), radius=2.5), style=SphereStyle(wireframe=True), opacity=0.3)
viz1.add(Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)), opacity=0.25)
viz1.run()

# ── Scene 2: Full explicit camera ──────────────────────────
print("\nScene 2: Explicit camera (top-down, narrow FOV)")
viz2 = Visualizer(
    title="Tanga — Explicit Camera",
    camera=CameraConfig(position=(0, 15, 0), target=(0, 0, 0), fov=30),
    space_extent=20,
)
viz2.add(Point(2, 0, 0), color="#ff4444", style=PointStyle(size=0.15), label="$P_1$")
viz2.add(Point(0, 2, 0), color="#44ff44", style=PointStyle(size=0.15), label="$P_2$")
viz2.add(Point(0, 0, 2), color="#4444ff", style=PointStyle(size=0.15), label="$P_3$")
viz2.add(Sphere(Point(0, 0, 0), radius=2.5), style=SphereStyle(wireframe=True), opacity=0.3)
viz2.run()

# ── Scene 3: Partial camera — position only ────────────────
print("\nScene 3: Partial camera — position set, target & FOV auto-computed")
viz3 = Visualizer(
    title="Tanga — Partial Camera",
    camera=CameraConfig(position=(10, 3, 0)),
)
viz3.add(Point(2, 0, 0), color="#ff4444", style=PointStyle(size=0.15), label="$P_1$")
viz3.add(Point(0, 2, 0), color="#44ff44", style=PointStyle(size=0.15), label="$P_2$")
viz3.add(Sphere(Point(0, 0, 0), radius=2.5), style=SphereStyle(wireframe=True), opacity=0.3)
viz3.run()

print("\nAll scenes complete.")
