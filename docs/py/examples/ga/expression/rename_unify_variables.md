# Re-key variables so independent expressions merge

**Keywords:** expressions · Variable · bind · rename_var · unify · merge

Two helpers each build an expression around their own `Variable` instance (the
same name "X", or a differently-named variable with the same mask).  `bind(X=X)`
and `unify([...], X=X, Y=X)` re-key them onto one canonical variable so they
merge into a single expression under `+`.

## Run

```bash
uv run python py/examples/ga/expression/rename_unify_variables.py
```

## Source

[`ga/expression/rename_unify_variables.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/ga/expression/rename_unify_variables.py)

## Code

````python
#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

r"""rename_unify_variables.py — Re-key variables so independent expressions merge.

Two helpers each build an expression around their own ``Variable`` instance (the
same name "X", or a differently-named variable with the same mask).  ``bind(X=X)``
and ``unify([...], X=X, Y=X)`` re-key them onto one canonical variable so they
merge into a single expression under ``+``.

Run with:  uv run python py/examples/ga/expression/rename_unify_variables.py

Keywords: expressions, Variable, bind, rename_var, unify, merge
"""

from pytanga import BladeMask, Variable
from pytanga.basis import BasisE3
from pytanga.expression import Expression, unify


def build_left(mask: BladeMask) -> Expression:
    """Simulate a class instance building its own "X" variable + expression."""
    x = Variable("X", mask)
    return x * mask.algebra.multivector({"e1": 2.0})


def build_right(mask: BladeMask) -> Expression:
    """Another instance using a different name but the same mask."""
    y = Variable("Y", mask)
    return y * mask.algebra.multivector({"e2": 3.0})


def main() -> None:
    alg = BasisE3()
    mask = BladeMask.full(alg)

    e1 = build_left(mask)
    e2 = build_right(mask)

    # One canonical variable to unify onto.
    x = Variable("X", mask)

    # Re-key both and combine into a single merged expression.
    left, right = unify([e1, e2], X=x, Y=x)
    merged = left + right

    v = alg.multivector({"e1": 1.0, "e2": 4.0})
    expected = v * alg.multivector({"e1": 2.0}) + v * alg.multivector({"e2": 3.0})
    print("merged variable names:", merged.names)
    print("E(v) =", merged(X=v))

    # rename_var: change the evaluation key without changing identity.
    renamed = left.rename_var("X", "P")
    print("\nrenamed names:", renamed.names)
    print("renamed E(P) =", renamed(P=v))
    print("expected     =", expected)


if __name__ == "__main__":
    main()
````
