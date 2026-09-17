#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

r"""project_onto_euclidean_n3.py — Project an N3 expression onto the Euclidean basis.

Builds an N3 (conformal) expression whose output mixes Euclidean blades with
``einf``/``eo`` components, then uses ``Expression.project_onto`` to restrict it
to the Euclidean basis ``e1, e2, e3, e12, e13, e23``, dropping the null terms.

Run with:  uv run python py/examples/ga/expression/project_onto_euclidean_n3.py

Keywords: expressions, Variable, project_onto, BladeMask, N3, Euclidean
"""

from typing import cast

from pytanga import BladeMask, MV, Variable
from pytanga.basis import BasisN3


def main() -> None:
    alg = BasisN3()
    full = BladeMask.full(alg)

    # Euclidean subspace blades of N3: e1, e2, e3, e12, e13, e23.
    euclid = BladeMask(alg, [alg.E1, alg.E2, alg.E3, alg.E12, alg.E13, alg.E23])

    # A null-inflected constant: Euclidean direction plus infinity/origin terms.
    c = alg.e1 * 1.0 + alg.e2 * 2.0 + alg.e3 * 3.0 + alg.einf * 4.0 + alg.eo * 5.0

    x = Variable("X", full)
    e = x * c  # Expression: geometric product of a variable and a constant.

    p = e.project_onto(euclid)

    v = alg.e1 * 1.0 + alg.e2 * 1.0 + alg.e3 * 1.0
    before = cast(MV, e(X=v))
    after = cast(MV, p(X=v))
    expected = before.project_onto(euclid)

    print("X          =", v)
    print("E.out_mask =", len(e.out_mask), "blades (full N3)")
    print("p.out_mask =", p.out_mask.names())
    print()
    print("E(X)       =", before)
    print("p(X)       =", after)
    print("expected   =", expected)

    assert (after - expected).mag < 1e-12
    print("\nproject_onto() reduced the expression to the Euclidean basis.")


if __name__ == "__main__":
    main()
