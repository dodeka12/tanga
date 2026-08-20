"""Benchmark: in-place ``RotorFunc`` vs. rebuilding a rotor per call.

Question answered: does mutating a single MV in place (and returning a
reference to it) actually speed up the "fresh rotor per angle" pattern?

Run:  uv run python dev/src/dev_rotorfunc_bench.py
"""

from __future__ import annotations

import math
import sys
import timeit

from pytanga.basis import BasisE3, BasisN3
from pytanga.geometry import Direction, Geometry, Point
from pytanga.geometry.create_e3 import create_rotor as create_rotor_e3
from pytanga.geometry.create_n3 import create_rotor as create_rotor_n3


class RotorFunc:
    """Prototype of the proposed in-place rotor function.

    Builds one MV up front and reuses it on every call, only recomputing
    the scalar/bivector coefficients for the new angle.  Returning the same
    MV reference is the whole point — and its main hazard (see below).
    """

    __slots__ = ("_mv", "_angle_fn", "_blades")

    def __init__(self, basis, axis, angle_fn):
        axis = axis.normalized()
        ax, ay, az = axis.x, axis.y, axis.z
        self._mv = basis.multivector()
        self._angle_fn = angle_fn
        # (blade_id, unit_bivector_coeff) — same sign convention as create_rotor.
        self._blades = (
            (basis._resolve_key("e23"), -ax),
            (basis._resolve_key("e13"), ay),
            (basis._resolve_key("e12"), -az),
        )

    @property
    def mv(self):
        """The reused multivector (updated by the last ``__call__``)."""
        return self._mv

    def __call__(self, value):
        half = self._angle_fn(value) / 2.0
        s = math.sin(half)
        c = math.cos(half)
        self._mv[0] = c
        for bid, coef in self._blades:
            self._mv[bid] = s * coef
        return self._mv


def bench(label: str, fn, number: int) -> float:
    t = timeit.timeit(fn, number=number)
    us = t * 1e6 / number
    print(f"  {label:<46} {us:9.3f} us/call")
    return t


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")

    E3 = BasisE3()
    N3 = BasisN3()
    axis = Direction(0.3, -0.5, 0.8).normalized()
    number = 200_000

    # ── 1. Correctness: in-place rotor must equal create_rotor ──────────────
    print("== correctness (RotorFunc vs. create_rotor) ==")
    for basis, create_rotor in ((E3, create_rotor_e3), (N3, create_rotor_n3)):
        rf = RotorFunc(basis, axis, lambda v: v)
        worst = 0.0
        for ang in (0.0, 0.7, 2.1, -1.3, 5.9):
            a = create_rotor(basis, ang, axis)
            b = rf(ang)
            worst = max(worst, (a - b).mag)
        print(
            f"  {type(basis).__name__:<10} max |create_rotor - RotorFunc| = {worst:.3g}"
        )

    # ── 2. Micro-benchmark: construction cost only ─────────────────────────
    print("\n== construction cost (E3) ==")
    s, c = math.sin(0.35), math.cos(0.35)
    ax, ay, az = axis.x, axis.y, axis.z
    ids = (
        0,
        E3._resolve_key("e23"),
        E3._resolve_key("e13"),
        E3._resolve_key("e12"),
    )
    rf_e3 = RotorFunc(E3, axis, lambda v: v)
    rf_e3(0.7)  # warm up

    def fresh():
        return create_rotor_e3(E3, 0.7, axis)

    def inplace():
        return rf_e3(0.7)

    def alloc_set():
        # isolate the C++ DynMV + MV wrapper allocation: no dict, no re-resolve
        mv = E3.multivector()
        mv._impl.set(ids[0], c)
        mv._impl.set(ids[1], -s * ax)
        mv._impl.set(ids[2], s * ay)
        mv._impl.set(ids[3], -s * az)
        return mv

    t_fresh = bench("create_rotor (dict + alloc + resolve)", fresh, number)
    t_alloc = bench("alloc DynMV + 4 set() (no dict/resolve)", alloc_set, number)
    t_inplace = bench("RotorFunc (in-place reuse)", inplace, number)
    print(f"  -> RotorFunc vs create_rotor: {t_fresh / t_inplace:.2f}x faster")
    print(f"  -> of that, dict+resolve costs  {t_fresh / t_alloc:.2f}x,")
    print(f"     and the DynMV/MV allocation  {t_alloc / t_inplace:.2f}x")

    # ── 3. End-to-end: apply rotor to a CGA point ──────────────────────────
    print("\n== end-to-end: rotate an N3 point (R * p * ~R) ==")
    geo = Geometry(N3)
    p = geo(Point(1.0, 0.0, 0.0))
    rf_n3 = RotorFunc(N3, axis, lambda v: v)
    rf_n3(0.7)

    def apply_fresh():
        R = create_rotor_n3(N3, 0.7, axis)
        return R * p * ~R

    def apply_inplace():
        R = rf_n3(0.7)
        return R * p * ~R

    t_af = bench("fresh rotor + sandwich", apply_fresh, number)
    t_ai = bench("RotorFunc + sandwich", apply_inplace, number)
    print(f"  -> end-to-end speedup: {t_af / t_ai:.2f}x (sandwich dominates)")

    # ── 4. Aliasing hazard: the returned MV is a shared mutable buffer ─────
    print("\n== aliasing hazard ==")
    rf = RotorFunc(E3, axis, lambda v: v)
    r1 = rf(0.5)
    print("  r1 = rf(0.5)      ->", r1.to_dict())
    r2 = rf(1.0)
    print("  r2 = rf(1.0)      ->", r2.to_dict())
    print("  r1 now            ->", r1.to_dict())
    print(f"  r1 is r2 is rf.mv -> {r1 is r2 is rf.mv}")


if __name__ == "__main__":
    main()
