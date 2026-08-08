# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""demo_mv_visualization.py — MV input from PGA3 and N3, OPNS vs IPNS.

Run with:  uv run python py/examples/viz/demo_mv_visualization.py
"""

from pytanga.basis import BasisN3, BasisPGA3
from pytanga.geometry import Direction, Point, analyze
from pytanga.viz import Visualizer

pga = BasisPGA3()
n3 = BasisN3()
viz = Visualizer(title="Tanga — MV → Entity Pipeline")

# ── PGA3 ─────────────────────────────────────────────────
viz.add(pga.plane(0, 0, 1, 3), opacity=0.3, label="Plane (PGA3)")

# Point in OPNS form (grade-3 in PGA3)
viz.add(pga.point(5, 0, 0), color="#ff4444", size=0.15, opns=True, label="P (OPNS)")

# Same point in IPNS form (grade-1 vector)
viz.add(pga.point(5, 0, 0), color="#44ff44", size=0.10, opns=False, label="P (IPNS)")

viz.add(
    pga.line_from_direction(Direction(1, 0, 0), Point(0, 0, 0)),
    color="#44ff44",
    label="L (x-axis)",
)

# ── N3 ───────────────────────────────────────────────────
viz.add(n3.point(-3, 2, 0), color="#ff8844", size=0.12, label="N3 Pt")
viz.add(n3.point_pair(-3, 0, 0, 0, 2, 0), color="#8844ff", label="PtPair")
viz.add(
    n3.line_from_origin_direction(Direction(0, 1, 0)), color="#44ffff", label="N3 L"
)
viz.add(n3.circle(0, 0, 0, 0, 0, 1, 2), color="#ff44ff", label="Circle")
viz.add(n3.plane(0, 0, 1, 5), opacity=0.2, color="#ff88ff", label="N3 Plane")
viz.add(n3.sphere(-2, 0, 0, 1.5), wireframe=True, opacity=0.35, label="Sphere")

# ── Explicit analyze() — show what happens internally ─────
mv_sphere = n3.sphere(0, 3, 0, 1.0)
result = analyze(mv_sphere)
print(f"  MV analyzed to: {result}")
print(f"  Type: {type(result).__name__}")
print(f"  Center: {result.center}, Radius: {result.radius}")

viz.run()
