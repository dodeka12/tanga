#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

r"""Polynomial (repeated-variable) expressions and affine sums.

Builds a polynomial ``f(v) = v*v + v + c`` once — a repeated-variable term plus
a linear term plus a constant, collected into an ``AffineExpression`` — then
evaluates it for a single vector and for a batch of vectors.

Run
---
.. code-block:: bash

    uv run python py/examples/ga/expression/polynomial_demo.py

Keywords: polynomial, expressions, repeated variables, affine
"""

from pytanga import BladeMask, DataArray, Variable
from pytanga.basis import BasisE3


def main() -> None:
    E3 = BasisE3()
    full = BladeMask(E3)

    v = Variable("V1", full)
    c = E3("e3")

    # f(v) = v*v + v + c  (quadratic + linear + constant -> AffineExpression)
    f = (v * v) + v + c
    print("f is an", type(f).__name__, "with", len(f.terms), "terms")

    # single evaluation
    x = E3("e1 + 2 e2")
    print("\nf(x)     =", f(V1=x).to_dict())
    print("direct   =", ((x * x) + x + c).to_dict())

    # batched evaluation
    xs = [E3(f"{i} e1 + {i + 1} e2") for i in range(3)]
    batch = DataArray(xs, masks=("n", full))
    print("\nf over a batch:")
    for xi, fi in zip(xs, f(V1=batch)):
        print("  ", xi.to_dict(), "->", fi.to_dict())


if __name__ == "__main__":
    main()
