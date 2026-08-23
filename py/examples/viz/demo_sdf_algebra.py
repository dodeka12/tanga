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

from pytanga.basis import BasisN3, BasisP3
from pytanga.basis.pga3 import BasisPGA3
from pytanga.geometry import create_entity
from pytanga.geometry.entities import Direction, Line, Plane, Point, Sphere
from pytanga.viz.sdf import SdfVisualizer

viz = SdfVisualizer(title="Tanga SDF — Algebra path (mixed algebras)")

# A PGA3 plane (OPNS): `op(point, plane)` is a grade-4 blade whose magnitude is
# proportional to the point–plane distance, so `scalar_pseudo` vanishes on the
# plane. `calibrate=True` computes the per-object gradient scale (|∇d| ≈ 1).
pga3 = BasisPGA3(opns=True)
plane = create_entity(pga3, Plane(point=Point(0, 0, 0), normal=Direction(0, 0, 1)))
viz.add(plane, color="#44ff44", calibrate=True, thickness=0.1)

# A P3 line (OPNS): `op(point, line)` is a trivector that vanishes on the line.
# `thickness=0.1` turns the zero-thickness line into a tube of radius 0.1, and
# `falloff=0.15` + `max_distance=0.5` give it a soft exponential opacity edge
# that hard-cuts to transparent at 0.5 (see the `sdf-viewer` docs).
p3 = BasisP3(opns=True)
line = create_entity(p3, Line(origin=Point(0, 0, 0), direction=Direction(1, 1, 1)))
viz.add(
    line,
    color="#ffaa00",
    calibrate=True,
    thickness=0.1,
    falloff=0.15,
    max_distance=0.5,
)

n3 = BasisN3()
sphere = create_entity(n3, Sphere(center=Point(1, 0, 0), radius=2.0))
viz.add(sphere, color="#4400ff", calibrate=True, thickness=0.0)

print("Algebra path: a green PGA3 plane, an orange P3 line (a soft tube), and a")
print("blue N3 sphere, all evaluated as mv_sdf objects (M·a → distOf). The default")
print("distance function is 'scalar_pseudo'; switch with viz.distance.")

viz.show()
viz.wait()
