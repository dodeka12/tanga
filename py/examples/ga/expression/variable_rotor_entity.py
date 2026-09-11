#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

r"""Rotate a list of points with a variable rotor and variable points.

Builds ``E = R * P * ~R`` once, where both ``R`` (a rotor) and ``P`` (a point)
are symbolic variables whose blade masks come from
:meth:`pytanga.geometry.Geometry.create_var`.  The same expression is then
evaluated with a concrete rotor and a list of points.

Run
---
.. code-block:: bash

    uv run python py/examples/ga/expression/variable_rotor_entity.py

Keywords: expressions, Variable, rotor, points, entity
"""

from pytanga.basis import BasisN3
from pytanga.geometry import Direction, Geometry, Point, Rotor


def main() -> None:
    N3 = BasisN3()
    geo = Geometry(N3)

    # Symbolic variables with geometry-derived blade masks:
    #   R  may hold any rotor    (scalar + Euclidean bivectors)
    #   P  may hold any point    (grade-1 OPNS conformal point)
    R = geo("R", Rotor)
    P = geo("P", Point)
    print("rotor mask :", R.mask.names())
    print("point mask :", P.mask.names())

    # Build the rotation expression once (bilinear in R and P).
    E = R * P * ~R

    # A concrete rotor and a list of concrete points (entities).
    r = geo(Rotor(1.2, Direction(0, 0, 1)))
    points = [geo(Point(x, 0, 0)) for x in (0.0, 1.0, 2.0, 3.0)]

    # Apply the rotor to each point in a single batched call.
    rotated = E(R=r, P=points)

    print("\nrotate a list of points:")
    for src, dst in zip(points, rotated):
        print("  ", geo(src), "->", geo(dst))


if __name__ == "__main__":
    main()
