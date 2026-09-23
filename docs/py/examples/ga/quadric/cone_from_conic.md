# lift a 2D conic into a 3D cone through an apex

**Keywords:** quadric · conic · cone · lift · translator · outer product

Fits a 2D conic to five points with the join/dual primitive (`geo(Point(...))`
→ outer product → undualize), lifts it to a cone (apex at the origin) with the
`q3(conic)` parameter mapping, then moves the apex with `geo(Translator(...))`
— a linear-map expression, since translation has no versor in the quadric space.
Prints the resulting rank/kind and verifies incidence via the scalar product.

## Run

```bash
uv run python py/examples/ga/quadric/cone_from_conic.py
```

## Source

[`ga/quadric/cone_from_conic.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/ga/quadric/cone_from_conic.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""cone_from_conic.py — lift a 2D conic into a 3D cone through an apex.

Fits a 2D conic to five points with the join/dual primitive (``geo(Point(...))``
→ outer product → undualize), lifts it to a cone (apex at the origin) with the
``q3(conic)`` parameter mapping, then moves the apex with ``geo(Translator(...))``
— a linear-map expression, since translation has no versor in the quadric space.
Prints the resulting rank/kind and verifies incidence via the scalar product.

Run with:  uv run python py/examples/ga/quadric/cone_from_conic.py

Keywords: quadric, conic, cone, lift, translator, outer product
"""

import math

from pytanga.entity import Direction, Point
from pytanga.expression import Expression
from pytanga.geometry import Geometry, Translator
from pytanga.quadric import BasisQ2, BasisQ3, Quadric3D


def _main() -> None:
    q2 = BasisQ2()
    geo2 = Geometry(q2)
    q3 = BasisQ3()
    geo3 = Geometry(q3)

    # Base conic: the ellipse x^2/4 + y^2 = 1, fitted from five points via the join.
    pts = [
        (2.0, 0.0),
        (0.0, 1.0),
        (-2.0, 0.0),
        (0.0, -1.0),
        (1.0, math.sqrt(3.0) / 2.0),
    ]
    emb = [geo2(Point(x, y, 0)) for x, y in pts]
    conic = (emb[0] ^ emb[1] ^ emb[2] ^ emb[3] ^ emb[4]).undual()

    # Lift to a cone (apex at origin): q3(conic) relabels the conic coefficients.
    cone0 = q3(conic)

    # Move the apex: a Translator is a linear-map expression (no versor).
    apex = Direction(1.0, -2.0, 3.0)
    trans = geo3(Translator(apex))
    assert isinstance(trans, Expression), "a quadric-space Translator is an Expression"
    cone = trans.evaluate(cone0)

    # Analyze the OPNS cone (dual -> grade-9) into a Quadric3D.
    quad = geo3.which_entity(cone.dual())
    assert isinstance(quad, Quadric3D)
    print("Cone quadric:")
    print("  rank:", quad.rank, " kind:", quad.kind.value)

    # Incidence via the scalar product: embed(p) · coeff(A) = ½ xᵀ A x.
    print("  apex incidence:", round(float(geo3(Point(1.0, -2.0, 3.0)).sp(cone)), 12))
    print("  base point incidence:", round(float(geo3(Point(3.0, -2.0, 4.0)).sp(cone)), 12))


if __name__ == "__main__":
    _main()
````
