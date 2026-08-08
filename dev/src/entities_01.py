#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Christian Perwass

"""Testing entities."""

from pytanga.basis import BasisN3
from pytanga.geometry import Geometry, Point, Sphere, analyze_entity, create


def main() -> None:

    N3 = BasisN3()
    # geo = Geometry(N3, opns=False)
    s1 = create(N3, Sphere(Point(0, 0, 0), 1.0), opns=False)
    s1.show("s1")
    ana = analyze_entity(s1)
    print(f"Analysis: {ana}")

    p1 = create(N3, Point(0, 0, 0))
    p1.show("p1")

    x = p1 ^ s1
    x.show("x")


if __name__ == "__main__":
    main()
