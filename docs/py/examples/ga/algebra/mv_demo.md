# The MV class: initialization, operators, and named methods

**Keywords:** MV · multivector · operators · coefficients · initialization

This script is a reference for everything you can do with an MV object once
you have an Algebra.  It covers:

  1. Initialization — four ways to create a multivector
  2. Coefficient access — reading and writing individual blades
  3. Unary operators  — negation (-), inverse (~)
  4. Binary operators — GP (*), outer (^), inner (|), add (+), sub (-), div (MV/MV, scalar/MV, MV/scalar)
  5. Mixed scalar/MV arithmetic — scalar on either side
  6. Named methods    — .gp(), .op(), .ip(), .inv(), .show()
  7. Utility          — .to_dict(), .prune(), repr()
  8. Reverse & versor product — .rev(), .vp(), .nvp()

The algebra used throughout is G(3, 0) over float64.

## Run

```bash
uv run python py/examples/ga/algebra/mv_demo.py
```

## Source

[`ga/algebra/mv_demo.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/ga/algebra/mv_demo.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""
mv_demo.py — The MV class: initialization, operators, and named methods.

This script is a reference for everything you can do with an MV object once
you have an Algebra.  It covers:

  1. Initialization — four ways to create a multivector
  2. Coefficient access — reading and writing individual blades
  3. Unary operators  — negation (-), inverse (~)
  4. Binary operators — GP (*), outer (^), inner (|), add (+), sub (-), div (MV/MV, scalar/MV, MV/scalar)
  5. Mixed scalar/MV arithmetic — scalar on either side
  6. Named methods    — .gp(), .op(), .ip(), .inv(), .show()
  7. Utility          — .to_dict(), .prune(), repr()
  8. Reverse & versor product — .rev(), .vp(), .nvp()

The algebra used throughout is G(3, 0) over float64.

Run with:
    uv run python py/examples/ga/algebra/mv_demo.py

Keywords: MV, multivector, operators, coefficients, initialization
"""

import pytanga
from pytanga import MV


def hr(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


alg = pytanga.Algebra(3, 0)  # G(3, 0), float64


# ─────────────────────────────────────────────────────────────────────────────
# 1. Initialization
# ─────────────────────────────────────────────────────────────────────────────
hr("1. Initialization")

# 1a. String expression — most readable for hand-written values
a: MV = alg("1 + 2 e1 - 3 e2 + 4 e12")
a.show("string  '1 + 2 e1 - 3 e2 + 4 e12'")

# 1b. Dict with string blade names
b: MV = alg({"e1": 2.0, "e2": -3.0, "e12": 4.0, "s": 1.0})
b.show("str-key {'e1':2, 'e2':-3, 'e12':4, 's':1}")

# 1c. Dict with tuple index keys — 1-based; (0,) or () for the scalar
c: MV = alg({(0,): 1.0, (1,): 2.0, (2,): -3.0, (1, 2): 4.0})
c.show("tuple   {(0,):1, (1,):2, (2,):-3, (1,2):4}")

# 1d. Dict with raw blade bitmasks (bit k = basis vector e_{k+1})
#     0=scalar, 1=e1, 2=e2, 3=e12, 4=e3, …
d: MV = alg({0: 1.0, 1: 2.0, 2: -3.0, 3: 4.0})
d.show("bitmask {0:1, 1:2, 2:-3, 3:4}")

# All four produce the same multivector:
assert a.to_dict() == b.to_dict() == c.to_dict() == d.to_dict()
print("  ✓  all four forms produce identical multivectors")

# Zero multivector
z: MV = alg()
z.show("zero multivector (no coeffs)")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Coefficient access
# ─────────────────────────────────────────────────────────────────────────────
hr("2. Coefficient access")

mv: MV = alg("3 e1 + 5 e12")
print(f"  mv['e1']  = {mv['e1']}")  # by blade name
print(f"  mv['e12'] = {mv['e12']}")
print(f"  mv['e2']  = {mv['e2']}")  # absent blade → 0
print(f"  mv['s']   = {mv['s']}")  # scalar part

# Write a coefficient
mv["e2"] = -7.0
mv.show("after mv['e2'] = -7")

# Bitmask key also works
print(f"  mv[2]  (bitmask for e2) = {mv[2]}")


# ─────────────────────────────────────────────────────────────────────────────
# 3. Unary operators
# ─────────────────────────────────────────────────────────────────────────────
hr("3. Unary operators")

e1: MV = alg("e1")
e2: MV = alg("e2")
e3: MV = alg("e3")

x: MV = alg("3 e1 + 2 e2")
x.show("x")

(-x).show("-x  (unary negation)")

# ~ is the reverse  (same as x.rev())
xi: MV = ~x
xi.show("~x  (reverse)")
(x * xi).show("x * ~x  (should be mag2 of x)")


# ─────────────────────────────────────────────────────────────────────────────
# 4. Binary MV operators
# ─────────────────────────────────────────────────────────────────────────────
hr("4. Binary MV operators")

u: MV = alg("e1 + 2 e2")
v: MV = alg("e2 + e3")

print("\nGeometric product  u * v  (GP):")
(u * v).show("u * v")

print("\nOuter product  u ^ v  (wedge):")
(u ^ v).show("u ^ v")

print("\nInner product  u | v  (symmetric):")
(u | v).show("u | v")

print("\nAddition  u + v:")
(u + v).show("u + v")

print("\nSubtraction  u - v:")
(u - v).show("u - v")

print("\nDivision by scalar  u / 2:")
(u / 2).show("u / 2")

print("\nDivision by MV  u / v  (= u * v.inv()):")
(u / v).show("u / v")
(u / v * v).show("(u / v) * v  (should equal u)")

print("\nScalar divided by MV  3 / u  (= 3 * u.inv()):")
(3 / u).show("3 / u")
(3 / u * u).show("(3 / u) * u  (should be scalar 3)")

print("\nGP is non-commutative (outer is also non-commutative in general):")
(u * v).show("u * v")
(v * u).show("v * u")
(u * v + v * u).show("u*v + v*u  (= 2*(u·v) for grade-1)")


# ─────────────────────────────────────────────────────────────────────────────
# 5. Mixed scalar / MV arithmetic
# ─────────────────────────────────────────────────────────────────────────────
hr("5. Mixed scalar / MV arithmetic")

mv = alg("e1 + e2")
mv.show("mv = e1 + e2")

(3 * mv).show("3 * mv")  # __rmul__
(mv * 3).show("mv * 3")  # __mul__  (scalar)
(mv / 4).show("mv / 4")  # __truediv__
(mv + 1).show("mv + 1")  # __add__  (scalar → scalar blade)
(1 + mv).show("1 + mv")  # __radd__
(mv - 1).show("mv - 1")  # __sub__
(1 - mv).show("1 - mv")  # __rsub__


# ─────────────────────────────────────────────────────────────────────────────
# 6. Named methods
# ─────────────────────────────────────────────────────────────────────────────
hr("6. Named methods")

p: MV = alg("e1 + e2 + e3")
q: MV = alg("e1 - e2")

print("\n.gp(other)  — geometric product (same as p * q):")
p.gp(q).show("p.gp(q)")

print("\n.op(other)  — outer product (same as p ^ q):")
p.op(q).show("p.op(q)")

print("\n.ip(other)  — inner product (same as p | q):")
p.ip(q).show("p.ip(q)")

print("\n.inv()      — multiplicative inverse (same as ~p):")
p.inv().show("p.inv()")
(p * p.inv()).show("p * p.inv()  (should be scalar 1)")

print("\n.show(label, fmt) — formatted display (fmt controls coefficient notation):")
a.show("a  (default fmt '.4g')")
a.show("a  (fmt='.2f')", fmt=".2f")


# ─────────────────────────────────────────────────────────────────────────────
# 7. Utility
# ─────────────────────────────────────────────────────────────────────────────
hr("7. Utility")

mv = alg("2 e1 + 0 e2 + 3 e12")
print(f"\n  repr(mv)   = {mv!r}")
print(f"  to_dict()  = {mv.to_dict()}")

# prune() removes blades whose coefficient is exactly 0 (as stored)
mv2 = alg({1: 1.0, 2: 0.0, 3: 5.0})
print(f"\n  before prune: repr = {mv2!r}")
mv2.prune()
print(f"  after  prune: repr = {mv2!r}  (zero blade removed)")

# ─────────────────────────────────────────────────────────────────────────────
# 8. Reverse & versor product
# ─────────────────────────────────────────────────────────────────────────────
hr("8. Reverse & versor product")

# rev() flips the sign of grade-k blades where k*(k-1)/2 is odd (grades 2,3 mod 4)
rotor = alg("e12 + e23")
print("\n  .rev() — reverse:")
rotor.show("  r       = e12 + e23")
rotor.rev().show("  r.rev() =")

# For a pure blade the reverse simply flips the sign for grade >= 2
e12 = alg("e12")
e12.rev().show("  (e12).rev()")

# vp(b) — versor product: self * b * self.rev()
# A unit vector acts as a reflection versor.
# Reflecting e1 in the plane whose normal is e2:
#   e2.vp(e1) = e2 * e1 * e2.rev() = e2 * e1 * e2 = -e1   (anti-commuting)
e1 = alg("e1")
e2 = alg("e2")
e3 = alg("e3")
print("\n  .vp() — versor product r.vp(a) = r * a * r.rev():")
e2.vp(e1).show("  e2.vp(e1)  (reflect e1 in normal e2, expect -e1)")
e3.vp(e1).show("  e3.vp(e1)  (reflect e1 in normal e3, expect -e1)")
e1.vp(e1).show("  e1.vp(e1)  (self-reflection, expect +e1)")

# nvp(b) — normalized versor product: self * b * inverse(self)
# For unit vectors inv(v) == rev(v) so vp and nvp agree.
# For a scaled vector (2*e2) the difference is clear:
#   vp  gives a magnitude-dependent result: (2 e2)*e1*(2 e2) = -4 e1
#   nvp normalizes by the true inverse:       (2 e2)*e1*(0.5 e2) = -e1
v = alg("2 e2")
print("\n  .nvp() — normalized versor product r.nvp(a) = r * a * r.inv():")
v.vp(e1).show("  (2 e2).vp(e1)   (expect -4 e1)")
v.nvp(e1).show("  (2 e2).nvp(e1)  (expect  -e1, magnitude-independent)")
````
