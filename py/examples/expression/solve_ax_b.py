#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

r"""Solve the general multivector equation ``A X = B`` with expressions.

Builds the linear map ``forward = A * X`` once, then recovers the unknown
``X`` in two ways:

- :meth:`Expression.inv` — inverts the square, invertible map, returning a new
  expression that maps ``B`` back to ``X``.
- :meth:`Expression.lstsq` — solves ``M · vec(X) = vec(B)`` numerically with an
  explicit right-hand side.

Run
---
.. code-block:: bash

    uv run python py/examples/expression/solve_ax_b.py
"""

from __future__ import annotations

from pytanga import BladeMask, Variable
from pytanga.basis import BasisP3


def main() -> None:
    alg = BasisP3()
    full = BladeMask.full(alg)

    # A concrete invertible multivector and its "true" solution.
    A = alg.multivector({0: 1.0, 1: 2.0, 2: -1.0, 4: 0.5})
    X_true = alg.multivector({0: 3.0, 1: -2.0, 2: 1.0, 4: 0.25, 7: 1.5})
    B = A * X_true

    # The linear map  X -> A * X  (full-mask variable).
    X = Variable("X", full)
    forward = A * X

    # Fit 1 — exact inverse.
    X_inv = forward.inv("X")(X=B)
    print("Solve A X = B via Expression.inv:")
    print("  A            =", {k: round(v, 4) for k, v in A.to_dict().items()})
    print("  B            =", {k: round(v, 4) for k, v in B.to_dict().items()})
    print("  X recovered  =", {k: round(v, 4) for k, v in X_inv.to_dict().items()})
    print("  |A·X - B|    =", (A * X_inv - B).mag)

    # Fit 2 — least squares with an explicit right-hand side.
    X_lstsq = forward.lstsq(rhs=B)
    print("\nSolve A X = B via Expression.lstsq (explicit rhs):")
    print("  X recovered  =", {k: round(v, 4) for k, v in X_lstsq.to_dict().items()})
    print("  |A·X - B|    =", (A * X_lstsq - B).mag)


if __name__ == "__main__":
    main()
