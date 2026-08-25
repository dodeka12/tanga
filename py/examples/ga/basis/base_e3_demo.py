# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""
base_e3_demo.py — Euclidean 3D geometric algebra  G(3, 0).

Demonstrates BasisE3: basis blades, string-based multivector construction,
geometric and outer products, and mixed-grade multivectors.

Run with:
    uv run python py/examples/ga/basis/base_e3_demo.py
"""

from pytanga import MV
from pytanga.basis import BasisE3


def hr(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


hr("BasisE3 — Euclidean 3D  G(3, 0)")

E3 = BasisE3()
e1: MV = E3.e1
e2: MV = E3.e2
e3: MV = E3.e3
e12: MV = E3.e12
e31: MV = E3.e31
e23: MV = E3.e23
I: MV = E3.I  # noqa: E741

print("\nBasis blades:")
e1.show("e1")
e2.show("e2")
e3.show("e3")
e12.show("e12 = e1 ∧ e2")
e31.show("e31 = e3 ∧ e1")
e23.show("e23 = e2 ∧ e3")
I.show("I   = pseudoscalar")

print("\nVector (string conversion):")
v = E3("e1 + 2 e2 + 3 e3")
v.show("v = (1, 2, 3)")

print("\nGeometric product examples:")
(e1 * e1).show("e1 * e1  (= +1 scalar)")
(e1 * e2).show("e1 * e2  (= e12 bivector)")
(e2 * e1).show("e2 * e1  (= −e12, anticommutes)")

print("\nOuter product: v ∧ e1  (kills the e1 component)")
E3.op(v, e1).show("v ∧ e1")

print("\nPseudoscalar squares to −1 in G(3,0):")
(I * I).show("I * I")

print("\nAll-grade multivector (grades 0–3) via show():")
mv = E3("5 + e1 + 2 e2 + 3 e3 + 4 e12 - e13 + 2 e23 - 7 I")
mv.show("5 + e1 + 2e2 + 3e3 + 4e12 − e13 + 2e23 − 7I")
