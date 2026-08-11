# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""e3_entities.py — Euclidean 3D geometry: Points, Planes, Reflections, Rotors.

Introduces the geometry submodule on the simplest algebra (E3).  Covers:
  - Entity creation and analysis (Direction, Plane, Space)
  - Operator creation and analysis (Reflection, Rotor)
  - Round-trip: geo.analyze(geo.create(...)) returns the same entity/operator
  - IPNS interpretation via the ``opns=False`` flag

The recommended API is the ``Geometry`` class, which binds an algebra and a
default OPNS flag.  The plain functions ``analyze()``, ``create()``, etc. are
also available (see the Plain Functions section at the end).

Note: E3 cannot represent Points or finite Lines as null spaces — use P3 or
N3 for those.  Points created manually with ``e3.vector()`` can still be
analyzed as Point entities when passed through with ``opns=False``.

Prerequisite: base_e3_demo.py
Run with:  uv run python py/examples/geometry/e3_entities.py
"""

import math

from pytanga.basis import BasisE3
from pytanga.geometry import (
    Direction,
    Geometry,
    Plane,
    Point,
    Reflection,
    Rotor,
    Space,
)


def hr(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


e3 = BasisE3()
geo = Geometry(e3)  # defaults to OPNS

# ── 1. Point (via algebra.vector, not geo.create) ─────────
hr("1. Point — create via algebra, then analyze")

# E3 cannot create Points via geo.create() (points must pass through
# the origin in E3), but we can still analyze a vector as a Point.
point_mv = e3.vector(3, 4, 0)
point_mv.show("e3.vector(3, 4, 0)")
result = geo.analyze(point_mv)
print(f"  analyze → {result}")

# ── 2. Plane (through origin) ───────────────────────────────
hr("2. Plane — bivector representation (via geo.create)")

pl = Plane(point=Point(0, 0, 0), normal=Direction(0, 0, 1))
mv_plane = geo.create(pl)
mv_plane.show("Plane with normal (0,0,1)")
result = geo.which_entity(mv_plane)
print(f"  analyze → {result}")

# ── 3. Space ─────────────────────────────────────────────────
hr("3. Space — pseudoscalar (via geo.create)")

sp = Space()
mv_sp = geo.create(sp)
mv_sp.show("Pseudoscalar I")
result = geo.which_entity(mv_sp)
print(f"  analyze → {result}")

# ── 4. Reflection ────────────────────────────────────────────
hr("4. Reflection — grade-1 versor (via geo.create)")

refl = Reflection(normal=Direction(1, 0, 0))
mv_ref = geo.create(refl)
mv_ref.show("Reflection in plane with normal (1,0,0)")
result = geo.which_operator(mv_ref)
print(f"  analyze → {result}")

# ── 5. Rotor ────────────────────────────────────────────────
hr("5. Rotor — rotation about an axis (via geo.create)")

r = Rotor(angle=math.pi / 3, axis=Direction(0, 0, 1))
mv_rot = geo.create(r)
mv_rot.show("Rotor: 60° about z-axis")
result = geo.which_operator(mv_rot)
print(f"  analyze → {result}")

# ── 6. IPNS (Inner Product Null Space) ───────────────────────
hr("6. IPNS interpretation (opns=False)")

vec = e3.e1
result = geo.which_entity(vec, opns=False)
print(f"  IPNS of e1  → {result}")

biv = e3.e12
result = geo.which_entity(biv, opns=False)
print(f"  IPNS of e12 → {result}")

# ── 7. Combined dispatcher ───────────────────────────────────
hr("7. Combined dispatcher: geo.analyze()")

mv_plane2 = geo.create(Plane(point=Point(0, 0, 0), normal=Direction(0, 1, 0)))
result = geo.analyze(mv_plane2)
print(f"  create + analyze Plane → {result}")

# ── 8. Plain Functions (alternative) ─────────────────────────
hr("8. Plain functions — no Geometry wrapper needed")

from pytanga.geometry import analyze, create  # noqa: E402

mv_ref2 = create(e3, Reflection(normal=Direction(0, 1, 0)))
result = analyze(mv_ref2)
print(f"  plain create + analyze → {result}")

print("\nDone — E3 geometry demo complete.")
