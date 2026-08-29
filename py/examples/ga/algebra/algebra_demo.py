# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""
algebra_demo.py — Creating and configuring an Algebra.

The Algebra class is the entry point for all of pytanga.  It represents a
geometric algebra G(dim, sig) — a vector space of dimension *dim* equipped
with a quadratic form whose signature is described by *sig*.

This script covers:

  1. Concept           — what G(dim, sig) means
  2. Dimension         — blade count, practical vs theoretical limits
  3. Signature         — bitmask form and tuple form
  4. Data type         — float32, float64, int32, int64
   5. Modulus           — integer algebras (brief, with references)
   6. Properties        — what you can inspect on an Algebra instance

Run with:
    uv run python py/examples/ga/algebra/algebra_demo.py

Keywords: Algebra, dimension, signature, dtype, modulus, basis
"""

from pytanga.algebra import Algebra


def hr(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Concept
# ─────────────────────────────────────────────────────────────────────────────
hr("1. Concept — G(dim, sig)")

print("""
A geometric algebra G(dim, sig) is built over a real vector space of
dimension *dim*.  Each basis vector e_k squares to +1 or -1; the set of
basis vectors that square to -1 is called the *negative* part of the
signature.

  G(3, 0)  — 3D Euclidean space; all basis vectors square to +1.
  G(4, 1)  — Spacetime-like; one basis vector squares to -1.

From the *dim* basis vectors, all their products (called *blades*) form
the full algebra.  The total number of basis blades is 2**dim:

  dim = 3  →  8 blades:  s, e1, e2, e3, e12, e13, e23, e123

The Algebra class wraps a compiled C++ extension that does the actual
arithmetic.  The first time you instantiate an algebra for a new
(dim, sig, dtype) the C++ code is compiled and cached; after that the
compiled binary is loaded in milliseconds.
""")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Dimension
# ─────────────────────────────────────────────────────────────────────────────
hr("2. Dimension")

print("""
THEORETICAL MAXIMUM: dim = 31
  The C++ template uses an 'unsigned int' (32-bit) as the blade bitmask.
  AlgebraDimension = 1u << dim, so dim = 32 would overflow.  dim = 31 is
  the highest safe value (2^31 = 2 147 483 648 possible basis blades).

HOW PYTANGA AVOIDS EXPONENTIAL BLOW-UP:
  There is no precomputed multiplication table.  Every blade-blade product
  is computed on the fly from the two blade bitmasks using cheap bit ops:

    result blade  =  bitmask_A XOR bitmask_B
    swap sign     =  popcount(shift-mask of bitmask_A with bitmask_B) & 1
    metric sign   =  popcount(signature & bitmask_A & bitmask_B) & 1

  This is O(dim) per blade-blade pair — not O(2^dim).

  Multivectors are SPARSE: CDynamicMultivector only stores non-zero blades
  in a dictionary keyed by bitmask.  A G(16, 0) bivector with two active
  blades occupies the same memory as a G(3, 0) bivector with two active
  blades.

COMPILE TIME:
  The compiled binding has the same structure for every dim value — it is
  the same template instantiated once.  The inner loop in GPSign runs
  dim-1 iterations, which changes nothing meaningful for the compiler.
  Compile time is ~5–20 s for ANY dim; it is dominated by CMake startup
  and template instantiation overhead, not by dimension.

PRACTICAL CONSIDERATIONS:
  The only real constraint for large dim is memory when you deliberately
  create DENSE multivectors (all 2^dim blades non-zero):

    dim =  3  →       8 blades   fine for any dtype
    dim =  4  →      16 blades   fine for any dtype
    dim =  5  →      32 blades   fine for any dtype
    dim = 10  →    1024 blades   still manageable
    dim = 16  →   65536 blades   large if dense, trivial if sparse
    dim = 20  → 1048576 blades   only feasible as sparse multivectors

  For the cryptographic use-cases pytanga targets, multivectors are
  typically grade-1 or grade-2 (vectors and bivectors), which have at
  most dim or dim*(dim-1)/2 non-zero blades regardless of total dim.
""")

for dim in (2, 3, 4, 5):
    print(f"  dim = {dim}  →  {2**dim:5d} blades")


# ─────────────────────────────────────────────────────────────────────────────
# 3. Signature
# ─────────────────────────────────────────────────────────────────────────────
hr("3. Signature — two ways to specify it")

print("""
The signature tells pytanga which basis vectors square to -1.
There are two equivalent ways to pass it:

  (a) BITMASK — an integer where bit k=1 means e_{k+1} squares to -1.
      The k-th bit (0-based) corresponds to e_{k+1}.

        sig = 0          → all positive  (Euclidean)
        sig = 0b0100     → bit 2 set  →  e3 squares to -1
        sig = 0b1000     → bit 3 set  →  e4 squares to -1

  (b) TUPLE — a tuple of 0-based indices of basis vectors that square to -1.

        sig = ()         → all positive  (same as sig=0)
        sig = (3,)       → e3 squares to -1  (same as sig=0b0100)
        sig = (1, 4, 5)  → e1, e4, e5 square to -1  (same as sig=0b11001)

