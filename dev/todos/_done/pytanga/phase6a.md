# Phase 6a — Congruence arithmetic for integer multivectors

**Overview plan:** [plan.md](plan.md)
**Depends on:** Phase 1 (`_blade_names`), Phase 4 (`_build`), Phase 6 (`Algebra`/`MV`)
**Required by:** none (enhancement)

---

## Goal

Extend the Python binding so that integer‑valued multivectors can be used with
a modulus, matching the C++ `CModular` congruence functionality.
Every GA operation – geometric product, outer product, inner product, inverse –
must work with an explicit prime modulus that defines the field arithmetic.

---

## Background

The C++ library uses a generic congruence type that is transparently passed
to `GP`, `OP`, `IP`, and `inv`. For integer types this congruence is mandatory
because addition and multiplication modulo a prime are fundamentally different
from standard integer arithmetic.

The current Python binding templates already contain
- `#include "Tan.Math/Congruence.h"`
- a typedef `using TCong = {CONG_TYPE};` where `{CONG_TYPE}` is replaced by the
  codegen (`Tan::Math::CModular<CTYPE>` for integer types, `Tan::Math::CTrafoNone`
  otherwise).
- a placeholder `{INV_DEF}` which, for integer types, generates the inverse
  function with a modulus.

We need to extend this mechanism to the basic GA products.

---

## Design

For integer dtypes (`int32`, `int64`) the template will produce pybind11
functions `gp_mod`, `op_mod`, `ip_mod`, and `inv_mod` that require an extra
`unsigned` modulus parameter. The generic `gp`, `op`, `ip` are **not** exposed
for integer types, because they would be meaningless without a modulus.

The Python module object returned by `pytanga._cache.get_or_build()` therefore
contains:
- `gp`, `op`, `ip` → only for `float32`/`float64`
- `gp_mod`, `op_mod`, `ip_mod`, `inv_mod` → only for `int32`/`int64`

The `Algebra` wrapper reflects this:
- `Algebra.gp`, `Algebra.op`, `Algebra.ip` → work for float types, raise
  `TypeError` for integer types.
- `Algebra.gp_mod(a, b, modulus)`, `Algebra.op_mod(a, b, modulus)`,
  `Algebra.ip_mod(a, b, modulus)` → only available for integer types and call
  the corresponding C++ functions with modulus.
- `Algebra.inv(a, modulus=None)` → already works for both families (requires
  modulus for integer dtypes).

---

## Steps

### 6a.1 — Extend `_template.cpp` placeholders

Define new placeholders `{GP_MOD_DEF}`, `{OP_MOD_DEF}`, `{IP_MOD_DEF}` and
leave existing `{INV_DEF}`.

For floating‑point types, each placeholder is replaced with the current plain
binding (as it is now), and for integer types with a `py::def` that accepts an
extra `unsigned` argument and internally creates a `TCong` and calls the
corresponding GA function with congruence.

Example for `GP`:

```cpp
{GP_MOD_DEF}
```

Will be replaced with:

```
m.def("gp", [](const TDynMV& a, const TDynMV& b) { ... });   // (float)
```
for float, and for integer:
```
m.def("gp_mod", [](const TDynMV& a, const TDynMV& b, unsigned mod) {
     TDynMV c;
     TCong cong(mod);
     Tan::GA::GP(c, a, b, cong);
     c.Prune();
     return c;
}, py::arg("a"), py::arg("b"), py::arg("mod"));
```

Similarly for `op`, `ip`, `inv`. The existing generic `gp`, `op`, `ip` bindings
are removed for integer types.

- [x] Step 6a.1

### 6a.2 — Update `pytanga/_codegen.py` to fill the placeholders

Modify the `generate()` function signature (or helper) to emit the appropriate C++
fragment for each new placeholder based on the *dtype* parameter.

- If dtype is a floating‑point type → insert the original `m.def("gp", ...)`
  etc. and set `{GP_MOD_DEF}`, … to an empty string.
- If dtype is integer → insert the `_mod` variants and fill the `{GP_MOD_DEF}`
  fields with the modulus‑aware code. Also remove/omit the plain `gp`, `op`, `ip`
  for integer types (they become an empty string).

- [x] Step 6a.2

### 6a.3 — Add modulus‑based methods to `Algebra`

In `pytanga/__init__.py`, add to `Algebra`:

- `gp_mod(a, b, modulus)`
- `op_mod(a, b, modulus)`
- `ip_mod(a, b, modulus)`

Each method validates the dtype and forwards to the corresponding function on
the C++ module (`self._mod.gp_mod`, …). If the dtype is not integer, raise
`TypeError`.

Make sure the existing `inv` method already handles the modulus, but double‑check
that the C++ module for integer types exports `inv` with modulus (it should via
`{INV_DEF}` placeholder). No changes to `inv` needed, but ensure that the fallback
for float uses `inv` without modulus.

- [x] Step 6a.3

### 6a.4 — Extend `Algebra.gp`, `.op`, `.ip` for integer dtypes

For integer types, the regular `gp`, `op`, `ip` should raise a suggestive error:

```python
if self._dtype in ("int32", "int64"):
    raise TypeError(
        "op() is not available for integer dtypes. Use op_mod(a, b, modulus) instead."
    )
```

This prevents accidental use and guides the user to the correct API.

- [x] Step 6a.4

### 6a.5 — Adjust the data‑type‑dependent `{CONG_TYPE}` and `{INV_DEF}` handling

Ensure `_codegen.py` correctly sets `{CONG_TYPE}` to `Tan::Math::CTrafoNone` for
float types and `Tan::Math::CModular<int64_t>` (or `uint64_t`) for integer types.
(This is likely already done, but verify.)

Also update the `{INV_DEF}` placeholder to use the same modulus‑aware pattern
for integer types.

- [x] Step 6a.5

### 6a.6 — Smoke test the new functionality

Write a minimal test (do not commit as part of this phase – manual validation):

```python
import pytanga

alg = pytanga.Algebra(dim=3, sig=0, dtype="int64")
a   = alg.multivector({1: 1})   # e1
b   = alg.multivector({2: 1})   # e2
mod = 1000000007                 # a prime

# e1 * e1 ≡ 1 (mod mod)
prod = alg.gp_mod(a, a, mod)
assert prod[0] == 1   # scalar blade with id 0

# e1 ^ e2 ≡ e12
wedge = alg.op_mod(a, b, mod)
assert wedge[3] == 1   # blade id 3 = e12

# inv(e1) ≡ e1 because e1*e1 ≡ 1
e1_inv = alg.inv(a, mod)
assert e1_inv[1] == 1
```

Ensure that calling `alg.gp(a, b)` raises `TypeError`.

- [x] Step 6a.6

---

## Completion check

- [x] `_template.cpp` contains the new placeholders and the codegen correctly replaces them.
- [x] `Algebra.gp_mod`, `.op_mod`, `.ip_mod` exist and work for integer dtypes.
- [x] Regular `Algebra.gp`, `.op`, `.ip` raise `TypeError` for integer dtypes.
- [x] The example above passes.
- [x] A float algebra still works as before (no regression).
- [x] The cache correctly stores/loads both float and integer modules.
