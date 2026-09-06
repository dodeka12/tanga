# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Trace the C++ ``FactorizeVersor`` loop for a near-degenerate motor.

Reimplements the loop in Python (grade projection -> blade_factorize -> pick
factor -> peel) including the eps guard that discards numerical-noise grades,
so we can see which stable factors are kept and where noise is dropped.
"""

import math

from pytanga.basis import BasisN3
from pytanga.geometry import Direction, Geometry, Motor, Rotor, Translator


def motor_mv(geo, angle):
    return geo.create(
        Motor(
            Rotor(angle, Direction(0, 0, 1)),
            Translator(Direction(math.sin(angle), math.cos(angle), 0)),
        )
    )


def trace(mv, eps=1e-6, max_iter=12):
    remaining = mv
    factors = []
    for it in range(max_iter):
        grades = [g for g in remaining.grades if g > 0]
        if not grades:
            print(f"  [{it}] no non-scalar grades left -> break (stable factors: {len(factors)})")
            break
        max_grade = max(grades)
        A = remaining.grade(max_grade)
        fMagA = A.mag
        if fMagA <= eps:
            print(f"  [{it}] grades={remaining.grades} max_grade={max_grade} "
                  f"A.mag={fMagA:.3e} <= eps -> DISCARD noise grade, continue")
            remaining = remaining - A
            continue
        vecA = A.blade_factorize()
        print(f"  [{it}] grades={remaining.grades} max_grade={max_grade} "
              f"A.mag={fMagA:.3e} #blade-factors={len(vecA)}")
        wN = None
        for j, a in enumerate(vecA):
            sp_aa = a.sp(a)
            print(f"        factor[{j}] mag={a.mag:.3e}  sp(a,a)={sp_aa:.3e}")
            if wN is None and abs(sp_aa) > 1e-12:
                wN = a
        if wN is None:
            wN = vecA[0]
        fMag = wN.mag
        print(f"        -> picked factor mag={fMag:.3e}")
        wN = wN / fMag
        factors.append(wN)
        remaining = remaining.gp(wN)
        print(f"        after peel: grades={remaining.grades} mag={remaining.mag:.3e}")
    return factors, remaining


if __name__ == "__main__":
    N3 = BasisN3()
    geo = Geometry(N3)
    for angle in (0.0, 1e-6, 1e-5, 1e-4, 0.12):
        print("=" * 72)
        print(f"angle = {angle}")
        mv = motor_mv(geo, angle)
        factors, remaining = trace(mv)
        print(f"RESULT: {len(factors)} stable factor(s)")
