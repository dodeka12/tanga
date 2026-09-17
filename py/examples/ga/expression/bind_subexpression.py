#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

r"""bind_subexpression.py — Bind a variable to a sub-expression (composition).

Build a placement-independent local expression ``v_b ^ (v_b | B)`` once (``v_b``
appears twice), then derive its world-frame form by binding ``v_b`` to the
sandwich ``R * V * ~R`` — an ``Expression``, not a plain ``MV``.  Shows that
``Expression.bind`` accepts a sub-expression whose output mask matches the bound
variable's mask, and that a repeated variable is substituted consistently (its
free variable stays one shared block, so both occurrences use the same value).

Run with:  uv run python py/examples/ga/expression/bind_subexpression.py

Keywords: expressions, bind, composition, sub-expression, rotor
"""

from typing import cast

from pytanga import BladeMask, MV, Variable
from pytanga.basis import BasisE3
from pytanga.geometry import Direction
from pytanga.geometry.create_e3 import create_rotor


def main() -> None:
    alg = BasisE3()
    full = BladeMask.full(alg)

    # A fixed rotor (scalar + bivector); ~R is its reverse/inverse.
    R = create_rotor(alg, 0.5, Direction(1, 0, 0))

    # Local/body-frame expression built once; v_b appears twice.
    v_b = Variable("v_b", full)
    B = alg.multivector({"e12": 1.0})
    local = v_b ^ (v_b | B)

    # World-frame symbol and the world->local sandwich (an Expression).
    V = Variable("V", full)
    sandwich = R * V * ~R

    # Compose: replace v_b with the sandwich sub-expression.
    world = local.bind(v_b=sandwich)

    print("local variable names:", local.names)
    print("world variable names:", world.names)
    print("occurrences of V in world:", len(world.names["V"]))

    w = alg.multivector({"e1": 1.0, "e2": 2.0, "e3": 0.5})
    expected = (R * w * ~R) ^ ((R * w * ~R) | B)
    result = cast(MV, world(V=w))
    print("world(V=w)  =", result)
    print("expected    =", expected)
    print("match:", (result - expected).mag < 1e-12)


if __name__ == "__main__":
    main()
