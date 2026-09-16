# Named GA product functions over variables

**Keywords:** expressions · Variable · gp · vp · sp · cp · rc

Builds the named GA products — `gp`, `ip`, `op`, `vp`, `nvp`, `sp`,
`cp`, `acp` and `rc` — between constant multivectors, `Variable`\ s and
expressions, then evaluates a couple of them.  The versor product `vp` shows
the `R * X * ~R` sandwich with a symbolic versor.

## Run

```bash
uv run python py/examples/ga/expression/named_products.py
```

## Source

[`ga/expression/named_products.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/ga/expression/named_products.py)

## Code

````python
#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

r"""named_products.py — Named GA product functions over variables.

Builds the named GA products — ``gp``, ``ip``, ``op``, ``vp``, ``nvp``, ``sp``,
``cp``, ``acp`` and ``rc`` — between constant multivectors, ``Variable``\ s and
expressions, then evaluates a couple of them.  The versor product ``vp`` shows
the ``R * X * ~R`` sandwich with a symbolic versor.

Run with:  uv run python py/examples/ga/expression/named_products.py

Keywords: expressions, Variable, gp, vp, sp, cp, rc
"""

from pytanga.basis import BasisE3
from pytanga.expression import Variable
from pytanga import BladeMask


def main() -> None:
    alg = BasisE3()
    full = BladeMask.full(alg)

    a = alg.multivector({"e1": 2.0, "e12": 3.0})
    v = Variable("V1", full)
    x = alg.multivector({"e1": 1.0, "e2": 4.0})

    # Each product builds a symbolic Expression (linear in v here).
    inner = v.ip(a)
    outer = v.op(a)
    comm = v.cp(a)
    anti = v.acp(a)
    rcon = v.rc(a)

    print("inner    v | a  ->", inner(V1=x))
    print("outer    v ^ a  ->", outer(V1=x))
    print("comm     0.5(v*a - a*v) ->", comm(V1=x))
    print("anticomm 0.5(v*a + a*v) ->", anti(V1=x))
    print("right-contr v ⌊ a ->", rcon(V1=x))

    # sp is scalar-valued: fully binding unwraps to a Python float.
    s = v.sp(a)
    print("scalar product ->", s(V1=x), type(s(V1=x)).__name__)

    # vp: a symbolic versor sandwich R * X * ~R.
    r = Variable("R", full)
    p = Variable("P", full)
    rot = r.vp(p)
    rr = alg.multivector({"e12": 1.0})
    pp = alg.multivector({"e1": 2.0, "e2": 3.0})
    print("versor R * P * ~R ->", rot(R=rr, P=pp))


if __name__ == "__main__":
    main()
````
