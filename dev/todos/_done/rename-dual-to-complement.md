# Rename `dual()` → `complement()` and `sdual()` → `dual()`

**Date:** 31 July 2026  
**Status:** Plan — do not implement yet

---

## Motivation

TANGA currently has two dual operations:

| Current name | Definition | Dual-of-dual |
|-------------|------------|--------------|
| `dual()` | Unsigned dual: bitwise XOR of blade mask with pseudoscalar, no sign change | Always `A` |
| `sdual()` | Signed dual: ★A = A · I⁻¹ (geometric product with inverse pseudoscalar) | ±A |

The naming is backwards from the user perspective: the geometrically correct dual — the one that satisfies **★(a ∧ b) = a × b** in G(3,0) — is `sdual()`. The unsigned operation is purely combinatorial (a bitwise complement, not a true Clifford dual). Users coming from the GA literature expect `dual()` to be the Hodge/Clifford dual, not a bitwise complement.

### Why the signed dual is the "true" dual

In Cl(3) with pseudoscalar **I** = **e₁₂₃** (I² = −1):

```
a ∧ b = (a₁b₂ − a₂b₁) e₁₂ + (a₁b₃ − a₃b₁) e₁₃ + (a₂b₃ − a₃b₂) e₂₃
```

The signed dual via I⁻¹ = e₃₂₁:

```
(a ∧ b) · I⁻¹ = (a₂b₃ − a₃b₂) e₁ − (a₁b₃ − a₃b₁) e₂ + (a₁b₂ − a₂b₁) e₃
              = a × b   ✓
```

The unsigned (bitwise complement) dual would give the wrong sign on the e₂ component (maps e₁₃ → e₂ without the − sign).

The sign difference arises because `dual()` does a pure XOR of blade IDs while `sdual()` additionally accounts for the permutation parity of reordering the blade basis vectors with the pseudoscalar (via `GPSign()` / `GetSignedDualSign()` in the C++ backend).

---

## Naming Conventions

| Old name | New name | C++ function | Rationale |
|----------|----------|-------------|-----------|
| `dual()` | `complement()` | `GA::Complement` | Pure bitwise complement — not the Clifford dual |
| `sdual()` | `dual()` | `GA::Dual` | Standard Clifford dual ★A = A · I⁻¹ |

The `dual()` method on `MV` and `Algebra` becomes the **signed** dual (previously `sdual()`). The `complement()` method replaces the old unsigned `dual()`.

---

## Scope

The rename touches these layers, listed in dependency order (each step builds on the previous; no step requires refactoring an earlier step):

| Layer | Files affected | What changes |
|-------|---------------|-------------|
| **C++ blade/mv** | `cpp/Tan.GA/Blade.h`, `cpp/Tan.GA/MV_Operators.h` | Rename existing methods + add `GetLeftDual`/`LDual` |
| **Python binding** | `py/pytanga/codegen/_mv_operators.py` (or binding layer) | Regenerate with new C++ names + new `ldual` wrapper |
| **Python Algebra/MV** | `py/pytanga/algebra/_algebra.py`, `py/pytanga/algebra/_mv.py` | Rename methods + add `ldual()` — **after** binding is ready |
| **Python geometry** | `py/pytanga/geometry/*.py` | **No change needed** — `.sdual()` → `.dual()` is automatic |
| **Python examples** | `py/examples/tensor/rotor_01.py` | `.dual()` → `.complement()` |
| **Docs** | `docs/py/algebra/duals.md`, `docs/cpp/duals.md`, and others | Rewrite after all code is in place |

### Geometry code — already correct

The geometry modules use **only** `sdual()` (the signed/geometric dual), never `dual()`:

```
py/pytanga/geometry/create_e3.py:97     ipns.sdual()
py/pytanga/geometry/create_n3.py        (multiple) .sdual()
py/pytanga/geometry/create_p3.py:91     ipns.sdual()
py/pytanga/geometry/create_pga3.py      (multiple) .sdual()
py/pytanga/geometry/analysis_e3.py:157  mv.sdual()
py/pytanga/geometry/analysis_n3.py      (multiple) .sdual()
py/pytanga/geometry/analysis_p3.py      (multiple) .sdual()
```

After renaming `sdual()` → `dual()`, all these callsites become `.dual()` — no code changes needed in the geometry layer.

The only usage of the unsigned `.dual()` outside the documentation is:

```
py/examples/tensor/rotor_01.py:81     alg("e1+e2+e3").dual()
```

This expects the bitwise complement (converts a vector to a bivector in E3). After the rename, it becomes `.complement()`.

---

## Implementation Phases (in dependency order)

### Phase 1 — C++: Rename existing + add left dual (`Blade.h` + `MV_Operators.h`)

All C++ changes happen together in one pass so the binding can be regenerated once.

#### 1.1 `CBlade` class (`cpp/Tan.GA/Blade.h`)

**Rename existing methods:**

