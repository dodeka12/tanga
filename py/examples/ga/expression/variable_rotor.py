#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

r"""Apply a fixed rotor to points with a Variable-backed expression.

Builds ``E = R * v * ~R`` once, then evaluates it for a single point and for a
batch of points — the higher-level counterpart to
``py/examples/ga/tensor/rotor_01.py``.

Run
---
.. code-block:: bash

    uv run python py/examples/ga/expression/variable_rotor.py
"""

import pytanga as pt
from pytanga.basis import BasisN3
from pytanga.geometry import Direction, Geometry, Point
from pytanga.geometry.create_n3 import create_rotor


def main() -> None:
    alg = BasisN3()
    geo = Geometry(alg)

    # A fixed rotor: 1.2 rad about the z axis.
    R = create_rotor(alg, 1.2, Direction(0, 0, 1))

    # A variable that can hold any N3 multivector.
    v = pt.Variable("P", pt.BladeMask.full(alg))

    # Build the rotation expression once (linear in the point P).
    E = R * v * ~R

    # Evaluate for a single point.
    p = geo(Point(1, 0, 0))
    print("rotate one point:")
    print("  ", p, "->", geo(E(P=p)))

    # Evaluate for a batch of points in a single call.
    points = [geo(Point(x, 0, 0)) for x in (0.0, 1.0, 2.0, 3.0)]
    rotated = E(P=points)
    print("\nrotate a batch of points:")
    for src, dst in zip(points, rotated):
        print("  ", src, "->", geo(dst))


if __name__ == "__main__":
    main()
