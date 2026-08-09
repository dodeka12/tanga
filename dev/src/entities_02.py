#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Christian Perwass

"""Testing entities."""

from pytanga.basis import BasisN3
from pytanga.geometry import Geometry, Point, Sphere, analyze_entity, create


def main() -> None:

    N3 = BasisN3()
    geo = Geometry(N3, opns=False)

    s1 = geo.create(Sphere(Point(0, 0, 0), 1.0))
    s1.show("s1")

    s2 = geo.create(Sphere(Point(0.00, 0, 0), 2.0))
    s2.show("s2")

    c = s1 ^ s2
    c.show("c")

    # ana = geo.which_entity(c)
    # print(f"Analysis: {ana}")

    cd = c.dual()
    cd.show("cd")


if __name__ == "__main__":
    main()
