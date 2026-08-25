# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""arrowhead.py — isolate the SDF arrowhead (capped cone) placement.

Draws two bare arrowheads built directly from the primitive library:

  * a red arrowhead at the origin whose apex should point along **+Z**, and
  * a blue arrowhead translated along **+X** that should still point along **+Z**.

No shaft, no disc, no ring — just the conical tip — so the direction the apex
actually points in is unambiguous. This is a diagnostic for the rotor/general
rotor axis-arrow placement bug.

The cone primitive (``sdCappedCone``) is a truncated cone along **+Y**: its
apex is the ``radius2`` end at local ``+Y``, its base the ``radius1`` end at
local ``-Y``. To aim the apex along +Z we rotate +Y onto +Z, i.e. a rotation
of ``+90°`` about the **+X** axis (the same axis/angle ``_rotation_align(_Y,
+Z)`` produces in the serializer).

Run with:  uv run python py/examples/viz/sdf/arrowhead.py
"""

import math

from pytanga.viz.sdf import SdfVisualizer, capped_cone

viz = SdfVisualizer(title="Tanga SDF — arrowhead placement debug")

# +Y -> +Z: rotate +90 degrees about +X.
# (cross((0,1,0),(0,0,1)) = (1,0,0); acos(dot) = pi/2.)
aim_z = ((1.0, 0.0, 0.0), math.pi / 2.0)

# Base radius at the fat end, apex radius 0 at the tip (local +Y).
half_height = 0.3
base_radius = 0.2

# Arrowhead 1: at the origin, apex should point along +Z.
viz.add(
    capped_cone(
        half_height,
        base_radius,
        0.0,
        position=(0.0, 0.0, 0.0),
        rotation=aim_z,
    ),
    color="#ff4444",
)

# Arrowhead 2: translated along +X, still pointing along +Z.
viz.add(
    capped_cone(
        half_height,
        base_radius,
        0.0,
        position=(3.0, 0.0, 0.0),
        rotation=aim_z,
    ),
    color="#44aaff",
)

print("Two arrowheads should be visible, both with their apex pointing along +Z")
print("(red at the origin, blue at x = +3). In the default view +Z points toward")
print("the camera, so both tips should reach up/back toward the viewer.")

viz.show()
viz.wait()
