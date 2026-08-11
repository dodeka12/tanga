# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""
binding_demo.py — How pytanga builds C++ backends on the fly.

OVERVIEW
========
pytanga has no pre-compiled extension bundled with the package.  Instead,
when you create an Algebra for a particular combination of (dim, sig, dtype),
pytanga:

  1. GENERATES a C++ source file from a pybind11 template, substituting the
     exact dimension, metric signature, and value type.
  2. COMPILES it with CMake + Ninja (or Make) into a Python extension (.so).
  3. CACHES the result under ~/.cache/pytanga/ (or $PYTANGA_CACHE_DIR).
  4. On subsequent uses, LOADS the cached binary in milliseconds — no
     recompilation unless the template or C++ headers change.

The cache key is a SHA-256 hash of:
  • the algebra parameters (dim, sig, dtype)
  • every .h header in the cpp/ tree
  • the binding template (_template.cpp)

Any change to those inputs automatically invalidates the cache for that
algebra, triggering a fresh compile on the next import.

Run with:
    uv run python py/examples/binding_demo.py
"""

import time
from pathlib import Path

import pytanga
from pytanga.codegen import cache_root, lookup, module_name

# generate() is an internal developer API — import from private module
from pytanga.codegen._generator import generate


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────
def hr(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Cache location
# ─────────────────────────────────────────────────────────────────────────────
hr("1. Cache location")

root = cache_root()
print(f"""
The compiled extensions are stored in:

    {root}

Each subdirectory is named after a SHA-256 digest (the cache key) and
contains the compiled .so plus a meta.json that records the algebra
parameters, the key, and a build timestamp.

Override the location with the PYTANGA_CACHE_DIR environment variable.
""")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Inspecting the cache
# ─────────────────────────────────────────────────────────────────────────────
hr("2. Inspecting cache entries")

import json  # noqa: E402

entries = sorted(root.glob("*/meta.json")) if root.exists() else []
if not entries:
    print("\n  (cache is empty — run another demo first to populate it)")
else:
    print(f"\n  Found {len(entries)} cached algebra(s):\n")
    for meta_path in entries:
        m = json.loads(meta_path.read_text(encoding="utf-8"))
        dim = m["dim"]
        sig = m["sig"]
        dtype = m["dtype"]
        ts = m.get("timestamp", "—")
        so = (meta_path.parent / m["so_path"]).stat().st_size // 1024
        print(
            f"    G({dim}, {sig:#06b})  dtype={dtype:<8}  "
            f"{so} kB   built {ts[:19].replace('T', ' ')} UTC"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 3. Cache hit — first load vs repeated load
# ─────────────────────────────────────────────────────────────────────────────
hr("3. Cache hit vs cache miss timing")

DIM, SIG, DTYPE = 3, 0, "float64"

already_cached = lookup(DIM, SIG, DTYPE) is not None

if already_cached:
    print(f"\n  G({DIM}, {SIG}) float64 is already in the cache.")
    print("  Loading it now (should be fast):\n")

    t0 = time.perf_counter()
    alg = pytanga.Algebra(DIM, SIG, DTYPE)
    elapsed = time.perf_counter() - t0
    print(f"    load time: {elapsed * 1000:.1f} ms")
else:
    print(f"\n  G({DIM}, {SIG}) float64 is NOT in the cache.")
    print("  Compiling now (first compile takes 5–20 s):\n")

    t0 = time.perf_counter()
    alg = pytanga.Algebra(DIM, SIG, DTYPE, verbose=True)
    elapsed = time.perf_counter() - t0
    print(f"\n    compile + load time: {elapsed:.1f} s")


# ─────────────────────────────────────────────────────────────────────────────
# 4. The generated C++ source
# ─────────────────────────────────────────────────────────────────────────────
hr("4. The generated C++ source")

print("""
pytanga never ships pre-written bindings.  Instead, _codegen.py reads
_template.cpp and substitutes concrete values for every placeholder:

    {DIM}        → vector-space dimension (e.g. 3)
    {SIG}        → metric signature bitmask (e.g. 0 for all-positive)
    {CTYPE}      → C value type (float, double, int32_t, int64_t)
    {CONG_TYPE}  → congruence helper class (float vs half-mod integer)
    {MODULE_NAME}→ Python module name (e.g. binding_dim3_sig0_float64)
    {GP_MOD_DEF} → geometric product (plain for float, modular for int)
    {INV_DEF}    → inverse (cong-free for float, modular for int)
    {REDUCE_DEF} → half-space reduction (int only; empty for float)