| Old method | New method | Logic change? |
|-----------|-----------|--------------|
| `GetDual(blDual)` | `GetComplement(blDual)` | No — name only |
| `GetDual(fValue, blDual)` | `GetComplement(fValue, blDual)` | No — name only |
| `GetSignedDualSign(uSign, blDual)` | `GetDualSign(uSign, blDual)` | No — name only |
| `GetSignedDual(fValue, blDual)` | `GetDual(fValue, blDual)` | No — name only |

**Add new `GetLeftDual` methods** (alongside the renamed ones):

```cpp
// Gets the sign of the left dual I · blade.
// Pseudoscalar on the LEFT of GPSign; no conjugate correction.
void GetLeftDualSign(unsigned &uSign, CBlade<...> &blDual) const
{
    const CBlade<...> blPS(GetPseudoScalar());
    uSign = 0;
    GPSign(uSign, blDual, blPS, *this);
}

// Applies the left dual sign to a coefficient value.
template <typename TValue>
void GetLeftDual(TValue &fValue, CBlade<...> &blDual) const
{
    unsigned uSign = 0;
    GetLeftDualSign(uSign, blDual);
    if ((uSign & 1) != 0) { fValue = -fValue; }
}
```

Key difference from `GetDual`: `GPSign(blPS, *this)` — pseudoscalar on the **left**, no `GetConjugateSign()` correction.

#### 1.2 Free functions (`cpp/Tan.GA/MV_Operators.h`)

**Rename:**

| Old function | New function | Wraps blade method |
|-------------|-------------|-------------------|
| `GA::Dual(wB, wA)` | `GA::Complement(wB, wA)` | `CBlade::GetComplement` |
| `GA::SDual(wB, wA)` | `GA::Dual(wB, wA)` | `CBlade::GetDual` |

**Add:**

| New function | Wraps blade method |
|-------------|-------------------|
| `GA::LDual(wB, wA)` | `CBlade::GetLeftDual` |

Implementation follows the same pattern as the existing `Dual`/`SDual` — iterate over blades in the multivector and apply the blade-level method to each blade's coefficient.

### Phase 2 — Regenerate Python Bindings

After the C++ headers are updated, regenerate the Python binding code so the `mod` object exposes the correct function names.

The binding maps Python attribute names to C++ free functions. After Phase 1, the C++ side has:

| C++ function | Intended Python name |
|-------------|---------------------|
| `GA::Complement` | `mod.complement` |
| `GA::Dual` (was `GA::SDual`) | `mod.dual` |
| `GA::LDual` (new) | `mod.ldual` |

The binding generation is in `py/pytanga/codegen/_mv_operators.py`. Update the list of wrapped operators and regenerate. After this step, calling e.g. `mod.dual(a._impl)` calls the new C++ `GA::Dual` (signed).

Phase 2 depends on Phase 1 and must complete before Phase 3.

### Phase 3 — Python `Algebra` and `MV` methods

Now that the C++ binding exposes `complement`, `dual` (signed), and `ldual`, update the Python wrapper classes.

#### 3.1 `Algebra` methods (`py/pytanga/algebra/_algebra.py`)

```python
# Remove: def dual(self, a: MV) → unsigned
# Remove: def sdual(self, a: MV) → signed
# Add:
def complement(self, a: MV) -> MV:
    """Bitwise blade complement (XOR with pseudoscalar), no sign change."""
    return MV(self._mod.complement(a._impl), self)

def dual(self, a: MV) -> MV:
    """Signed dual ★A = A · I⁺.  In G(3,0): ★(a ∧ b) = a × b."""
    return MV(self._mod.dual(a._impl), self)

def ldual(self, a: MV) -> MV:
    """Left dual I · A.  In G(3,0): ldual(a ∧ b) = −(a × b)."""
    return MV(self._mod.ldual(a._impl), self)
```

#### 3.2 `MV` methods (`py/pytanga/algebra/_mv.py`)

```python
# Remove: def dual(self) → unsigned
# Remove: def sdual(self) → signed
# Add:
def complement(self) -> "MV":
    """Bitwise blade complement, no sign change. Not the Clifford dual."""
    return self._alg.complement(self)

def dual(self) -> "MV":
    """Signed dual ★self = self · I⁺.  In G(3,0): ★(a∧b) = a×b."""
    return self._alg.dual(self)

def ldual(self) -> "MV":
    """Left dual I · self.  In G(3,0): ldual(a∧b) = −(a×b)."""
    return self._alg.ldual(self)
```

After this phase the geometry code (which calls `.sdual()`) will break — but Phase 4 fixes that automatically.

### Phase 4 — Geometry Code: verify and rename `sdual()` → `dual()`

**Step 4.0 — Verification:** Before renaming, verify that the geometry code uses **only** the signed dual and never the unsigned one. The signed dual (`.sdual()`) is the geometrically correct operation for all entity/operator dualization — it satisfies `dual(a ∧ b) = a × b` in G(3,0). The unsigned complement (`.dual()` currently, `.complement()` after rename) does not belong in geometry code because its sign is wrong for cross-product-like operations.

Grep all geometry files for `.dual()` (unsigned) and `.sdual()` (signed):

```
grep -rn "\.dual()" py/pytanga/geometry/ | grep -v sdual
```

