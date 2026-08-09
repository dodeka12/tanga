#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Christian Perwass

"""PGA3 example: creating and transforming 3D points in projective geometric algebra."""

from pytanga import Algebra
from pytanga.basis import BasisPGA3
from pytanga.geometry import Direction, Geometry, Plane, Point


def main() -> None:
    # Create a PGA3 algebra
    P3 = BasisPGA3()
    geo = Geometry(P3)

    e0_ = P3.multivector({P3.EP: 1.0, P3.EM: 1.0})
    e0_.show("e0_")

    e0 = P3.e0
    e0.show("e0")
    e1 = P3.e1

    print(f"e0   = {e0}")
    print(f"e0² = {e0 * e0}")  # nilpotent (0)

    # Create a point: p = eo + x*e1 + y*e2 + z*e3
    p = geo.create(Point(1, 2, 3))
    # p = P3("e0 + 1 e1 + 2 e2 + 3 e3")
    print(f"\nPoint at (1, 2, 3): {p}")

    p_d = p.dual()
    p_d.show("p dual")
    ana = geo.which_entity(p_d)
    print(ana)

    # Translation with dual e1  (translator = 1 + t/2 * e1^e0)
    # translator = 1 + 0.5 * (e1 ^ e0)
    # translator.show("translator")
    # p_t = translator * p * translator.rev()
    # p_t.show("p_t")
    # print(f"Translated by 1 along e1: {p_t}")
    # ana = geo.which_entity(p_t)
    # print(ana)
    # print(geo.which_operator(translator))

    p1 = geo.create(Plane(Point(1, 0, 0), Direction(1, 0, 0)))
    p2 = geo.create(Plane(Point(2, 0, 0), Direction(1, 0.1, 0)))
    p1.show("p1")
    p2.show("p2")

    t = p1 * p2
    t.show("t")
    v = t.blade_factorize_versor()
    print(v)


if __name__ == "__main__":
    main()
