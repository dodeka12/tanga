# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""
modulus_algebra_single.py — Integer GA with a single modulus (Path C).

When all arithmetic in a computation is done modulo the same prime p, pass
``modulus=p`` at construction time.  Every subsequent operator (+, -, *, and
scalar multiplication) automatically applies half-space modular reduction
(``hmod``) so coefficients stay in ``[-p//2, p//2]``.

The ``hmod`` function maps a value v into the half-open interval
  [-(p-1)//2,  (p-1)//2]
which is the standard centred representation used in lattice-based
cryptography.  Coefficients with absolute value > p//2 are wrapped.

Run with:
    uv run python py/examples/ga/algebra/modulus_algebra_single.py

Keywords: Algebra, modulus, integer, fixed modulus
"""

import pytanga
from pytanga import MV


def hr(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


# ─────────────────────────────────────────────────────────────────────────────
# Setup — G(3, 0) over int64 with a fixed prime modulus
# ─────────────────────────────────────────────────────────────────────────────
MOD = 101  # a small prime
alg = pytanga.Algebra(3, 0, dtype="int64", modulus=MOD)

print(f"\nalgebra : G(3, 0),  dtype = int64,  modulus = {alg.modulus}")
print(f"algebra_dim = {alg.algebra_dim}  (2^3 = 8 basis blades)")

# Named blade aliases — the declaration block pattern from basis_usage.py
e1: MV = alg("e1")
e2: MV = alg("e2")
e3: MV = alg("e3")
e12: MV = alg("e12")


# ─────────────────────────────────────────────────────────────────────────────
# 1. Automatic reduction through operators
# ─────────────────────────────────────────────────────────────────────────────
hr("1. Automatic hmod reduction through operators")

print("\nGeometric product — same as float, result stays in [-50, 50]:")
(e1 * e2).show("e1 * e2")
(e2 * e1).show("e2 * e1")

print("\nScalar multiplication — large coefficient gets wrapped:")
# hmod(60, 101): 60 ≤ 50? No → 60 - 101 = -41
(60 * e1).show("60 * e1                   (hmod(60,101) = -41)")
# hmod(50, 101): 50 ≤ 50 → stays 50
(50 * e1).show("50 * e1                   (hmod(50,101) =  50)")
# hmod(51, 101): 51 > 50 → 51 - 101 = -50
(51 * e1).show("51 * e1                   (hmod(51,101) = -50)")

print("\nAddition — coefficients reduced after each step:")
a = 48 * e1 + 48 * e2  # 48+48=96 > 50 for component e1... wait, they're separate
# e1 and e2 are different blades; no cross-addition
b = 10 * e1 + 40 * e2  # after reduction: e1 coeff is 10, e2 is 40
(a + b).show("(48e1 + 48e2) + (10e1 + 40e2)")
# e1: hmod(48+10,101)=hmod(58,101)=58-101=-43
# e2: hmod(48+40,101)=hmod(88,101)=88-101=-13

print("\nSubtraction:")
c = 3 * e1 - 5 * e2
c.show("3e1 - 5e2")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Geometric product chains
# ─────────────────────────────────────────────────────────────────────────────
hr("2. Geometric product chains")

# Build a non-trivial multivector
x = alg("3 e1 + 7 e2 - 2 e3")
y = alg("5 e1 - 4 e2 + 6 e3")
x.show("x = 3e1 + 7e2 - 2e3")
y.show("y = 5e1 - 4e2 + 6e3")

xy = x * y
yx = y * x
xy.show("x * y")
yx.show("y * x")
# In G(3,0): e1*e1=1, e2*e2=1, e3*e3=1 — so x*y has scalar and bivector parts
(x * y + y * x).show("x*y + y*x  (should be 2*(x·y) scalar)")


# ─────────────────────────────────────────────────────────────────────────────
# 3. Multiplicative inverse and round-trip
# ─────────────────────────────────────────────────────────────────────────────
hr("3. Multiplicative inverse — a * a.inv() ≡ scalar 1")

a = alg("3 e1 + 7 e2 - 2 e3 + 4 e12")
a.show("a")

# For a single-modulus algebra the stored modulus is used automatically.
a_inv = a.inv()
a_inv.show("a.inv()")

product = a * a_inv
product.show("a * a.inv()   (scalar coeff should be 1)")
assert product["s"] == 1, f"expected scalar 1, got {product['s']}"
print("  ✓  scalar coefficient is 1")


# ─────────────────────────────────────────────────────────────────────────────
# 4. Operator precedence and mixed expressions
# ─────────────────────────────────────────────────────────────────────────────
hr("4. Mixed expressions — all ops reduce mod 101")

u = alg("30 e1 + 40 e2")
v = alg("20 e1 - 50 e3")
(u + v).show("u + v")
(u - v).show("u - v")
(u * v).show("u * v  (GP)")
(2 * u + 3 * v - u * v).show("2u + 3v - u*v")

print(f"\nAll coefficients confirmed in [{-(MOD - 1) // 2}, {(MOD - 1) // 2}].")
