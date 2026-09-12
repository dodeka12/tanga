#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

r"""Sum an ``AffineExpression`` over a batched variable.

Builds ``f = v * w + c`` — a term linear in ``v`` plus a constant offset — and
reduces a ``DataArray``-introduced counting axis at the top level.  Terms that
carry the axis are reduced; the constant term is broadcast (scaled by the summed
weights).

Run
---
.. code-block:: bash

    uv run python py/examples/ga/expression/affine_counting_reduction.py

Keywords: expressions, AffineExpression, counting axis, DataArray, weighted sum
"""

from __future__ import annotations

import numpy as np

from pytanga import BladeMask, DataArray, Variable
from pytanga.basis import BasisE3


def main() -> None:
    E3 = BasisE3()
    full = BladeMask(E3)

    v = Variable("v", full)
    w = Variable("w", full)
    c = E3("2 e3")

    # AffineExpression: v*w (linear in v) plus a constant offset c.
    f = (v * w) + c

    vecs = [E3("e1"), E3("2 e1"), E3("e1 + e2")]
    weights = np.array([1.0, 2.0, 0.5])

    # Bind v to a batch (counting axis "n"), then reduce "n" at the top level.
    partial = f(v=DataArray(vecs, masks=("n", full)))
    result = partial(n=weights)  # still an AffineExpression over {w}

    w_val = E3("3 e2")
    reduced = result(w=w_val)
    expected = sum(wt * (vec * w_val) for wt, vec in zip(weights, vecs)) + c * float(
        weights.sum()
    )

    print("AffineExpression counting-axis reduction + broadcast:")
    print("  partial terms:", len(partial.terms))
    print("  result(w=3 e2) :", {k: round(v, 4) for k, v in reduced.to_dict().items()})
    print("  expected       :", {k: round(v, 4) for k, v in expected.to_dict().items()})
    print("  |diff|         :", (reduced - expected).mag)


if __name__ == "__main__":
    main()
