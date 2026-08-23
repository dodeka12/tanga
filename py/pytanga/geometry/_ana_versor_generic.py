# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Generic versor analysis shared across PGA and N-algebras.

The key trick ``bi.op(einf_like).ip(e0_inv_like)`` projects out null
bivectors, leaving the pure Euclidean bivector.  This works for both:

- PGA:  ``einf_like = e0``,  ``e0_inv_like = e0_inv``
- N:    ``einf_like = einf``, ``e0_inv_like = −eo``

because ``e0 = einf = ep+em`` and ``e0_inv = −eo = 0.5·ep − 0.5·em``.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from .entities import Direction, Point
from .operators import GeneralRotor, Motor, Rotor, Translator, _motor_screw

if TYPE_CHECKING:
    from pytanga.algebra._mv import MV


def ana_versor_generic(
    mv: MV,
    *,
    einf_like: MV,
    e0_inv_like: MV,
    blade_order_sign: int = 1,
    is_2d: bool = False,
) -> Rotor | Translator | Motor | GeneralRotor:
    """Analyze a versor by grade content (PGA2/3, N2/3).

    Parameters
    ----------
    mv : MV
        The versor to analyze.
    einf_like : MV
        The null vector (e₀ in PGA, e∞ in N).
    e0_inv_like : MV
        The inverse/dual of the null vector (e₀⁻¹ in PGA, −eₒ in N).
    blade_order_sign : int
        +1 for PGA (bivector form e0∧t), −1 for N (bivector form t∧einf).
        Applied to translation vector extraction.
    is_2d : bool
        If True, the rotation axis is always (0, 0, 1) (PGA2/N2).
        If False, axis is extracted from the Euclidean bivector (PGA3/N3).
    """
    s = mv.grade(0)
    s_val = float(s[0]) if not s.is_zero else 0.0
    bi = mv.grade(2)
    q = mv.grade(4)

    # Project out null bivector parts → pure Euclidean bivector
    bi_e = bi.op(einf_like).ip(e0_inv_like)
    bi_e_mag = bi_e.mag

    q_mag = q.mag

    # ── Motor (has grade‑4 component) ──
    if q_mag > 1e-15:
        if bi_e_mag < 1e-15:
            raise ValueError("Motor has grade‑4 but no Euclidean bivector")
        cos_a = s_val
        sin_a = bi_e_mag
        angle = 2.0 * math.atan2(sin_a, cos_a)
        axis = _extract_axis(bi_e, is_2d)

        # Factor out pure rotation: trans = V * R⁻¹
        rot_pure = mv.grade(0) + bi_e
        trans = mv.gp(rot_pure.inv())
        t_s = trans.grade(0)
        t_s_val = float(t_s[0]) if not t_s.is_zero else 0.0
        if abs(t_s_val) < 1e-15:
            raise ValueError("Motor translation scalar is zero")
        t_bi = trans.grade(2)
        tv = 2.0 * t_bi.ip(e0_inv_like) / t_s_val * blade_order_sign

        t_dir = Direction(tv["e1"], tv["e2"], tv["e3"])
        gen, trans = _motor_screw(angle, axis, t_dir)
        return Motor(rotor=gen, translator=trans)

    # ── No Euclidean bivector → Translator ──
    if bi_e_mag < 1e-15:
        if abs(s_val) < 1e-15:
            raise ValueError("Zero scalar — not a valid versor")
        tv = 2.0 * bi.ip(e0_inv_like) / s_val * blade_order_sign
        return Translator(Direction(tv["e1"], tv["e2"], tv["e3"]))

    # ── Angle + axis (shared by Rotor & GeneralRotor) ──
    cos_a = s_val
    sin_a = bi_e_mag
    angle = 2.0 * math.atan2(sin_a, cos_a)
    axis = _extract_axis(bi_e, is_2d)

    # ── Pure Rotor vs GeneralRotor ──
    tb = bi.ip(e0_inv_like)  # null bivector part
    if tb.mag < 1e-15:
        return Rotor(angle=angle, axis=axis)

    # GeneralRotor: rotation origin = tb · bi_e⁻¹
    t = tb.ip(bi_e.inv()) * blade_order_sign
    return GeneralRotor(
        angle=angle,
        axis=axis,
        origin=Point(t["e1"], t["e2"], t["e3"]),
    )


def _extract_axis(bi_e: MV, is_2d: bool) -> Direction:
    """Extract rotation axis from the Euclidean bivector."""
    if is_2d:
        return Direction(0, 0, 1)
    axis_mv = bi_e.ip(bi_e._alg.multivector({7: 1.0}))  # e₁₂₃
    axis = Direction(axis_mv["e1"], axis_mv["e2"], axis_mv["e3"])
    return axis.normalized()
