# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Rotor analysis in PGA3"""

from __future__ import annotations

import math

from pytanga.algebra._algebra import Algebra
from pytanga.basis import BasisPGA3
from pytanga.geometry import Geometry
from pytanga.geometry.analysis import analyze_entity, analyze_operator
from pytanga.geometry.create import create_entity, create_operator
from pytanga.geometry.entities import Direction, Line, Plane, Point
from pytanga.geometry.operators import (
    GeneralRotor,
    Motor,
    Rotor,
    Translator,
)

P3 = BasisPGA3()
geo = Geometry(P3)

p1 = geo.create(Plane(Point(0, 0, 0), Direction(1, 0, 0)))
p2 = geo.create(Plane(Point(1, 0, 0), Direction(1, 1, 0)))

p1.show("p1")
p2.show("p2")


def ana_rotor(rot):
    s = rot.grade(0)[0]
    bi = rot.grade(2)
    q = rot.grade(4)

    bi_e = bi.op(P3.e0).ip(P3.e0_inv)
    bi_e.show("bi_e")
    bi_e_mag = bi_e.mag

    if bi_e_mag > 1e-15:
        cos_a = s
        sin_a = bi_e.mag
        angle = 2 * math.atan2(sin_a, cos_a)
        angle_deg = math.degrees(angle)
        print(f"Angle: {angle_deg}")

        axis = bi_e.ip(P3({P3.E123: 1})) / bi_e.mag
        axis.show("axis")

    q_mag = q.mag
    if q_mag > 1e-15:
        print("test for motor")
        if bi_e_mag < 1e-15:
            raise ValueError("Given multivector cannot be interpreted as operator")

        tb = bi.ip(P3.e0_inv)
        tb.show("tb")
        if tb.mag < 1e-15 or abs(s) < 1e-15:
            raise ValueError("Given multivector cannot be interpreted as operator")

        rot_pure = rot.grade(0) + bi_e
        trans = rot * rot_pure.inv()
        t_bi = trans.grade(2)
        tb = 2.0 * t_bi.ip(P3.e0_inv) / trans.grade(0)[0]
        tb.show("tb")

        return Motor(
            Rotor(angle=angle, axis=Direction(axis["e1"], axis["e2"], axis["e3"])),
            Translator(
                Direction(tb["e1"], tb["e2"], tb["e3"]),
            ),
        )

    # Could be General rotor or rotor or translator
    if bi_e_mag < 1e-15:
        print("test for translator")
        if abs(s) < 1e-15:
            raise ValueError("Given multivector cannot be interpreted as operator")
        tb = 2.0 * bi.ip(P3.e0_inv) / s
        tb.show("tb")
        return Translator(Direction(tb["e1"], tb["e2"], tb["e3"]))

    tb = bi.ip(P3.e0_inv)
    tb.show("tb")
    if tb.mag < 1e-15:
        return Rotor(angle, axis=Direction(axis["e1"], axis["e2"], axis["e3"]))

    bi_e_inv = bi_e.inv()
    bi_e_inv.show("bi_e_inv")

    t = tb.ip(bi_e_inv)
    t.show("t")

    return GeneralRotor(
        angle=angle,
        axis=Direction(axis["e1"], axis["e2"], axis["e3"]),
        origin=Point(t["e1"], t["e2"], t["e3"]),
    )


rot = p1 * p2
rot_pure = geo.create(Rotor(math.radians(90), Direction(0, 0, 1)))
rot_pure.show("rot_pure")
trans = geo.create(Translator(Direction(1, 2, 3)))
trans.show("trans")
trans2 = 2.0 * trans
trans2.show("trans2")
rot = trans * rot_pure
rot.show("rot")
rot_div = rot / rot[0]
rot_div.show("rot_div")
gr_op = ana_rotor(rot)
print(gr_op)
rot2 = geo.create(gr_op)
rot2.show("rot2")

x = geo.create(Point(2, 2, 3))
x.show("x")
y = rot * x * rot.rev()
y.show("y")
print(geo.which_entity(y))

y2 = rot2 * x * rot2.rev()
y2.show("y2")
print(geo.which_entity(y2))
