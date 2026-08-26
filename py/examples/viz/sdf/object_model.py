# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""object_model.py — the unified SDF object model in the standard viewer.

Demonstrates per-entity SDF styles, the ``SdfObject`` wrapper, Python operator
CSG (``+``/``-``/``&``/``^``), and an ``SdfGroup`` whose members keep their own
color/opacity and can be re-positioned at runtime by id.

Run with:  uv run python py/examples/viz/sdf/object_model.py
"""

from pytanga.geometry import Circle, Cylinder, Direction, Point, Sphere, Translator
from pytanga.viz import SdfCircleStyle, SdfCylinderStyle, SdfSphereStyle, Visualizer
from pytanga.viz.sdf import ECompose, SdfGroup, SdfObject

viz = Visualizer(title="Tanga — SDF object model")
viz.show()

# ── Per-entity SDF objects (geometry + id + per-entity style) ──
body = SdfObject(
    Sphere(Point(-2.5, 0.0, 0.0), 1.2),
    id="body",
    style=SdfSphereStyle(color="#ffaa00"),
)
body2 = SdfObject(
    Sphere(Point(-1.5, 0.0, 0.0), 1.2),
    id="body",
    style=SdfSphereStyle(color="#ffaa00"),
)


drill = SdfObject(
    Cylinder(
        origin=Point(-2.5, 0.0, 0.0),
        axis=Direction(0.0, 1.0, 0.0),
        length=3.0,
        radius=0.35,
        align_center=0.5,
    ),
    id="drill",
    style=SdfCylinderStyle(color="#44ff44"),
)
ring = SdfObject(
    Circle(Point(-2.5, 0.0, 0.0), 1.2, Direction(0.0, 0.0, 1.0)),
    id="ring",
    style=SdfCircleStyle(color="#ff44ff", tube_radius=0.12),
)

# ── Operators: + (union), - (subtract), & (intersection), ^ (xor) ──
viz.add(body - drill, label="drilled sphere  (body - drill)")

union_grp = viz.add_group("union")
union_grp.add(body - ring, label="sphere ∩ ring    (body & ring)")
union_grp.apply_transform(Translator(Direction(3, 0, 0)))

xor_grp = viz.add_group("xor")
xor_grp.add((body ^ ring) - body2, label="xor")
xor_grp.apply_transform(Translator(Direction(6, 0, 0)))

# ── SdfGroup: multi-member object with per-member materials ────
# The unary `-drill` tags that member with SUBTRACT polarity; `~` would tag it
# INTERSECTION. Each member keeps its own color/opacity (the material table).
group = SdfGroup(body, -drill, ring)
sdf_grp = viz.add_group("sdf")
sdf_grp.add(group, label="SdfGroup  (per-member materials)")
sdf_grp.apply_transform(Translator(Direction(0, 4, 0)))

# Re-position the ring member at runtime, addressing it by id. The proxy box
# recomputes its union AABB so the moved member stays inside the march volume.
# group.set_member_transform("ring", position=Point(2.5, 0.8, 0.0))

viz.flush()

print("An orange drilled sphere, a sphere∩ring, a sphere-xor-ring, and a")
print("three-member SdfGroup (orange body + green drill + magenta ring) should")
print("be visible. The ring member is offset upward; each member shows its own")
print("color/opacity; hover changes the hit member's emissive/opacity.")
print("Close the browser window or press Ctrl+C to exit.")

viz.export_snapshot("_output/sdf_object_model.html")

viz.wait()
