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

Keywords: expressions, Variable, rotor, points
"""

from pytanga.basis import BasisN3
from pytanga.expression import DataArray, Variable
from pytanga.geometry import Direction, Geometry, Point, RndPoint, Rotor


def main() -> None:
    N3 = BasisN3()
    geo = Geometry(N3)

    # A fixed rotor: 1.2 rad about the z axis.
    R = geo(Rotor(1.2, Direction(0, 0, 1)))

    # A variable that can hold any N3 multivector.
    v = Variable("P", geo.mask_for(Point))

    # Build the rotation expression once (linear in the point P).
    E = R * v * ~R

    # Evaluate for a single point.
    p = geo(Point(1, 0, 0))
    p_rotated = E(P=p)
    print("rotate one point:")
    print("  ", p, "->", geo(p_rotated))

    # Evaluate for a batch of points in a single call.
    # Create a list of random points in N3.
    points = geo(RndPoint(count=4))

    rotated = E(P=DataArray(points, masks=("pnt_idx", geo.mask_for(Point))))
    print("\nrotate a batch of points:")
    for src, dst in zip(points, rotated):
        print("  ", src, "->", geo(dst))


if __name__ == "__main__":
    main()
