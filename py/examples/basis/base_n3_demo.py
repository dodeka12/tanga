# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""
base_n3_demo.py — Null / conformal 3D algebra  G(5, 0b10000).

Demonstrates BasisN3: the extra null basis vectors einf and eo (composed
from ep and em), null conditions, and blades displayed in the einf/eo basis.

Run with:
    uv run python py/examples/base_n3_demo.py
"""

from pytanga import MV
from pytanga.basis import BasisN3


def hr(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


hr("BasisN3 — Null / conformal 3D  G(5, 0b10000)")

N3 = BasisN3()
e1: MV = N3.e1
e2: MV = N3.e2
e3: MV = N3.e3
ep: MV = N3.ep
em: MV = N3.em
einf: MV = N3.einf
eo: MV = N3.eo
I: MV = N3.I  # noqa: E741

print("\nExtra basis vectors:")
ep.show("ep  (ep² = +1)")
em.show("em  (em² = −1)")

print("\nComposed null vectors:")
einf.show("einf = ep + em")
eo.show("eo   = 0.5·em − 0.5·ep")  # noqa: F821

print("\nNull conditions  (both must be 0):")
(einf * einf).show("einf * einf")
(eo * eo).show("eo   * eo  ")

print("\nInner product eo · einf  (= −1 by definition):")
N3.ip(eo, einf).show("ip(eo, einf)")

print("\nGrade-2 blades displayed in einf/eo notation (not ep/em):")
N3.op(e1, einf).show("e1 ∧ einf")
N3.op(e1, eo).show("e1 ∧ eo")
N3.op(e1, e2).show("e1 ∧ e2")
N3.op(einf, eo).show("einf ∧ eo")

print("\nGrade-3 and grade-4 blades:")
N3.op(N3.op(e1, e2), einf).show("e1 ∧ e2 ∧ einf")
N3.op(N3.op(e1, einf), eo).show("e1 ∧ einf ∧ eo")
N3.op(N3.op(N3.op(e1, e2), einf), eo).show("e1 ∧ e2 ∧ einf ∧ eo")  # noqa: F821

print("\nRound-trip: mixed MV with all null-vector grades:")
# Build 3*(e1∧einf) + 5*(e1∧eo) + 7*(e1∧e2) using named blade keys:
# e1∧einf = e14+e15; e1∧eo = −0.5·e14 + 0.5·e15; e1∧e2 = e12
mixed = N3.multivector({"e12": 7, "e14": 3 + 5 * (-0.5), "e15": 3 + 5 * 0.5})
mixed.show("7(e1∧e2) + 3(e1∧einf) + 5(e1∧eo)")