Expected result: **zero matches**. All geometry dualization uses `.sdual()`. If any `.dual()` call is found, it is a bug and must be changed to `.sdual()` before proceeding.

**Step 4.1 — Rename:** After Phase 3, `.sdual()` no longer exists — it has been renamed to `.dual()`. A simple search-and-replace across the geometry modules fixes this:

**Search:** `.sdual()`  
**Replace:** `.dual()`

Files to update:

| File | Occurrences |
|------|-----------|
| `py/pytanga/geometry/create_e3.py` | 1 |
| `py/pytanga/geometry/create_n3.py` | ~12 |
| `py/pytanga/geometry/create_p3.py` | 1 |
| `py/pytanga/geometry/create_pga3.py` | ~3 |
| `py/pytanga/geometry/analysis_e3.py` | 1 |
| `py/pytanga/geometry/analysis_n3.py` | ~4 |
| `py/pytanga/geometry/analysis_p3.py` | ~3 |

No logic changes — these calls already used the signed dual, just under the old name.

**Step 4.2 — Re-verify:** After the rename, grep for any remaining `.sdual()` or `.complement()` calls in geometry:

```
grep -rn "\.sdual()" py/pytanga/geometry/
grep -rn "\.complement()" py/pytanga/geometry/
```

Expected result: zero matches for `.sdual()` (all renamed), zero matches for `.complement()` (not used in geometry — the signed dual is the correct operation).

**Design rule:** Geometry code must **never** use `complement()` for dualization. The complement is only for bitmask tracking and combinatorial blade gymnastics. All geometric dualization (OPNS ↔ IPNS switching) uses `dual()` = A · I⁺.

### Phase 5 — Example Update

`py/examples/tensor/rotor_01.py` line 81:

```python
# OLD
rotor = to_rotor(angle, bivec=alg("e1+e2+e3").dual())

# NEW
rotor = to_rotor(angle, bivec=alg("e1+e2+e3").complement())
```

This converts a grade-1 vector to a bivector in E3 via the unsigned complement. After the rename, `.complement()` is the correct method.

### Phase 6 — Documentation

With all code in place, update the docs:

| File | Changes |
|------|---------|
| `docs/py/algebra/duals.md` | Rewrite: three operations (`complement`, `dual`, `ldual`) with cross-product justification, sign explanation, and the `ldual` triangulation identity |
| `docs/cpp/duals.md` | Rewrite: `Complement`, `Dual`, `LDual` with same explanations |
| `docs/py/algebra/mv.md` | Update method table |
| `docs/py/algebra/algebra.md` | Update method references |
| `docs/py/algebra/index.md` | Update text mentioning duals |

### Phase 7 — Tests

No test files currently test `MV.dual()` (unsigned) directly — `test_geometry_e3.py` tests `sdual()` implicitly through geometry create/analyze round-trips. After renaming, these tests continue to pass because they call `sdual()` which becomes `dual()` — no test code changes needed.

Consider adding tests to verify:
- `dual(a ∧ b) = a × b` in G(3,0)
- `ldual(a ∧ b) = −(a × b)` in G(3,0)
- `ldual(dual(A)) = (−1)^(k·(D−k)) · A` for pure blades
- `complement(complement(A)) = A` always (already true, just verifying the renamed method)

---

## Summary of All Changes (ordered by implementation phase)

| Phase | File | Change |
|-------|------|--------|
| 1 | `cpp/Tan.GA/Blade.h` | Rename `GetDual`→`GetComplement`, `GetSignedDual`→`GetDual`, `GetSignedDualSign`→`GetDualSign`; **add** `GetLeftDualSign`, `GetLeftDual` |
| 1 | `cpp/Tan.GA/MV_Operators.h` | Rename `GA::Dual`→`GA::Complement`, `GA::SDual`→`GA::Dual`; **add** `GA::LDual` |
| 2 | `py/pytanga/codegen/_mv_operators.py` | Regenerate bindings: `mod.complement`→`GA::Complement`, `mod.dual`→`GA::Dual` (signed), `mod.ldual`→`GA::LDual` |
| 3 | `py/pytanga/algebra/_algebra.py` | Replace `dual`/`sdual` with `complement`/`dual`; **add** `ldual` |
| 3 | `py/pytanga/algebra/_mv.py` | Replace `dual`/`sdual` with `complement`/`dual`; **add** `ldual` |
| 4 | `py/pytanga/geometry/*.py` | Search/replace `.sdual()` → `.dual()` (~25 occurrences across 7 files) |
| 5 | `py/examples/tensor/rotor_01.py` | `.dual()` → `.complement()` |
| 6 | `docs/py/algebra/duals.md` | Rewrite: three operations, cross-product justification, `ldual` triangulation identity |
| 6 | `docs/cpp/duals.md` | Rewrite with new names + `LDual` |
| 6 | `docs/py/algebra/mv.md` | Update method table |
| 6 | `docs/py/algebra/algebra.md` | Update method references |
| 6 | `docs/py/algebra/index.md` | Update text |
