# draw arbitrary quadrics via entities + GA translation

**Keywords:** quadric · ray · Quadric3D · hyperboloid · paraboloid · cone · translator

Builds three non-ellipsoid quadrics from entities — a hyperboloid of one sheet, a
cone, and an elliptic paraboloid — and draws each in the standard viewer.  The
hyperboloid and paraboloid are built at the origin with `geo(...)` and moved to
their positions with `geo(Translator(...))` (a linear-map expression, since
translation has no versor in the quadric space).  Each result is a raw quadric
MV, rendered through the analytic ray renderer.

## Run

```bash
uv run python py/examples/ga/quadric/general_quadric.py
```

## Source

[`ga/quadric/general_quadric.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/ga/quadric/general_quadric.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""general_quadric.py — draw arbitrary quadrics via entities + GA translation.

Builds three non-ellipsoid quadrics from entities — a hyperboloid of one sheet, a
cone, and an elliptic paraboloid — and draws each in the standard viewer.  The
hyperboloid and paraboloid are built at the origin with ``geo(...)`` and moved to
their positions with ``geo(Translator(...))`` (a linear-map expression, since
translation has no versor in the quadric space).  Each result is a raw quadric
MV, rendered through the analytic ray renderer.

Run with:  uv run python py/examples/ga/quadric/general_quadric.py

Keywords: quadric, ray, Quadric3D, hyperboloid, paraboloid, cone, translator
"""

import math

from pytanga.entity import Direction, Point
from pytanga.expression import Expression
from pytanga.geometry import Cone, Geometry, Hyperboloid, Paraboloid, Translator
from pytanga.quadric import BasisQ3
from pytanga.viz import Visualizer

geo = Geometry(BasisQ3(opns=False))

viz = Visualizer(title="Tanga — general quadrics (analytic ray renderer)")

# Hyperboloid of one sheet:  x² + y² - z² = 1, centred at (-4, 0, 0).
hyper = geo(Hyperboloid(Point(0, 0, 0), (1.0, 1.0, 1.0), sheets=1))
translation = geo(Translator(Direction(-4.0, 0.0, 0.0)))
assert isinstance(translation, Expression)
hyper = translation @ hyper
viz.add(hyper, color="#44aaff", label="Hyperboloid (1 sheet)")

# Cone:  x² + y² - z² = 0, apex at the origin.
cone = geo(Cone(Point(0, 0, 0), Direction(0, 0, 1), math.pi / 4.0))
viz.add(cone, color="#ff8844", label="Cone")

# Elliptic paraboloid:  (x - 4)² + y² - z = 0, vertex at (4, 0, 0).
parab = geo(Paraboloid(Point(0, 0, 0), (1.0, 1.0)))
translation = geo(Translator(Direction(4.0, 0.0, 0.0)))
assert isinstance(translation, Expression)
parab = translation @ parab
viz.add(parab, color="#44ffaa", label="Paraboloid")

print("Three general quadrics, each rendered through the analytic ray path.")
viz.show()
viz.wait()
````
