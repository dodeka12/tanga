# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""demo_sdf_opacity.py — distance → opacity transfer functions.

Shows the opacity transfer axis: the same scene re-rendered with a soft
``sigmoid`` edge (switch to ``linear`` or ``step`` to compare). The per-object
``opacity`` is the falloff breadth ε for the non-``step`` transfers (and the
surface alpha for ``step``).

Run with:  uv run python py/examples/viz/demo_sdf_opacity.py
"""

from pytanga.geometry import Point, Sphere
from pytanga.viz.sdf import SdfVisualizer

viz = SdfVisualizer(title="Tanga SDF — Opacity transfer functions")

# A few overlapping translucent spheres.
viz.add(Sphere(Point(-1.5, 0, 0), 1.2), color="#ffaa00", opacity=0.6)
viz.add(Sphere(Point(0, 0.6, 0), 1.2), color="#44ff44", opacity=0.6)
viz.add(Sphere(Point(1.5, 0, 0), 1.2), color="#44aaff", opacity=0.6)

# Start with a soft sigmoid edge; the breadth is the per-object opacity (ε).
viz.opacity = "sigmoid"

print("Opacity transfers: three overlapping translucent spheres with a soft")
print("sigmoid edge. Compare with viz.opacity = 'linear' or 'step'.")

viz.show()
viz.wait()
