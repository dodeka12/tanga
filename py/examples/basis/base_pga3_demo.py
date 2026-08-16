# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""
base_pga3_demo.py — Projective GA  (PGA 3D).

Demonstrates BasisPGA3: the null vector e0, finite vs ideal points,
lines, and planes — displayed in the e0/e1/e2/e3 basis.

Run with:
    uv run python py/examples/base_pga3_demo.py
"""

from pytanga import MV
from pytanga.basis import BasisPGA3


def hr(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


hr("BasisPGA3 — PGA 3D (plane‑based geometric algebra)")

PGA = BasisPGA3()
e0: MV = PGA.e0
e1: MV = PGA.e1
e2: MV = PGA.e2
e3: MV = PGA.e3

print("\nBasis blades:")
e0.show("e0 (null vector)")
e1.show("e1")
e2.show("e2")
e3.show("e3")

print("\nNull condition  e0 * e0 = 0:")
(e0 * e0).show("e0 * e0")

print("\nFinite point  p = x·e1 + y·e2 + z·e3 + e0 (string conversion):")
P = PGA("e1 + 2 e2 + 3 e3 + e0")
Q = PGA("-e1 + e3 + e0")
P.show("P = point(1, 2, 3)")
Q.show("Q = point(−1, 0, 1)")

print("\nIdeal / direction  d = x·e1 + y·e2 + z·e3:")
d = PGA("e3")  # direction along z
d.show("d = direction(0, 0, 1)")

print("\nThe e0 term distinguishes finite points from ideal directions:")
print("  (P and Q carry e0; d does not)")

print("\nPQ line (outer product):")
PGA.op(P, Q).show("P ∧ Q")

print("\nPlane through P, Q, d (outer product of three elements):")
PGA.op(PGA.op(P, Q), d).show("P ∧ Q ∧ d")

print("\ne0_inv exists — its geometric product with e0 is the scalar 1:")
(e0 * PGA.e0_inv).show("e0 * e0_inv")

print("\nHigher-grade PGA3 blade — e1 ∧ e2 ∧ e0 (grade-3):")
PGA.op(PGA.op(e1, e2), e0).show("e1 ∧ e2 ∧ e0")

print(f"\nPseudoscalar id: {PGA.pseudoscalar_id}  (= 2^5 − 1 = 31)")