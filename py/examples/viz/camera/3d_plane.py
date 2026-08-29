# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""3d_plane.py — 3D projective camera via View3dConfig.

``View3dConfig`` defines the initial framing of a projective 3D camera using a
virtual plane: a plane ``point``/``normal``, the plane ``extent_u``/``extent_v``,
and an optional ``up`` vector.  The camera is placed along the plane normal at a
distance computed from ``fov`` and the extents, looking at the plane centre.
The ``up`` vector (default ``(0, 1, 0)``) is the orbit rotation axis in the
interactive viewer, independent of the plane orientation.

The resulting camera is a plain projective 3D camera with free orbit controls:
left-drag rotates, right/middle-drag pans, and the scroll wheel zooms.

The ``View3dConfig`` can be passed directly to ``Visualizer(camera=...)``.

Run with:  uv run python py/examples/viz/camera/3d_plane.py

Keywords: camera, 3D, View3dConfig, up vector
"""

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    Axes3D,
    Axes3DStyle,
    AxisStyle,
    LabelStyle,
    PointStyle,
    SphereStyle,
    View3dConfig,
    Visualizer,
)

viz = Visualizer(
    title="Tanga — 3D Plane Camera (View3dConfig)",
    camera=View3dConfig(
        point=(0.0, 0.0, 0.0),
        normal=(0.4, 0.6, 1.0),
        extent_u=7.0,
        extent_v=5.0,
        fov=50.0,
    ),
)

viz.new(
    Axes3D(),
    style=Axes3DStyle(
        u=AxisStyle(
            color="red",
            label_style=LabelStyle(
                align=(0.5, 1), offset_2d=(0, 0), offset_local=(0, 0, 0)
            ),
        ),
        v=AxisStyle(color="green"),
        w=AxisStyle(color="blue"),
    ),
)
viz.new(Point(2, 1, 3), color="#ff4444", style=PointStyle(size=0.15), label="$P_1$")
viz.new(Point(-1, 2, 1), color="#44ff44", style=PointStyle(size=0.15), label="$P_2$")
viz.new(
    Sphere(Point(0, 0, 0), radius=2.0),
    style=SphereStyle(wireframe=True),
    opacity=0.3,
)

viz.show()
viz.wait()
