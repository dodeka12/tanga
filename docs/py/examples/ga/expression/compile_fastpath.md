# Expression.compile() for fast repeated evaluation

**Keywords:** expressions · compile · performance · rotor · sandwich · N3

Builds a versor sandwich `~R * X * R` once, then compares three ways to
evaluate it for the same concrete rotor and point: raw multivector arithmetic,
the bound `Expression` (which now routes fully-bound MV/scalar calls through
an internal compiled fast path), and the explicit `compile()` callable.  Also
shows `AffineExpression.compile()` on a two-term quadratic sum.

## Run

```bash
uv run python py/examples/ga/expression/compile_fastpath.py
```

## Source

[`ga/expression/compile_fastpath.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/ga/expression/compile_fastpath.py)

## Code

````python
#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

r"""compile_fastpath.py — Expression.compile() for fast repeated evaluation.

Builds a versor sandwich ``~R * X * R`` once, then compares three ways to
evaluate it for the same concrete rotor and point: raw multivector arithmetic,
the bound ``Expression`` (which now routes fully-bound MV/scalar calls through
an internal compiled fast path), and the explicit ``compile()`` callable.  Also
shows ``AffineExpression.compile()`` on a two-term quadratic sum.

Run with:  uv run python py/examples/ga/expression/compile_fastpath.py

Keywords: expressions, compile, performance, rotor, sandwich, N3
"""

import time
from typing import Callable

from pytanga import AffineExpression, Variable
from pytanga.basis import BasisN3
from pytanga.geometry import Direction, Geometry, Motor, Rotor


def _time_ms(fn: Callable[[], object], n: int) -> float:
    fn()  # warm-up (also builds the compile plan / caches)
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    return 1000.0 * (time.perf_counter() - t0) / n


def main() -> None:
    alg = BasisN3()
    geo = Geometry(alg)

    R = geo.create_var("R", Motor)
    X = Variable("X", geo.mask_for(Motor))
    sandwich = ~R * X * R

    r = geo(Rotor(0.3, Direction(0, 0, 1)))
    x = 1.0 * alg.e12 + 0.5 * alg.e13 + 0.2 * (alg.e1 ^ alg.einf)

    compiled = sandwich.compile()
    n = 5000
    raw_ms = _time_ms(lambda: r.rev() * x * r, n)
    bound_ms = _time_ms(lambda: sandwich(R=r, X=x), n)
    compiled_ms = _time_ms(lambda: compiled(R=r, X=x), n)

    print("compiled == bound:", (compiled(R=r, X=x) - sandwich.evaluate(R=r, X=x)).mag < 1e-12)
    print(f"raw MV sandwich : {raw_ms:.4f} ms/call")
    print(f"bound Expression: {bound_ms:.4f} ms/call")
    print(f"compiled        : {compiled_ms:.4f} ms/call")

    # AffineExpression.compile() on a two-term quadratic sum.
    v = Variable("V", geo.mask_for(Motor))
    aff = AffineExpression([v * v, v * alg.e12])
    aff_compiled = aff.compile()
    omega = 0.3 * alg.e12 + 0.1 * alg.e13
    print("\naffine compiled == bound:", (aff.evaluate(V=omega) - aff_compiled(V=omega)).mag < 1e-12)


if __name__ == "__main__":
    main()
````
