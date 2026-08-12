# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""demo_camera_3d_plane.py — 3D plane-based camera via ViewPlaneConfig.

Defines a tilted virtual plane (point + normal) with explicit horizontal
extents and a custom ``span_u`` direction.  The camera is placed along
the plane normal at a distance computed from ``fov`` and the extents.

Run with:  uv run python py/examples/viz/demo_camera_3d_plane.py
"""

from pytanga.geometry import Point, Sphere
from pytanga.viz import CameraConfig, PointStyle, SphereStyle, ViewPlaneConfig, Visualizer

viz = Visualizer(
    title="Tanga — 3D Plane Camera (ViewPlaneConfig)",
    camera=CameraConfig(
        view_plane=ViewPlaneConfig(
            point=(0.0, 0.0, 0.0),
            normal=(0.4, 0.6, 1.0),
            extent_u=7.0,
            extent_v=5.0,
            span_u=(1.0, 0.0, -0.4),
            fov=50.0,
        )
    ),
)

viz.add(Point(2, 1, 3), color="#ff4444", style=PointStyle(size=0.15), label="$P_1$")
viz.add(Point(-1, 2, 1), color="#44ff44", style=PointStyle(size=0.15), label="$P_2$")
viz.add(
    Sphere(Point(0, 0, 0), radius=2.0),
    style=SphereStyle(wireframe=True),
    opacity=0.3,
)

viz.run()