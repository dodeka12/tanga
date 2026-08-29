# Polynomial (repeated-variable) expressions and affine sums

**Keywords:** polynomial · expressions · repeated variables · affine

Builds a polynomial `f(v) = v*v + v + c` once — a repeated-variable term plus
a linear term plus a constant, collected into an `AffineExpression` — then
evaluates it for a single vector and for a batch of vectors.

## Run

```bash
uv run python py/examples/ga/expression/polynomial_demo.py
```

## Source

[`ga/expression/polynomial_demo.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/ga/expression/polynomial_demo.py)

## Code

````python
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

import pytanga as pt
from pytanga.basis import BasisE3


def main() -> None:
    alg = BasisE3()
    full = pt.BladeMask.full(alg)

    v = pt.Variable("V1", full)
    c = alg.multivector({"e3": 1.0})

    # f(v) = v*v + v + c  (quadratic + linear + constant -> AffineExpression)
    f = (v * v) + v + c
    print("f is an", type(f).__name__, "with", len(f.terms), "terms")

    # single evaluation
    x = alg.multivector({"e1": 1.0, "e2": 2.0})
    print("\nf(x)     =", f(V1=x).to_dict())
    print("direct   =", ((x * x) + x + c).to_dict())

    # batched evaluation
    xs = [alg.multivector({"e1": float(i), "e2": float(i + 1)}) for i in range(3)]
    print("\nf over a batch:")
    for xi, fi in zip(xs, f(V1=xs)):
        print("  ", xi.to_dict(), "->", fi.to_dict())


if __name__ == "__main__":
    main()
````
