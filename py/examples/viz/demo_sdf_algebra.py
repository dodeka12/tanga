# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""demo_sdf_algebra.py — the SDF viewer's algebra (MV) rendering path.

Draws raw multivectors directly — without routing them through
``geometry.analyze()`` — as ``mv_sdf`` objects: each MV is reduced to its
product matrix ``M`` on the backend and evaluated per-pixel in the shader as
``distOf(M·a)``. Here a PGA3 plane and a P3 line coexist in one scene (mixed
algebras) under the default ``scalar_pseudo`` distance function.

Run with:  uv run python py/examples/viz/demo_sdf_algebra.py
"""

from pytanga.basis.p3 import BasisP3
from pytanga.basis.pga3 import BasisPGA3
from pytanga.geometry import create_entity
from pytanga.geometry.entities import Direction, Line, Plane, Point
from pytanga.viz.sdf import SdfVisualizer

viz = SdfVisualizer(title="Tanga SDF — Algebra path (mixed algebras)")

# A PGA3 plane (OPNS): `op(point, plane)` is a grade-4 blade whose magnitude is
# proportional to the point–plane distance, so `scalar_pseudo` vanishes on the
# plane. `calibrate=True` computes the per-object gradient scale (|∇d| ≈ 1).
pga3 = BasisPGA3(opns=True)
plane = create_entity(pga3, Plane(point=Point(0, 0, 0), normal=Direction(0, 0, 1)))
viz.add(plane, color="#44ff44", calibrate=True)

# A P3 line (OPNS): `op(point, line)` is a trivector that vanishes on the line.
p3 = BasisP3(opns=True)
line = create_entity(
    p3, Line(origin=Point(-2, 0, 0), direction=Direction(1, 0, 0))
)
viz.add(line, color="#ffaa00", calibrate=True)

print("Algebra path: a green PGA3 plane and an orange P3 line, both evaluated")
print("as mv_sdf objects (M·a → distOf). The default distance function is")
print("'scalar_pseudo'; switch with viz.distance = 'magnitude' | 'scalar'.")

viz.show()
viz.wait()
