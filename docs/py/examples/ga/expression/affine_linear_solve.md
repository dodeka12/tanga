# Solve a single-linear-map AffineExpression

**Keywords:** expressions · AffineExpression · solve · least-squares · inv

Builds `F = u * w + (u * u) * w` — two terms, both linear in `w`, that do
not merge because they have different `u`-degree.  Binding `u` to a constant
leaves a single linear map in `w`, which is then solved three ways: exact
inverse (`inv`), least squares with an explicit right-hand side (`lstsq`),
and singular-value decomposition (`svd`).

## Run

```bash
uv run python py/examples/ga/expression/affine_linear_solve.py
```

## Source

[`ga/expression/affine_linear_solve.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/ga/expression/affine_linear_solve.py)

## Code

````python
#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

r"""Solve a single-linear-map ``AffineExpression``.

Builds ``F = u * w + (u * u) * w`` — two terms, both linear in ``w``, that do
not merge because they have different ``u``-degree.  Binding ``u`` to a constant
leaves a single linear map in ``w``, which is then solved three ways: exact
inverse (``inv``), least squares with an explicit right-hand side (``lstsq``),
and singular-value decomposition (``svd``).

Run
---
.. code-block:: bash

    uv run python py/examples/ga/expression/affine_linear_solve.py

Keywords: expressions, AffineExpression, solve, least-squares, inv
"""

from __future__ import annotations

from pytanga import BladeMask, Variable
from pytanga.basis import BasisE3


def main() -> None:
    E3 = BasisE3()
    full = BladeMask(E3)

    u = Variable("u", full)
    w = Variable("w", full)

    # Two terms, linear in w, but different u-degree -> AffineExpression.
    F = (u * w) + (u * u) * w

    u_val = E3("0.5 e1")
    F_u = F(u=u_val)  # single linear map in w (two terms)

    w0 = E3("e2")
    rhs = F_u(w=w0)

    w_inv = F_u.inv("w")(w=rhs)
    w_lstsq = F_u.lstsq(rhs=rhs)
    svalues, _mvs = F_u.svd()

    print("AffineExpression as a single linear map in 'w':")
    print("  terms        :", len(F_u.terms))
    print("  inv round-trip |w - inv(w)(F_u(w))| :", (w0 - w_inv).mag)
    print("  lstsq        |F_u(w_lstsq) - rhs|   :", (F_u(w=w_lstsq) - rhs).mag)
    print("  singular values                       :", [f"{v:.4f}" for v in svalues])


if __name__ == "__main__":
    main()
````
