#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Christian Perwass

"""PGA3 example: creating and transforming 3D points in projective geometric algebra."""

from pytanga import Algebra
from pytanga.basis import BasisN3
from pytanga.geometry import Dilator, Direction, Geometry, Plane, Point, Translator


def main() -> None:
    # Create a N3 algebra
    N3 = BasisN3()
    geo = Geometry(N3)

    p = geo.create(Point(1, 2, 3))
    p.show("p")

    dil = geo.create(Dilator(2))
    dil.show("dil")

    q = dil * p * ~dil
    q.show("q")

    print(geo.which_entity(q))

    trans = geo.create(Translator(Direction(1, 2, 3)))
    trans.show("trans")

    dil_t = trans * dil * trans.rev()
    dil_t.show("dil_t")

    q2 = dil_t * p * dil_t.rev()
    q2.show("q2")
    print(geo.which_entity(q2))

    # Analyze the general dilator
    E = N3.einf ^ N3.eo
    print(E | E)
    print(N3.einf * E)

    d_part = dil_t | E
    d_part.show("d_part")

    t_part = dil_t.ip(N3.eo).op(N3.eo).ip(N3.einf)
    t_part.show("t_part")

    t_euc = -t_part / d_part[0]
    t_euc.show("t_euc")

    D = d_part[0]
    d = (1 - D) / (1 + D)
    print(f"Dilation factor: {d}")


if __name__ == "__main__":
    main()
