# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""group.py — SDF object groups with per-member CSG + independent animation.

Builds an :class:`SdfGroup` (two spheres with a cylinder cut out) rendered as
ONE ray-marched solid in the standard viewer. One member is animated
independently while cross-object CSG, smooth shading, and self-shadowing are
preserved across the whole group, and the proxy bounding box resizes to wrap the
members as they move.

Run with:  uv run python py/examples/viz/sdf/group.py

Keywords: SDF, group, CSG, animation
"""

import math

from pytanga.geometry import Cylinder, Direction, Point, Sphere
from pytanga.viz import SdfStyle, Visualizer
from pytanga.viz.sdf import ECompose, SdfCompose, SdfGroup, capped_cylinder, sphere

viz = Visualizer(title="Tanga — SDF groups")
viz.show()

# ── A group: two spheres + a drilled cylinder, rendered as one solid ──
# (per-object CSG: member 2 subtracts the cylinder from both spheres.)
group = SdfGroup(
    sphere(1.0, position=(-1.0, 0.0, 0.0), id="left"),  # member 0 (union)
    sphere(1.0, position=(1.0, 0.0, 0.0), id="orbit"),  # member 1 (union)
    SdfCompose(capped_cylinder(1.5, 0.35), ECompose.SUBTRACT),  # member 2 (cut-out)
)
sdf_grp = viz.new(group, style=SdfStyle(color="#ffaa00"), label="SDF group")

# A normal (mesh) partially-transparent cylinder in the same place as the SDF
# cut-out, so the drilled hole is visible. The SDF member subtracts a cylinder
# of half-height 1.5 (length 3.0) and radius 0.35 along +Y, centered at the
# origin — mirror that exactly.
viz.add(
    Cylinder(
        origin=Point(0.0, 0.0, 0.0),
        axis=Direction(0.0, 1.0, 0.0),
        length=3.0,
        radius=0.35,
        align_center=0.5,
    ),
    color="#22cc88",
    opacity=0.5,
    label="mesh cut-out cylinder",
)

# A mesh sphere for reference (the unchanged vertex/mesh pipeline).
viz.add(Sphere(Point(-3.0, 0.0, 0.0), 1.0), color="#4477cc", label="mesh sphere")

viz.flush()

print("An SDF group (two spheres minus a cylinder) renders as one solid.")
print("Member 1 orbits; the proxy box resizes and cross-object CSG is preserved.")

angle = 0.0
for _ in viz.animate(fps=60):
    angle += 0.03
    x = 1.0 + 0.8 * math.cos(angle)
    y = 0.8 * math.sin(angle)
    # Animate a member independently by id (or by index) — frame-by-frame.
    sdf_grp.set_member_transform("orbit", position=(x, y, 0.0))
    viz.flush()

print("Animation stopped.")
viz.stop_server()
