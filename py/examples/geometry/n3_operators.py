# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""n3_operators.py — Full conformal (N3) operators: Rotors, Motors, Inversions.

Showcases all operator (versor) types in the conformal geometric algebra:
  - 8 operator types: Reflection, Inversion, Rotor, Translator, Dilator,
    Motor, GeneralRotor, GeneralDilator
  - Versor decomposition via blade_factorize_versor()
  - Entity/Operator distinction: sphere analyzed as Sphere vs Inversion
  - Factor-count-based classification

Entities are covered separately in n3_entities.py.

Prerequisite: n3_entities.py
Run with:  uv run python py/examples/geometry/n3_operators.py
"""

import math

from pytanga.algebra import Algebra
from pytanga.geometry import (
    Dilator,
    Direction,
    Inversion,
    Motor,
    Point,
    Reflection,
    Rotor,
    Sphere,
    Translator,
    analyze,
    analyze_entity,
    analyze_operator,
    create,
    create_entity,
    create_operator,
)

n3 = Algebra.from_name("N3")


def hr(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print("=" * 60)


# ── 1. Reflection ──────────────────────────────────────────
hr("1. Reflection — grade-1 versor, no null components")

refl = Reflection(normal=Direction(0, 0, 1))
mv_ref = create_operator(n3, refl)
mv_ref.show("Reflection in plane with normal (0,0,1)")
result = analyze_operator(mv_ref)
print(f"  analyze → {result}")

# ── 2. Inversion ───────────────────────────────────────────
hr("2. Inversion — grade-1 versor with eo component")

inv = Inversion(origin=Point(2, 0, 0))
mv_inv = create_operator(n3, inv)
mv_inv.show("Inversion at origin (2,0,0)")
result = analyze_operator(mv_inv)
print(f"  analyze → {result}")
print(
    f"  origin: ({result.origin.x:.1f}, "
    f"{result.origin.y:.1f}, "
    f"{result.origin.z:.1f})"
)

# ── 3. Rotor ───────────────────────────────────────────────
hr("3. Rotor — two Euclidean reflectors")

rot = Rotor(angle=math.pi / 3, axis=Direction(0, 0, 1))
mv_rot = create_operator(n3, rot)
mv_rot.show("Rotor: 60° about z-axis")
result = analyze_operator(mv_rot)
print(f"  analyze → {result}")

# ── 4. Translator ──────────────────────────────────────────
hr("4. Translator — two einf reflectors, direct coefficient extraction")

t = Translator(vector=Direction(3, 1, 0))
mv_t = create_operator(n3, t)
mv_t.show("Translator by (3, 1, 0)")
result = analyze_operator(mv_t)
print(f"  analyze → {result}")
print(
    f"  vector = ({result.vector.x:.3f}, "
    f"{result.vector.y:.3f}, "
    f"{result.vector.z:.3f})"
)

# ── 5. Dilator ─────────────────────────────────────────────
hr("5. Dilator — two eo reflectors, uniform scaling")

d = Dilator(factor=2.0)
mv_d = create_operator(n3, d)
mv_d.show("Dilator: factor = 2.0")
result = analyze_operator(mv_d)
print(f"  analyze → {result}")
if isinstance(result, Dilator):
    print(f"  factor = {result.factor:.3f}")

# ── 6. Motor — combined rotation + translation ─────────────
hr("6. Motor — rigid body motion (4 factors)")

motor = Motor(
    rotor=Rotor(angle=math.pi / 2, axis=Direction(0, 0, 1)),
    translator=Translator(vector=Direction(1, 0, 0)),
)
mv_m = create_operator(n3, motor)
mv_m.show("Motor: 90° around z + shift along x")
result = analyze_operator(mv_m)
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
    ("Inversion", Inversion(Point(1, 0, 0))),
    ("Rotor", Rotor(angle=0.5, axis=Direction(0, 0, 1))),
    ("Translator", Translator(vector=Direction(3, 0, 0))),
    ("Dilator", Dilator(factor=2.0)),
]

for name, op in ops:
    mv_op = create_operator(n3, op)
    result = analyze_operator(mv_op)
    print(f"  {name}: {type(result).__name__} ✓")

# Motor via generic dispatcher
result = analyze(create(n3, motor))
print(f"  Motor (via analyze): {type(result).__name__} ✓")

# ── 8. Entity/Operator distinction ─────────────────────────
hr("8. Entity vs Operator — same blade, different interpretation")

sphere = Sphere(center=Point(0, 0, 0), radius=2.0)
mv_sph = create(n3, sphere)

# analyze_entity sees the geometric entity
entity_result = analyze_entity(mv_sph)
print(f"  analyze_entity → {entity_result}")
print("    (sphere is a geometric entity)")

# analyze_operator sees the same blade as an Inversion
op_result = analyze_operator(mv_sph)
print(f"  analyze_operator → {op_result}")
print("    (the same blade is also an inversion operator)")

print("\nDone — N3 operators demo complete.")