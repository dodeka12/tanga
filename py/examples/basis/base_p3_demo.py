# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""
base_p3_demo.py — Projective 3D geometric algebra  G(4, 0).

Demonstrates BasisP3: basis blades including the homogeneous direction e4,
string-based homogeneous point construction, and join of points via the
outer product (lines and planes).

Run with:
    uv run python py/examples/base_p3_demo.py
"""

from pytanga import MV
from pytanga.basis import BasisP3


def hr(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


hr("BasisP3 — Projective 3D  G(4, 0)")

P3 = BasisP3()
e1: MV = P3.e1
e2: MV = P3.e2
e3: MV = P3.e3
e4: MV = P3.e4
I: MV = P3.I  # noqa: E741

print("\nBasis blades:")
e1.show("e1")
e2.show("e2")
e3.show("e3")
e4.show("e4 (homogeneous direction)")
I.show("I  = pseudoscalar")

print("\nHomogeneous points (string conversion: x·e1 + y·e2 + z·e3 + e4):")
A = P3("e1 + e4")
B = P3("e2 + e4")
C = P3("e3 + e4")
A.show("A = point(1, 0, 0)")
B.show("B = point(0, 1, 0)")
C.show("C = point(0, 0, 1)")

print("\nJoin of two points (outer product gives a line):")
P3.op(A, B).show("A ∧ B")

print("\nJoin of three points (outer product gives a plane):")
P3.op(P3.op(A, B), C).show("A ∧ B ∧ C")

print("\nAll-grade multivector (grades 0–4) via show():")
mv = P3.multivector("1 + 2 e1 + 3 e12 + 4 e14 + 5 e123 + 6 e124 + 7 I")
mv.show("1 + 2e1 + 3e12 + 4e14 + 5e123 + 6e124 + 7I")