The result is a fully specialised .cpp that CMake compiles with -O2.
""")

# Show a snippet of what the generated code looks like
import tempfile  # noqa: E402

with tempfile.NamedTemporaryFile(suffix=".cpp", delete=False, mode="w") as tmp:
    tmp_path = Path(tmp.name)

generate(DIM, SIG, DTYPE, tmp_path)
lines = tmp_path.read_text(encoding="utf-8").splitlines()
tmp_path.unlink()

print(f"  First 30 lines of the generated binding for G({DIM}, {SIG}) float64:\n")
for i, line in enumerate(lines[:30], 1):
    print(f"  {i:3}  {line}")
print("  ...")


# ─────────────────────────────────────────────────────────────────────────────
# 5. Module name and what lives inside the extension
# ─────────────────────────────────────────────────────────────────────────────
hr("5. What's inside the compiled extension")

mod_name = module_name(DIM, SIG, DTYPE)
print(f"""
  Module name: {mod_name!r}

  Every compiled extension exposes:

    Constants
      ALGEBRA_DIM      — total number of basis blades (2**dim)
      PSEUDOSCALAR_ID  — bitmask of the pseudoscalar blade

    Class
      DynMV            — the dynamic multivector (thin C++ wrapper)
        .set(blade_id, value)
        .get(blade_id) → value
        .to_dict()     → Python dict {{blade_id: value, ...}}
        .blade_count() → number of non-zero blades currently stored
        .prune()       — remove zero-coefficient blades in-place
        .reset()       — clear all blades

    Free functions (all take DynMV arguments, return a new DynMV)
      gp(a, b)             geometric product
      op(a, b)             outer (wedge) product
      ip(a, b)             left inner product
      inv(a)               multiplicative inverse
      add(a, b)            component-wise addition
      sub(a, b)            component-wise subtraction
      neg(a)               unary negation
      scale(a, s)          scalar multiplication
      rev(a)               reverse (flip sign of grade-2,3 mod 4 blades)
      vp(versor, b)        versor product: versor * b * rev(versor)
      gp_mod(a, b, mod)    geometric product modulo mod  (int dtypes)
      inv(a, mod)          inverse modulo mod            (int dtypes)
      reduce(a, mod)       half-space modular reduction  (int dtypes)
""")

raw_mod = alg._mod
print(f"  ALGEBRA_DIM     = {raw_mod.ALGEBRA_DIM}")
print(
    f"  PSEUDOSCALAR_ID = {raw_mod.PSEUDOSCALAR_ID:#010b}  ({raw_mod.PSEUDOSCALAR_ID})"
)

# Demonstrate direct use of the raw C++ module (bypassing the MV wrapper)
a_impl = raw_mod.DynMV()
b_impl = raw_mod.DynMV()
a_impl.set(0b001, 1.0)  # e1
b_impl.set(0b010, 1.0)  # e2
c_impl = raw_mod.gp(a_impl, b_impl)
print(f"\n  Direct C++ call — gp(e1, e2).to_dict() = {c_impl.to_dict()}")
print("  (blade_id 3 = 0b011 = e1^e2 = e12)")


# ─────────────────────────────────────────────────────────────────────────────
# 6. Precompiling multiple algebras in parallel
# ─────────────────────────────────────────────────────────────────────────────
hr("6. Precompiling a set of algebras in parallel")

print("""
If you know upfront which algebras a script needs, you can compile them all
in parallel before your main computation starts:

    import pytanga
    pytanga.precompile([
        (3, 0,       "float64"),   # G(3,0)  — Euclidean 3D
        (4, 0b1000,  "float64"),   # G(4, e4²=-1) — PGA3
        (5, 0b10000, "float64"),   # G(5, e5²=-1) — CGA3
    ])

precompile() uses a ProcessPoolExecutor so the compilations run in separate
Python processes.  It prints a status line for each algebra as it finishes.

You would typically put this call in a one-time setup script (e.g. in a
Makefile or CI job) so normal runs always see warm cache hits.
""")

# Check which of the common algebras are already warm
to_check = [
    (3, 0, "float64", "G(3,0)   Euclidean 3D"),
    (4, 0b1000, "float64", "G(4,…)   PGA3"),
    (5, 0b10000, "float64", "G(5,…)   CGA3"),
    (3, 0, "int64", "G(3,0)   int64 (modular)"),
]
print("  Current cache status for common algebras:")
for dim, sig, dtype, label in to_check:
    hit = "WARM" if lookup(dim, sig, dtype) else "cold"
    print(f"    {hit}  {label}")


# ─────────────────────────────────────────────────────────────────────────────
# 7. Cache invalidation
# ─────────────────────────────────────────────────────────────────────────────
hr("7. Cache invalidation")

print("""
The cache is keyed on a SHA-256 hash of the algebra parameters AND the full
content of every C++ header plus the binding template.  This means:

  • Editing any .h in cpp/ automatically invalidates ALL cached algebras on
    the next import (each key embeds all headers).

  • Editing _template.cpp invalidates every cached algebra.

  • Changing dim, sig, or dtype gives a different key, so different
    algebra configs never collide.

You can also invalidate manually:

    from pytanga.codegen import invalidate, clear

    invalidate(3, 0, "float64")   # remove one entry
    clear()                        # wipe the entire cache

After invalidation the next Algebra(dim, sig, dtype) call re-compiles.
""")
