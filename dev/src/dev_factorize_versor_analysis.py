# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""Diagnostic: exercise FactorizeVersor (blade_factorize_versor) across versor types.

Reports, for each versor:
  - input grades,
  - returned factor count and per-factor grades,
  - reconstruction error (scale * prod(reversed factors)) vs original,
  - any exception raised.

Run:  uv run python dev/src/dev_factorize_versor_analysis.py
"""

from __future__ import annotations

import math
import sys

from pytanga.basis import BasisE3, BasisN3

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def reconstruct(scale, factors):
    """Reverse the extraction order used by FactorizeVersor (right-to-left)."""
    r = scale
    for f in reversed(factors):
        r = r * f
    return r


def analyze(name, mv):
    print(f"\n=== {name} ===")
    print(f"  grades      = {mv.grades}")
    try:
        scale, factors = mv.blade_factorize_versor()
    except Exception as ex:  # noqa: BLE001 - diagnostic
        print(f"  RESULT      : EXCEPTION -> {type(ex).__name__}: {ex}")
        return

    print(f"  scale       = {scale}")
    print(f"  #factors    = {len(factors)}")
    for i, f in enumerate(factors):
        print(f"    factor[{i}] grades={f.grades}  mag2={f.mag2:.6f}  {f}")
    try:
        recon = reconstruct(scale, factors)
        diff = recon - mv
        print(f"  recon error = {diff.mag:.3e}")
    except Exception as ex:  # noqa: BLE001 - diagnostic
        print(f"  recon       : EXCEPTION -> {type(ex).__name__}: {ex}")


def main() -> None:
    # ------------------------------------------------------------------
    # E3
    # ------------------------------------------------------------------
    e3 = BasisE3()
    e1, e2, e3v = e3.e1, e3.e2, e3.e3

    analyze("E3 bivector versor  e1*e2", e1 * e2)

    a = 0.7
    rotor_e3 = math.cos(a / 2) + math.sin(a / 2) * (e1 ^ e2)
    analyze("E3 rotor  cos+sin*(e1^e2)", rotor_e3)

    # ------------------------------------------------------------------
    # N3
    # ------------------------------------------------------------------
    n3 = BasisN3()
    n1, n2, n3v = n3.e1, n3.e2, n3.e3
    einf, eo = n3.einf, n3.eo

    b = n1 ^ n2  # Euclidean bivector, unit
    rotor_n3 = math.cos(a / 2) + math.sin(a / 2) * b
    analyze("N3 rotor  cos+sin*(e1^e2)", rotor_n3)

    t = 0.5 * n1 + 0.3 * n2 + 0.1 * n3v
    translator = n3.multivector({0: 1.0}) - 0.5 * (t ^ einf)
    analyze("N3 translator  1 - 0.5*t^einf", translator)

    motor = translator * rotor_n3
    analyze("N3 motor  T*R", motor)

    general_rotor = translator * rotor_n3 * translator.rev()
    analyze("N3 general rotor  T*R*T~", general_rotor)

    # Versor whose max-grade blade is a pure null bivector (t^einf only).
    null_bivec_versor = n3.multivector({0: 1.0}) + (t ^ einf)
    analyze("N3  1 + t^einf  (null bivector part)", null_bivec_versor)

    # Rotor in a *degenerate* metric directly: a null Euclidean-like vector.
    # einf is null; build versor 1 + einf (a single null reflector).
    analyze("N3  1 + einf  (null vector part)", n3.multivector({0: 1.0}) + einf)

    # Pure-grade blade input (reflection family): a grade-2 blade.
    analyze("N3  pure bivector e1^e2", b)

    # ------------------------------------------------------------------
    # G(5,0) random versor (mirrors the C++/pytest case)
    # ------------------------------------------------------------------
    import numpy as np
    import pytanga

    alg = pytanga.Algebra(5, 0)
    rng = np.random.default_rng(42)
    versor5 = alg.multivector({0: 1.0})
    for _ in range(4):
        vec = alg()
        for bit in range(5):
            val = rng.uniform(-2.0, 2.0)
            if abs(val) > 1e-12:
                vec[1 << bit] = val
        versor5 = versor5 * vec
    analyze("G(5,0) random 4-factor versor", versor5)


if __name__ == "__main__":
    main()
