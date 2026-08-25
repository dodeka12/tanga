# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""fit_2d.py — 2D fit-camera keeps the axes/grid undistorted.

Reproduces the scenario that used to expose a perspective-camera bug in the
default 2D viewer: one object far off to the left at ``(-20, 0)`` and another
at ``(5, 0)``, then ``flush(fit_camera=True)`` recenters the camera.

Because the 2D viewer uses an orthographic top-down camera, fitting the camera
only moves the view centre — the default grid (``z = -1``) and axes
(``z = -0.5``) stay perfectly aligned and at equal scale instead of appearing
smaller/misaligned as they would under a perspective projection.

Run with:  uv run python py/examples/viz/camera/fit_2d.py
"""

from pytanga.geometry import Point
from pytanga.viz import PointStyle, Visualizer

viz = Visualizer(
    space_dim=2,
    title="Tanga — 2D fit-camera (default camera)",
    annotation=(
        "## 2D fit-camera check\n\n"
        "Two points at **(-20, 0)** and **(5, 0)**, then `flush(fit_camera=True)`.\n\n"
        "The orthographic camera recenters to fit both points; the default axes and "
        "grid stay aligned and at equal scale (no perspective distortion).\n\n"
        "*Right-drag to pan · scroll to zoom.*"
    ),
)

viz.new(
    Point(-20, 0, 0), color="#ff4444", label="A (−20, 0)", style=PointStyle(size=0.4)
)
viz.new(Point(5, 0, 0), color="#4488ff", label="B (5, 0)", style=PointStyle(size=0.4))

viz.show()
viz.flush(fit_camera=True)

viz.wait()
