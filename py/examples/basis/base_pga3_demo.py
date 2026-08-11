# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""
base_pga3_demo.py — Projective GA  (PGA 3D, built on top of BasisN3).

Demonstrates BasisPGA3: finite and ideal points, lines, planes, and
higher-grade blades — all displayed in the einf/eo null-vector basis.

Run with:
    uv run python py/examples/base_pga3_demo.py
"""

from pytanga import MV
from pytanga.basis import BasisPGA3


def hr(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


hr("BasisPGA3 — PGA 3D (built on BasisN3)")

PGA = BasisPGA3()
e1: MV = PGA.e1
e2: MV = PGA.e2
e3: MV = PGA.e3
ep: MV = PGA.ep
em: MV = PGA.em
einf: MV = PGA.einf
eo: MV = PGA.eo
I: MV = PGA.I  # noqa: E741

print("\nFinite point factory  p = x·e1 + y·e2 + z·e3 + eo:")
P = PGA.point(1, 2, 3)
Q = PGA.point(-1, 0, 1)
P.show("P = point(1, 2, 3)")
Q.show("Q = point(−1, 0, 1)")

print("\nIdeal / direction factory  d = x·e1 + y·e2 + z·e3:")
d = PGA.vector(0, 0, 1)  # direction along z
d.show("d = vector(0, 0, 1)")

print("\nNull condition  ip(point, einf) = −1 for any finite point:")
PGA.ip(P, einf).show("ip(P, einf)")
PGA.ip(Q, einf).show("ip(Q, einf)")

print("\nDirection at infinity has ip(direction, einf) = 0:")
PGA.ip(d, einf).show("ip(d, einf)")

print("\nPQ line (outer product):")
PGA.op(P, Q).show("P ∧ Q")

print("\nPlane through P, Q, d (outer product of three elements):")
PGA.op(PGA.op(P, Q), d).show("P ∧ Q ∧ d")

print("\nNote: all blades displayed in einf/eo notation (no ep/em appear).")

print("\nHigher-grade PGA3 blade — e1 ∧ e2 ∧ eo (grade-3):")
PGA.op(PGA.op(e1, e2), eo).show("e1 ∧ e2 ∧ eo")

print(f"\nPseudoscalar id: {PGA.pseudoscalar_id}  (= 2^5 − 1 = 31)")
