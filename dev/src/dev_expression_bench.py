# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Benchmark: expression evaluation vs. fresh computation.

Builds a fixed-rotor application expression ``E = R * v * ~R`` once (linear in
the variable ``v``), then compares:

1. single evaluation ``E(V1=x)`` vs. the fresh sandwich ``R * x * ~R``,
2. batched evaluation ``E(V1=DataArray(xs, ...))`` vs. a Python loop of fresh
   sandwiches.

Run:  uv run python dev/src/dev_expression_bench.py
"""

import sys
import timeit

from pytanga import BladeMask, DataArray, Variable
from pytanga.basis import BasisE3
from pytanga.geometry import Direction
from pytanga.geometry.create_e3 import create_rotor

sys.stdout.reconfigure(encoding="utf-8")

N_SINGLE = 200_000
N_BATCH = 20_000

alg = BasisE3()
axis = Direction(0, 0, 1)
R = create_rotor(alg, 0.7, axis)  # fixed rotor

mask = BladeMask.full(alg)
v = Variable("V1", mask)
E = R * v * ~R  # build once

x = alg.multivector({1: 1.0, 2: 2.0, 3: 3.0})

# correctness check
diff = (E(V1=x) - (R * x * ~R)).mag
print(f"correctness: |E(x) - R*x*~R| = {diff:.3g}\n")


def fresh():
    return R * x * ~R


def single():
    return E(V1=x)


xs = [
    alg.multivector({1: float(i), 2: float(i + 1), 3: float(i + 2)})
    for i in range(N_BATCH)
]


def fresh_loop():
    return [R * xi * ~R for xi in xs]


def batched():
    return E(V1=DataArray(xs, masks=("n", mask)))


def bench(label, fn, number):
    t = timeit.timeit(fn, number=number)
    print(f"  {label:<36} {t * 1e6 / number:9.3f} us/call")
    return t


print("== single evaluation (apply fixed rotor to one vector) ==")
t_fresh = bench("fresh sandwich R*x*~R", fresh, N_SINGLE)
t_single = bench("expression E(V1=x)", single, N_SINGLE)
print(f"  -> single speedup: {t_fresh / t_single:.2f}x\n")

print(f"== batched evaluation (apply rotor to {N_BATCH} vectors) ==")
t_loop = timeit.timeit(fresh_loop, number=1) * 1000
t_batch = timeit.timeit(batched, number=1) * 1000
print(f"  fresh loop over {N_BATCH} items : {t_loop:9.3f} ms")
print(f"  expression batch                : {t_batch:9.3f} ms")
print(f"  -> batched speedup: {t_loop / t_batch:.2f}x")


# --- repeated variable (quadratic form) ---
Q = v * v


def fresh_quad():
    return x * x


def quad():
    return Q(V1=x)


print("\n== single evaluation (quadratic v*v) ==")
t_fresh_q = bench("fresh product x*x", fresh_quad, N_SINGLE)
t_quad = bench("expression (v*v)(V1=x)", quad, N_SINGLE)
print(f"  -> single speedup: {t_fresh_q / t_quad:.2f}x")


# --- affine sum: v*v + v ---
F = (v * v) + v


def fresh_aff():
    return (x * x) + x


def aff():
    return F(V1=x)


print("\n== single evaluation (affine v*v + v) ==")
t_fresh_aff = bench("fresh (x*x) + x", fresh_aff, N_SINGLE)
t_aff = bench("expression F(V1=x)", aff, N_SINGLE)
print(f"  -> single speedup: {t_fresh_aff / t_aff:.2f}x")
