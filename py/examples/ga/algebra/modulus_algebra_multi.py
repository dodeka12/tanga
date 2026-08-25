# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""
modulus_algebra_multi.py — Integer GA with two different moduli (NTRU style).

When the same multivector algebra is used under two different moduli
simultaneously — as in the NTRU-style geometric-algebra cryptosystem in
``cpp/Tan.Crypt.Test/Test_Crypt_03.cpp`` — a single modulus stored on the
Algebra does not work because the same MV objects are operated on under
*both* moduli at different points in the algorithm.

The solution is to create **one** Algebra instance (no modulus) and use the
explicit-modulus methods on MV:

  mv.gp_mod(other, p)   geometric product, then hmod(·, p)
  mv.op_mod(other, p)   outer product, then hmod(·, p)
  mv.ip_mod(other, p)   inner product, then hmod(·, p)
  mv.inv(p)             modular inverse under prime p
  mv.reduce(p)          standalone hmod(·, p) applied coefficient-wise

This maps directly to the C++ pattern:
  GA::GP_Congruence(result, a, b, xModP)  →  a.gp_mod(b, P)
  GA::Congruence(result, xModP)           →  result.reduce(P)
  GA::Inverse(result, a, xModP)           →  a.inv(P)

Run with:
    uv run python py/examples/ga/algebra/modulus_algebra_multi.py
"""

import random

import pytanga
from pytanga import MV


def hr(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: next prime above n (simple sieve for small values)
# ─────────────────────────────────────────────────────────────────────────────
def next_prime(n: int) -> int:
    def is_prime(k: int) -> bool:
        if k < 2:
            return False
        for i in range(2, int(k**0.5) + 1):
            if k % i == 0:
                return False
        return True

    k = n + 1
    while not is_prime(k):
        k += 1
    return k


# ─────────────────────────────────────────────────────────────────────────────
# Setup — G(5, 0) over int64, NO modulus stored on the algebra.
#
# Two moduli are chosen following the sizing in Test_Crypt_03.cpp:
#   half_range = 1  →  modA = next_prime(2*half_range+1) = 5
#   modB = next_prime(modA * half_range^2 * algebra_dim)
# For the demo we use a smaller algebra (G(3,0), dim=8) to keep outputs short.
# ─────────────────────────────────────────────────────────────────────────────

# G(3,0) has algebra dimension 2^3 = 8
alg = pytanga.Algebra(3, 0, dtype="int64")  # no modulus on algebra
ALG_DIM = alg.algebra_dim  # 8

HALF_RANGE = 1
MODA = next_prime(2 * HALF_RANGE + 1)  # = 5
MODB = next_prime(MODA * HALF_RANGE**2 * ALG_DIM)  # = next_prime(40) = 41

print("\nalgebra   : G(3, 0),  dtype = int64,  no algebra-level modulus")
print(f"algebra_dim = {ALG_DIM}")
print(f"MODA = {MODA},  MODB = {MODB}")
print(f"MODA < MODB : {MODA < MODB}  (required by NTRU construction)")


# ─────────────────────────────────────────────────────────────────────────────
# 1. Explicit per-call modulus — basic demonstration
# ─────────────────────────────────────────────────────────────────────────────
hr("1. Explicit per-call modulus")

a = alg("3 e1 + 2 e2")
b = alg("e1 + 4 e12")

print("\nSame GP, two different moduli:")
a.show("a")
b.show("b")
a.gp_mod(b, MODA).show(f"a.gp_mod(b, MODA={MODA})")
a.gp_mod(b, MODB).show(f"a.gp_mod(b, MODB={MODB})")

print("\nStandalone reduce — same result, different moduli:")
raw = a * b  # raw integer GP, no modulus
raw.show("a * b  (raw)")
raw.reduce(MODA).show(f"(a*b).reduce(MODA={MODA})")
raw.reduce(MODB).show(f"(a*b).reduce(MODB={MODB})")

print("\nSame MV object inverted under each modulus independently:")
f = alg("2 e1 - 3 e2 + e3 + e12")
f.show("f")
f_inv_A = f.inv(MODA)
f_inv_B = f.inv(MODB)
f_inv_A.show(f"f.inv(MODA={MODA})")
f_inv_B.show(f"f.inv(MODB={MODB})")

check_A = f.gp_mod(f_inv_A, MODA)
check_B = f.gp_mod(f_inv_B, MODB)
check_A.show("f * f.inv(MODA) mod MODA  (scalar should be 1)")
check_B.show("f * f.inv(MODB) mod MODB  (scalar should be 1)")
assert check_A["s"] == 1 and check_B["s"] == 1
print("  ✓  both inverses verified")


# ─────────────────────────────────────────────────────────────────────────────
# 2. NTRU-style encode / decode
#
# Follows the structure of Test_Crypt_03.cpp:
#
#   Alice's secret key : f  (invertible under both moduli)
#   Public key         : h = f_inv_B * g  mod MODB
#   Bob encodes        : c = h * (MODA * L) + M  mod MODB
#   Alice decodes
#     step 1           : S1 = f * c  mod MODB
#     step 2           : M' = f_inv_A * S1  mod MODA
#   Check              : M' == M
# ─────────────────────────────────────────────────────────────────────────────
hr("2. NTRU-style encode / decode")

rng = random.Random(42)


def rand_mv() -> MV:
    """Random MV with coefficients in [-HALF_RANGE, HALF_RANGE]."""
    return alg(
        {
            blade_id: rng.randint(-HALF_RANGE, HALF_RANGE)
            for blade_id in alg.all_blades()
        }
    )


# Alice chooses f invertible under both moduli
for _ in range(20):
    f = rand_mv()
    try:
        f_inv_A = f.inv(MODA)
        f_inv_B = f.inv(MODB)
        break
    except RuntimeError:
        continue
else:
    raise RuntimeError("Could not find invertible f in 20 tries")

# Public key
g = rand_mv()
h = f_inv_B.gp_mod(g, MODB)  # h = f⁻¹_B * g  mod MODB

print("\nAlice's secret key f:")
f.show("  f")
print("\nPublic key h = f_inv_B * g  mod MODB:")
h.show("  h")

# Bob encodes message M
L = rand_mv()
M = rand_mv()
print("\nPlaintext message M:")
M.show("  M")

# c = h * (MODA * L) + M  mod MODB
#   — mirrors: wQb = wFib_G_aL + wM; GA::Congruence(wQb, xModB)
c = (h * (MODA * L) + M).reduce(MODB)
print("\nEncoded ciphertext c:")
c.show("  c")

# Alice decodes
S1 = f.gp_mod(c, MODB)  # step 1: f * c  mod MODB
M_decoded = f_inv_A.gp_mod(S1, MODA)  # step 2: f⁻¹_A * S1  mod MODA

print("\nDecoded message M':")
M_decoded.show("  M'")

# Verify M == M' (both reduced mod MODA for fair comparison)
M_A = M.reduce(MODA)
diff = M_A - M_decoded
diff.show("  M_reduced - M'  (should be 0)")
assert all(v == 0 for v in diff.to_dict().values()), "Decryption mismatch!"
print("  ✓  decryption successful: M' == M  (mod MODA)")