Both forms produce identical algebras.  The tuple form is often more
readable; the bitmask form matches the C++ template parameter directly.
""")

# Demonstrate that bitmask and tuple give the same algebra
alg_bitmask = Algebra(5, 0b11001)  # e1, e4, e5 square to -1
alg_tuple = Algebra(5, (1, 4, 5))  # same, written as a tuple

assert alg_bitmask._sig == alg_tuple._sig, "signatures should match"
print(f"  Algebra(5, 0b11001)._sig  = {alg_bitmask._sig:#07b}")
print(f"  Algebra(5, (1,4,5))._sig  = {alg_tuple._sig:#07b}  (identical)")

# Common signature examples
print("""
  Common signatures:

    Algebra(3)            G(3, 0)   Euclidean 3D       — all e_k² = +1
    Algebra(3, (3,))      G(3,…)    e3² = -1
    Algebra(4, (4,))      G(4,…)    PGA3-style, e4² = -1
    Algebra(4, (2,3,4))   G(4,…)    STA-like, e2,e3,e4 square to -1
    Algebra(5, (5,))      G(5,…)    CGA3-style, e5² = -1
""")

# Quadratic-form check: e_k * e_k should equal +1 or -1
alg = Algebra(4, (4,))  # e4² = -1
e4 = alg("e4")
sq = e4 * e4
print("  In Algebra(4, (4,)):  e4 * e4 = ", end="")
sq.show()  # expect -1 scalar

alg2 = Algebra(4)  # all positive
e4p = alg2("e4")
sq2 = e4p * e4p
print("  In Algebra(4, 0):     e4 * e4 = ", end="")
sq2.show()  # expect +1 scalar


# ─────────────────────────────────────────────────────────────────────────────
# 4. Data type
# ─────────────────────────────────────────────────────────────────────────────
hr("4. Data type (dtype)")

print("""
The dtype parameter controls the C++ value type used for all blade
coefficients.  It must be one of:

    dtype='float32'  →  C float    (32-bit IEEE 754)
    dtype='float64'  →  C double   (64-bit IEEE 754)   ← default
    dtype='int32'    →  C int32_t  (signed 32-bit integer)
    dtype='int64'    →  C int64_t  (signed 64-bit integer)

Float algebras support all standard GA operations including the
inverse (~) and the versor product.

Integer algebras are designed for modular arithmetic (see section 5).
They support the same operations but results are exact integers and may
grow unboundedly without a modulus.  The inverse requires a modulus.

Each (dim, sig, dtype) triple compiles to a separate cached binary, so
Algebra(3, 0, 'float32') and Algebra(3, 0, 'float64') are independent.
""")

alg_f32 = Algebra(3, dtype="float32")
alg_f64 = Algebra(3, dtype="float64")  # same as Algebra(3)
alg_i64 = Algebra(3, dtype="int64")

a_f = alg_f64("e1 + 2 e2")
a_i = alg_i64("e1 + 2 e2")

print("  float64 algebra — e1 + 2 e2:")
a_f.show("  a")

print("\n  int64 algebra   — e1 + 2 e2:")
a_i.show("  a")

print("\n  integer coefficients stay exact (no floating-point rounding):")
large = alg_i64({"e1": 1_000_000, "e12": 999_999})
large.show("  1000000 e1 + 999999 e12")


# ─────────────────────────────────────────────────────────────────────────────
# 5. Modulus (integer algebras only)
# ─────────────────────────────────────────────────────────────────────────────
hr("5. Modulus — integer algebras with automatic reduction")

print("""
Integer algebras can be equipped with a prime *modulus* p.  When a
modulus is set, every arithmetic result is automatically mapped into the
half-space interval [-(p-1)//2, (p-1)//2] (the "hmod" reduction used
in lattice-based cryptography).

    alg = Algebra(3, dtype='int64', modulus=101)

This is equivalent to working in Z_p for every coefficient.

There are two typical usage patterns:

  SINGLE MODULUS — one prime governs all operations throughout a script.
    See: py/examples/ga/algebra/modulus_algebra_single.py

  MULTIPLE MODULI — operations are performed under several different
    primes (e.g. for CRT reconstruction).
    See: py/examples/ga/algebra/modulus_algebra_multi.py
""")

MOD = 101
alg_mod = Algebra(3, dtype="int64", modulus=MOD)
e1m = alg_mod("e1")
e2m = alg_mod("e2")

# Show that 60 * (e1 * e1) = 60 is reduced to -41 under mod 101
large_coeff = alg_mod({1: 60})  # 60 e1
product = large_coeff * large_coeff  # 60*60 = 3600 e1*e1 = 3600 scalar
product.show(f"  (60 e1)² = 3600·s → hmod({MOD})")


# ─────────────────────────────────────────────────────────────────────────────
# 6. Properties
# ─────────────────────────────────────────────────────────────────────────────
hr("7. Algebra properties")

alg = Algebra(4, (4,), dtype="float64")  # G(4, e4²=-1) via tuple sig

print(f"""
  alg = Algebra(4, (4,), dtype='float64')

  alg.dim           = {alg.dim}          (vector-space dimension)
  alg.sig           = {alg.sig:#06b}  (signature bitmask; bit 3 set → e4² = -1)
  alg.dtype         = {alg.dtype!r}   (value type)
  alg.modulus       = {alg.modulus}        (None for float algebras)
  alg.algebra_dim   = {alg.algebra_dim}         (number of basis blades = 2**dim)
  alg.pseudoscalar_id = {alg.pseudoscalar_id:#06b}  (bitmask of the pseudoscalar blade)
  repr(alg)         = {alg!r}
""")
