# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""demo_mv_visualization.py — MV input from PGA3 and N3, OPNS vs IPNS.

Run with:  uv run python py/examples/viz/demo_mv_visualization.py
"""

from pytanga.basis import BasisN3, BasisPGA3
from pytanga.geometry import (
    Circle,
    Direction,
    Geometry,
    Line,
    Plane,
    Point,
    PointPair,
    Sphere,
    analyze,
)
from pytanga.viz import PointStyle, SphereStyle, Visualizer

pga = BasisPGA3()
n3 = BasisN3()
geo_pga = Geometry(pga)
geo_n3 = Geometry(n3)
viz = Visualizer(title="Tanga — MV → Entity Pipeline")

# ── PGA3 ─────────────────────────────────────────────────
viz.add(
    # geo_pga(...) creates for Entity/Operator args; analyzes for MV args
    geo_pga.create(Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1))),
    opacity=0.3,
    label="Plane (PGA3)",
)

# Point in OPNS form (grade-3 in PGA3)
viz.add(
    geo_pga(Point(5, 0, 0)),
    color="#ff4444",
    style=PointStyle(size=0.15),
    label="P (OPNS)",
)

# Same point in IPNS form (grade-1 vector)
geo_pga_ipns = Geometry(BasisPGA3(opns=False))
viz.add(
    geo_pga_ipns(Point(5, 0, 0)),
    color="#44ff44",
    style=PointStyle(size=0.10),
    label="P (IPNS)",
)

viz.add(
    # geo_pga(...) creates for Entity/Operator args; analyzes for MV args
    geo_pga.create(Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0))),
    color="#44ff44",
    label="L (x-axis)",
)

# ── N3 ───────────────────────────────────────────────────
viz.add(geo_n3(Point(-3, 2, 0)), color="#ff8844", style=PointStyle(size=0.12), label="N3 Point")
viz.add(
    # geo_n3(...) creates for Entity/Operator args; analyzes for MV args
    geo_n3.create(PointPair(point_a=Point(-3, 0, 0), point_b=Point(0, 2, 0))),
    color="#8844ff",
    label="PtPair",
)
viz.add(
    # geo_n3(...) creates for Entity/Operator args; analyzes for MV args
    geo_n3.create(Line(origin=Point(0, 0, 0), direction=Direction(0, 1, 0))),
    color="#44ffff",
    label="N3 L",
)
viz.add(
    # geo_n3(...) creates for Entity/Operator args; analyzes for MV args
    geo_n3.create(Circle(center=Point(0, 0, 0), normal=Direction(0, 0, 1), radius=2.0)),
    color="#ff44ff",
    label="Circle",
)
viz.add(
    # geo_n3(...) creates for Entity/Operator args; analyzes for MV args
    geo_n3.create(Plane(point=Point(0, 0, 5), normal=Direction(0, 0, 1))),
    opacity=0.2,
    color="#ff88ff",
    label="N3 Plane",
)
viz.add(
    # geo_n3(...) creates for Entity/Operator args; analyzes for MV args
    geo_n3.create(Sphere(center=Point(-2, 0, 0), radius=1.5)),
    style=SphereStyle(wireframe=True),
    opacity=0.35,
    label="Sphere",
)

# ── Explicit analyze() — show what happens internally ─────
# geo_n3(...) creates for Entity/Operator args; analyzes for MV args
mv_sphere = geo_n3.create(Sphere(center=Point(0, 3, 0), radius=1.0))
result = analyze(mv_sphere)
print(f"  MV analyzed to: {result}")
print(f"  Type: {type(result).__name__}")
print(f"  Center: {result.center}, Radius: {result.radius}")

viz.run()
