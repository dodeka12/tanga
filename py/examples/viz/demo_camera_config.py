# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""demo_camera_config.py — Auto-fit, explicit, and partial camera modes.

Run with:  uv run python py/examples/viz/demo_camera_config.py
"""

from pytanga.geometry import Direction, Plane, Point, Sphere
from pytanga.viz import (
    CameraConfig3d,
    PointStyle,
    SphereStyle,
    View2DConfig,
    View3dConfig,
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
viz1.show()
viz1.wait()

# ── Scene 2: Full explicit camera ──────────────────────────
print("\nScene 2: Explicit camera (top-down, narrow FOV)")
viz2 = Visualizer(
    title="Tanga — Explicit Camera",
    camera=CameraConfig3d(position=(0, 15, 0), target=(0, 0, 0), fov=30),
)
viz2.add(Point(2, 0, 0), color="#ff4444", style=PointStyle(size=0.15), label="$P_1$")
viz2.add(Point(0, 2, 0), color="#44ff44", style=PointStyle(size=0.15), label="$P_2$")
viz2.add(Point(0, 0, 2), color="#4444ff", style=PointStyle(size=0.15), label="$P_3$")
viz2.add(Sphere(Point(0, 0, 0), radius=2.5), style=SphereStyle(wireframe=True), opacity=0.3)
viz2.show()
viz2.wait()

# ── Scene 3: Partial camera — position only ────────────────
print("\nScene 3: Partial camera — position set, target & FOV auto-computed")
viz3 = Visualizer(
    title="Tanga — Partial Camera",
    camera=CameraConfig3d(position=(10, 3, 0)),
)
viz3.add(Point(2, 0, 0), color="#ff4444", style=PointStyle(size=0.15), label="$P_1$")
viz3.add(Point(0, 2, 0), color="#44ff44", style=PointStyle(size=0.15), label="$P_2$")
viz3.add(Sphere(Point(0, 0, 0), radius=2.5), style=SphereStyle(wireframe=True), opacity=0.3)
viz3.show()
viz3.wait()

# ── Scene 4: 2D orthographic view via View2DConfig ─────────
print("\nScene 4: View2DConfig — rectangle centred at (1, 2), letterboxed")
viz4 = Visualizer(
    title="Tanga — View2DConfig (letterboxed)",
    camera=View2DConfig(xmin=-1.0, xmax=3.0, ymin=0.5, ymax=3.5),
)
viz4.add(Point(2, 0, 0), color="#ff4444", style=PointStyle(size=0.15), label="$P_1$")
viz4.add(Point(0, 2, 0), color="#44ff44", style=PointStyle(size=0.15), label="$P_2$")
viz4.show()
viz4.wait()

# ── Scene 5: 2D stretch-to-fill via View2DConfig (uniform=False) ──
print("\nScene 5: View2DConfig — long, thin plot stretched to fill")
viz5 = Visualizer(
    title="Tanga — View2DConfig (stretch-to-fill)",
    camera=View2DConfig(
        xmin=0.0,
        xmax=100.0,
        ymin=0.0,
        ymax=2.0,
        border_world=2.0,
        border_px=30.0,
        uniform=False,
    ),
)
viz5.add(Point(10, 1, 0), color="#ff4444", style=PointStyle(size=0.15), label="$P_1$")
viz5.add(Point(50, 0.5, 0), color="#44ff44", style=PointStyle(size=0.15), label="$P_2$")
viz5.add(Point(90, 1.5, 0), color="#4444ff", style=PointStyle(size=0.15), label="$P_3$")
viz5.show()
viz5.wait()

# ── Scene 6: 3D plane-based camera via View3dConfig ─────
print("\nScene 6: View3dConfig — tilted virtual plane")
viz6 = Visualizer(
    title="Tanga — View3dConfig",
    camera=View3dConfig(
        point=(0.0, 0.0, 0.0),
        normal=(0.5, 0.4, 1.0),
        extent_u=6.0,
        extent_v=5.0,
        fov=45.0,
    ),
)
viz6.add(Point(2, 0, 0), color="#ff4444", style=PointStyle(size=0.15), label="$P_1$")
viz6.add(Point(0, 2, 0), color="#44ff44", style=PointStyle(size=0.15), label="$P_2$")
viz6.add(Sphere(Point(0, 0, 0), radius=2.5), style=SphereStyle(wireframe=True), opacity=0.3)
viz6.show()
viz6.wait()

print("\nAll scenes complete.")
