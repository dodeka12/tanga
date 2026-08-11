# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""n3_operators.py — Full conformal (N3) operators: Rotors, Motors, Inversions.

Showcases all operator (versor) types in the conformal geometric algebra:
  - 7 operator types: Reflection, Inversion, Rotor, Translator, Dilator,
    Motor, GeneralRotor
  - Versor decomposition via blade_factorize_versor()
  - Entity/Operator distinction: sphere analyzed as Sphere vs Inversion
  - Factor-count-based classification

Uses the ``Geometry`` class to bind the N3 algebra.  Plain functions remain
available as an alternative (see the last section).

Entities are covered separately in n3_entities.py.

Prerequisite: n3_entities.py
Run with:  uv run python py/examples/geometry/n3_operators.py
"""

import math

from pytanga.basis import BasisN3
from pytanga.geometry import (
    Dilator,
    Direction,
    Geometry,
    Inversion,
    Motor,
    Point,
    Reflection,
    Rotor,
    Sphere,
    Translator,
)

n3 = BasisN3()
geo = Geometry(n3)  # defaults to OPNS


def hr(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


# ── 1. Reflection ──────────────────────────────────────────
hr("1. Reflection — grade-1 versor, no null components")

refl = Reflection(normal=Direction(0, 0, 1))
mv_ref = geo.create(refl)
mv_ref.show("Reflection in plane with normal (0,0,1)")
result = geo.which_operator(mv_ref)
print(f"  analyze → {result}")

# ── 2. Inversion ───────────────────────────────────────────
hr("2. Inversion — grade-1 versor with eo component")

inv = Inversion(center=Point(2, 0, 0))
mv_inv = geo.create(inv)
mv_inv.show("Inversion at origin (2,0,0)")
result = geo.which_operator(mv_inv)
print(f"  analyze → {result}")
print(
    f"  center: ({result.center.x:.1f}, {result.center.y:.1f}, {result.center.z:.1f})"
)

# ── 3. Rotor ───────────────────────────────────────────────
hr("3. Rotor — two Euclidean reflectors")

rot = Rotor(angle=math.pi / 3, axis=Direction(0, 0, 1))
mv_rot = geo.create(rot)
mv_rot.show("Rotor: 60° about z-axis")
result = geo.which_operator(mv_rot)
print(f"  analyze → {result}")

# ── 4. Translator ──────────────────────────────────────────
hr("4. Translator — two einf reflectors, direct coefficient extraction")

t = Translator(vector=Direction(3, 1, 0))
mv_t = geo.create(t)
mv_t.show("Translator by (3, 1, 0)")
result = geo.which_operator(mv_t)
print(f"  analyze → {result}")
print(
    f"  vector = ({result.vector.x:.3f}, {result.vector.y:.3f}, {result.vector.z:.3f})"
)

# ── 5. Dilator ─────────────────────────────────────────────
hr("5. Dilator — two eo reflectors, uniform scaling")

d = Dilator(factor=2.0)
mv_d = geo.create(d)
mv_d.show("Dilator: factor = 2.0")
result = geo.which_operator(mv_d)
print(f"  analyze → {result}")
if isinstance(result, Dilator):
    print(f"  factor = {result.factor:.3f}")

# ── 6. Motor — combined rotation + translation ─────────────
hr("6. Motor — rigid body motion (4 factors)")

motor = Motor(
    rotor=Rotor(angle=math.pi / 2, axis=Direction(0, 0, 1)),
    translator=Translator(vector=Direction(1, 0, 0)),
)
mv_m = geo.create(motor)
mv_m.show("Motor: 90° around z + shift along x")
result = geo.which_operator(mv_m)
print(f"  analyze → {result}")
if isinstance(result, Motor):
    print(f"    rotor angle = {result.rotor.angle:.3f} rad")
    print(
        f"    translator  = ({result.translator.vector.x:.1f}, "
        f"{result.translator.vector.y:.1f}, "
        f"{result.translator.vector.z:.1f})"
    )

# ── 7. Operator coverage summary ───────────────────────────
hr("7. Operator coverage — all N3 operator types")

ops = [
    ("Reflection", Reflection(Direction(0, 0, 1))),
    ("Inversion", Inversion(center=Point(1, 0, 0))),
    ("Rotor", Rotor(angle=0.5, axis=Direction(0, 0, 1))),
    ("Translator", Translator(vector=Direction(3, 0, 0))),
    ("Dilator", Dilator(factor=2.0)),
]

for name, op in ops:
    mv_op = geo.create(op)
    result = geo.which_operator(mv_op)
    print(f"  {name}: {type(result).__name__} ✓")

# Motor via combined dispatcher
result = geo.analyze(geo.create(motor))
print(f"  Motor (via analyze): {type(result).__name__} ✓")

# ── 8. Entity/Operator distinction ─────────────────────────
hr("8. Entity vs Operator — same blade, different interpretation")

sphere = Sphere(center=Point(0, 0, 0), radius=2.0)
mv_sph = geo.create(sphere)

# which_entity sees the geometric entity
entity_result = geo.which_entity(mv_sph)
print(f"  which_entity → {entity_result}")
print("    (sphere is a geometric entity)")

# which_operator sees the same blade as an Inversion
try:
    op_result = geo.which_operator(mv_sph)
    print(f"  which_operator → {op_result}")
    print("    (the same blade is also an inversion operator)")
except (ValueError, NotImplementedError):
    print("  which_operator → (grade-4 versor analysis not yet available)")

# ── 9. Plain Functions (alternative) ───────────────────────
hr("9. Plain functions — no Geometry wrapper needed")

from pytanga.geometry import analyze_operator, create_operator  # noqa: E402

mv_op = create_operator(n3, Reflection(Direction(1, 0, 0)))
result = analyze_operator(mv_op)
print(f"  plain create + analyze → {result}")

print("\nDone — N3 operators demo complete.")
