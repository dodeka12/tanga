# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""demo_camera_config.py — Auto-fit, explicit, and partial camera modes.

Run with:  uv run python py/examples/viz/demo_camera_config.py
"""

from pytanga.geometry import Direction, Plane, Point, Sphere
from pytanga.viz import (
    CameraConfig,
    PointStyle,
    SphereStyle,
    View2DConfig,
    ViewPlaneConfig,
    Visualizer,
)

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

# ── Scene 4: 2D orthographic view via View2DConfig ─────────
print("\nScene 4: View2DConfig — rectangle centred at (1, 2)")
viz4 = Visualizer(
    title="Tanga — View2DConfig",
    camera=CameraConfig(view_2d=View2DConfig(extent_x=4.0, extent_y=3.0, center=(1.0, 2.0))),
    space_dim=2,
)
viz4.add(Point(2, 0, 0), color="#ff4444", style=PointStyle(size=0.15), label="$P_1$")
viz4.add(Point(0, 2, 0), color="#44ff44", style=PointStyle(size=0.15), label="$P_2$")
viz4.run()

# ── Scene 5: 3D plane-based camera via ViewPlaneConfig ─────
print("\nScene 5: ViewPlaneConfig — tilted virtual plane")
viz5 = Visualizer(
    title="Tanga — ViewPlaneConfig",
    camera=CameraConfig(
        view_plane=ViewPlaneConfig(
            point=(0.0, 0.0, 0.0),
            normal=(0.5, 0.4, 1.0),
            extent_u=6.0,
            extent_v=5.0,
            fov=45.0,
        )
    ),
)
viz5.add(Point(2, 0, 0), color="#ff4444", style=PointStyle(size=0.15), label="$P_1$")
viz5.add(Point(0, 2, 0), color="#44ff44", style=PointStyle(size=0.15), label="$P_2$")
viz5.add(Sphere(Point(0, 0, 0), radius=2.5), style=SphereStyle(wireframe=True), opacity=0.3)
viz5.run()

print("\nAll scenes complete.")
