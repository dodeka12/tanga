# Multi-variable linear equations with Variables

**Keywords:** expressions · variables · linear equations · Variable

Demonstrates products (GP/IP/OP), addition/subtraction over a shared variable
set, involutions, and two-variable products.

## Run

```bash
uv run python py/examples/ga/expression/equation_demo.py
```

## Source

[`ga/expression/equation_demo.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/ga/expression/equation_demo.py)

## Code

````python
#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

r"""Multi-variable linear equations with Variables.

Demonstrates products (GP/IP/OP), addition/subtraction over a shared variable
set, involutions, and two-variable products.

Run
---
.. code-block:: bash

    uv run python py/examples/ga/expression/equation_demo.py

Keywords: expressions, variables, linear equations, Variable
"""

from pytanga import BladeMask, Variable
from pytanga.basis import BasisE3


def show(label: str, mv) -> None:
    print(f"  {label:<16} {mv.to_dict()}")


def main() -> None:
    alg = BasisE3()
    full = BladeMask.full(alg)

    v = Variable("V1", full)
    w = Variable("V2", full)

    a = alg("2 e1")
    b = alg("3 e2")
    x = alg("e1 - e3")
    y = alg("2 e2")

    # GP + addition over a shared variable: (v*a + v*b) == v*(a+b)
    E = v * a + v * b
    print("(v*a + v*b)(x):")
    show("expression", E(V1=x))
    show("direct", x * a + x * b)

    # Two-variable product.
    E2 = v * w
    print("\n(v*w)(x, y):")
    show("expression", E2(V1=x, V2=y))
    show("direct", x * y)

    # IP / OP.
    print("\nIP / OP:")
    show("(v|a)(x)", (v | a)(V1=x))
    show("(v^a)(x)", (v ^ a)(V1=x))

    # Involutions.
    print("\nreverse / conjugate of E:")
    show("~E(x)", (~E)(V1=x))
    show("conj(E)(x)", E.conj()(V1=x))


if __name__ == "__main__":
    main()
````
