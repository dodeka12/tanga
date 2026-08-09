# Galgebra → Tanga: Multivector Operations Parity Plan

Map the full set of galgebra multivector operations into tanga, preserving
existing tanga operations where they differ.

**Date:** 9 August 2026  
**Reference:** `galgebra/mv.py` (class `Mv`), `galgebra/ga.py` (class `Ga`),
`galgebra/README.md` operator tables; tanga `py/pytanga/algebra/_mv.py`,
`py/pytanga/algebra/_algebra.py`.

> **Notation:** In mathematical formulas, `A`, `B`, `V` etc. denote multivectors
> (`MV` instances).  This follows standard GA convention where uppercase
> letters are multivectors.

---

## 1. Operations already in tanga — no change

| # | Galgebra | Tanga | Notes |
|---|----------|-------|-------|
| 0a | `rev()` / `~A` | `rev()` / `~mv` | Reverse. Identical. |
| 0b | `scalar()` | `scalar` (property) | Scalar coefficient. API differs (method vs property). OK as-is. |
| 0c | `grade(k)` / `get_grade(k)` / `A[k]` | `grade(k)` / `grade_proj(…)` | Grade projection. Tanga's `grade_proj` will be **extended** to also accept a list of grades (see §3.3). |
| 0d | `dual()` | `dual()` | Tanga has **signed** dual (Hodge-like). Galgebra's is configurable via `dual_mode`. Tanga also has `complement` (unsigned) and `ldual` (left). Compatible. |
| 0e | `inv()` | `inv()` | Inverse. Both compute `A⁻¹`. Compatible. |
| 0f | `sp(A, B)` (no switch) | `sp(a, b)` | Scalar part of `A * B`. Identical. |
| 0g | `mag2()` / `mag()` | `mag2` / `mag` (property) | Sum-of-squares magnitude. Identical. |
| 0h | `A * B` | `A * B` / `gp()` | Geometric product. |
| 0i | `A ^ B` | `A ^ B` / `op()` | Outer (wedge) product. |
| 0j | `A | B` | `A | B` / `ip()` | Inner (left-contraction) product. See §3.4 for distinction from right contraction. |
| 0k | `A / B` | `A / B` | Division (A times inverse of B). |
| 0l | `normalized()` | `normalized()` | Normalize to unit magnitude. |
| 0m | `is_scalar()` | `is_scalar` (property) | Will be updated to use `precision` threshold (see §1.1). |
| 0n | `is_zero()` | `is_zero` (property) | Will be updated to use `precision` threshold (see §1.1). |
| 0o | `proj(blade_lst)` | `project_to(other)` | Tanga's `project_to` will be **extended** to also accept `int` (blade mask) or `list[int]` (blade IDs); no separate method needed (see §3.3). |

### 1.1 Precision / tolerance on Algebra

The `Algebra` class gains a `_precision` attribute (default `1e-10`), settable
via the constructor and a read/write property:

```python
alg = Algebra(3, precision=1e-8)
alg.precision   # → 1e-8
alg.precision = 1e-12
```

This value controls the tolerance used by:
- `prune()` — removes coefficients with `abs(coeff) < precision`
- `is_zero()` — returns `True` when all `abs(coeff) < precision`
- `is_scalar()` — ignores non-scalar blades whose `abs(coeff) < precision`



---

## 2. Exception: tanga conjugate stays — galgebra ccon added separately

Galgebra's "Clifford conjugate" (`ccon`) is **different** from tanga's `conj`:

| Operation | Definition | Metric-dependent? |
|-----------|------------|-------------------|
| tanga `conj()` | `rev(B_k) × (−1)^r` where *r* = count of negative‑metric basis vectors in the blade | **Yes** — sign depends on signature |
| galgebra `ccon()` | `g_invol(B_k).rev()` = `(−1)^(k(k+1)/2) B_k` | **No** — purely grade‑based |

Tanga's `conj()` **stays unchanged**. Galgebra's `ccon` is added as a
**separate, new operation** (see §3).

---

## 3. New operations to add from galgebra

### 3.1 High-priority (core GA operations)

| # | Galgebra name | Suggested tanga name | Signature | Semantics |
|---|---------------|----------------------|-----------|-----------|
| G1 | `g_invol()` | **`grade_involution`** or `ginvol` | `MV → MV` | Grade involution: negates odd-grade parts. `ginvol(B_k) = (−1)^k · B_k`. Pure Python using existing `grade()`. |
| G2 | `ccon()` | **`grade_conj`** | `MV → MV` | Galgebra-style Clifford conjugate (grade-based, metric-independent). `grade_conj(B_k) = (−1)^(k(k+1)/2) · B_k`. Pure Python: `grade_involution(self).rev()`. |
| G3 | `sp(B, switch='rev')` | **`scalar_product`** | `(self: MV, other: MV, *, rev: bool = False) → float\|int` | Galgebra's full scalar product. `a.scalar_product(b, rev=True)` computes `scalar_part(rev(a) * b)`. See §4. |
| G4 | `norm2()` / `norm()` | **`norm2`** / **`norm`** | `MV → float` | Quadratic-form-based norm. In Euclidean: identical to `mag2`/`mag`. In non-Euclidean: `norm2(A) = \|scalar_part(rev(A)*A)\|`, `norm(A) = sqrt(norm2(A))`. Distinct from existing `mag2`/`mag`. |
| G5 | `qform()` | **`qform`** or `quadratic_form` | `MV → float` | Quadratic form: `scalar_part(rev(A) * A)`. Pure Python: `self.rev().sp(self)`. |
| G6 | `even()` / `odd()` | **`even`** / **`odd`** | `MV → MV` | Extract even-grade or odd-grade parts. Pure Python: sum `grade(k)` for even/odd k. |
| G7 | `exp()` | **`exp`** | `MV → MV` | Exponential of a multivector. See §3.4 for mathematical details. |
| G8 | `undual()` | **`undual`** | `MV → MV` | Inverse of the signed dual. See §3.5 for algebra-specific behaviour. |
| G9 | `cp()` / `acp()` | **`cp`** / **`acp`** | `(MV, MV) → MV` | Commutator `cp(A,B) = (A*B − B*A)/2`. Anti-commutator `acp(A,B) = (A*B + B*A)/2`. Pure Python. |
| G10 | `A > B` (right contraction) | **`rc`** or `right_contraction` | `MV × MV → MV` | Right contraction. See §3.6 for definition and comparison with inner product. |
| | G11 | Hestenes inner product | **`gp_min`** | `(MV, MV) → MV` | Hestenes inner product for pure blades: `gp_min(A,B) = grade_proj(gp(A,B), abs(grade(A)-grade(B)))`. Raises if not pure blades. See §3.6. |
| | G12 | outermost grade product | **`gp_max`** | `(MV, MV) → MV` | Outermost grade part for pure blades: `gp_max(A,B) = grade_proj(gp(A,B), grade(A)+grade(B))`. Raises if not pure blades. See §3.6. |

### 3.2 Medium-priority

| # | Galgebra name | Suggested tanga name | Signature | Semantics |
|---|---------------|----------------------|-----------|-----------|
| G11 | Hestenes inner product | **`gp_min`** | `(MV, MV) → MV` | Hestenes inner product for pure blades: `gp_min(A,B) = grade_proj(gp(A,B), abs(grade(A)-grade(B)))`. Raises if either operand is not a pure blade. See §3.6. |
| | G12 | | | G12 | outermost grade product | **`gp_max`** | `(MV, MV) → MV` | Outermost grade part for pure blades: `gp_max(A,B) = grade_proj(gp(A,B), grade(A)+grade(B))`. Raises if either operand is not a pure blade. See §3.6.
| G13 | `pure_grade()` | **`is_vector`** (property) | `MV → bool` | True if only grade-1 blades are non-zero. Pure Python. |
| G13 | `is_blade()` | **`is_blade`** (property) | `MV → bool` | True if MV is a simple r-vector. Requires blade factorization test. |
| G14 | `is_versor()` | **`is_versor`** (property) | `MV → bool` | True if MV is a versor (GP of invertible vectors). |
| G15 | `is_base()` | **`is_base`** (property) | `MV → bool` | True if MV is exactly one basis blade with coefficient 1. Pure Python. |
| G16 | `blade_coefs(blade_lst)` | **`blade_coefs`** | `(list[MV] \| None) → list[float]` | Coefficients for each blade in the given list. |
| G17 | `components()` | **`components`** | `MV → list[MV]` | Decompose MV into list of single-blade MVs. |
| G18 | `get_coefs(k)` | **`get_coefs`** | `MV × int → list[float]` | Grade-k coefficients in canonical blade order. |

### 3.3 Extensions to existing methods

**`project_to`** — extended to accept multiple types:

```python
def project_to(self, other: MV | int | list[int]) -> MV:
```

- `MV` — existing behaviour: restrict to blades present in `other`
- `int` — treat as a blade mask; retain only blades whose mask is a subset of this mask
- `list[int]` — treat as a list of blade IDs; retain only those exact blades

This absorbs galgebra's `proj(blade_lst)` without a separate method.

**`grade_proj`** — extended to accept multiple grades:

```python
def grade_proj(self, grade: int | list[int]) -> MV:
```

- `int` — existing behaviour: extract grade-k part ⟨A⟩_k
- `list[int]` — extract sum of those grade parts, e.g. `grade_proj([0, 2])` returns the scalar + bivector part

### 3.4 Exponential of a multivector

For a multivector `A` whose square is a scalar (`A² = s ∈ ℝ`):

```
exp(A) = cosh(√s) + (sinh(√s) / √s) * A          when s > 0
exp(A) = 1 + A                                     when s = 0
exp(A) = cos(√|s|) + (sin(√|s|) / √|s|) * A       when s < 0
```

Algorithm:
1. Compute `s = scalar_part(gp(A, A))` — must be scalar (raise `ValueError` if not).
2. Branch on `s = 0`, `s > 0`, `s < 0`.
3. Return the scalar-plus-A combination as a new `MV`.

If `A²` is **not** a scalar (A is not a "blade-like" element), `exp()` raises
`ValueError`.  This covers rotors (bivector generators), translators (null-square
elements), and dilators (scalar + vector combinations) — all common GA use-cases.

### 3.5 Undual by algebra

The undual is the inverse of the (signed) dual: `A.dual().undual() == A`.

In **E3/2, P3/2, N3/2** (where pseudoscalar I is invertible with I² = ±1):

```
undual(A) = A * I
```

This is a right-multiplication by the pseudoscalar I.  It is the inverse of
`dual(A) = A · I⁻¹` (right-contraction with pseudoscalar inverse).

In **PGA3/2** (where the pseudoscalar **is not invertible**):

```
undual(A) = J(A)
```

The J-map is the PGA-specific involution that satisfies `J(J(A)) = A` and is
constructed so that `dual(undual(A)) = A`.  In PGA3/2 the dual is defined via
the J-map (complement-like), so `dual` and `undual` may coincide — both may map
to the same J-map operation.

Each `Basis*` class may override `undual()` to provide the correct
algebra-specific implementation.

### 3.6 Left contraction vs. right contraction vs. inner product

The three products are related but distinct:

| Product | Tanga | Notation | Definition |
|---------|-------|----------|------------|
| Left contraction | `ip(A, B)` = `A \| B` | `A ⌋ B` | grade_k( B ) − grade_j( A ) for each grade-pair; zero when j > k |
| Right contraction | new: `rc(A, B)` | `A ⌊ B` | grade_k( B ) − grade_j( A ) for each grade-pair; zero when j < k |
 | `⟨AB⟩_{|k−j|}` | For pure blades: `grade_proj(gp(A,B), abs(grade(A)−grade(B)))`. Raises ValueError if not pure blades. |
| | Outermost grade product | new: `gp_max(A, B)` | `⟨AB⟩_{k+j}` | For pure blades: `grade_proj(gp(A,B), grade(A)+grade(B))`. Raises ValueError if not pure blades. |

**Key relationship:**

```
rc(A, B) = ip(B, A) · (−1)^(j(k−j))     [where j = grade(A), k = grade(B)]
```

For pure-grade operands, the right contraction can be computed from the left
contraction with a grade-dependent sign.

For tanga's `ip` (which IS left contraction): `ip(A, B)` vanishes whenever
`grade(A) > grade(B)`, and for `grade(A) ≤ grade(B)` only the highest-grade
parts of `GP(A, B)` that yield `grade(B) − grade(A)` are kept.

For the new `rc(A, B)`: vice versa — `grade(A) < grade(B)` vanishes, and when
`grade(A) ≥ grade(B)` only the parts yielding `grade(A) − grade(B)` are kept.

The **Hestenes inner product** `A · B` is the scalar product when A and B are
homogeneous of the same grade, and `⟨AB⟩_{\|k−j\|}` otherwise (only non-zero
when one operand is a vector).  Tanga's existing `sp()` covers the homogeneous
case.  In addition, tanga provides `gp_min()` for the full Hestenes inner
product on pure blades of any grade, and `gp_max()` for the outermost
grade part (see §3.6.1 below).


#### 3.6.1 gp_min — Hestenes inner product (blade-to-blade)

`gp_min(A, B)` computes the Hestenes inner product for two pure blades of
any grades (not just vectors when one is grade-1).  Formula:

```
gp_min(A, B) = grade_proj(gp(A, B), abs(grade(A) − grade(B)))
```

- Both A and B must be pure blades (use `is_grade()` to check); raises `ValueError` otherwise.
- When `grade(A) = grade(B)`, `gp_min(A, B)` returns the scalar part — same as `sp(A, B)`.
- Works for any grade combination: vector-vector, bivector-vector, trivector-bivector, etc.
- Implementation: compute `gp(A, B)`, determine grades via `is_grade()` checks, then call `grade_proj(result, abs(k−j))`.

#### 3.6.2 gp_max — outermost grade product (blade-to-blade)

`gp_max(A, B)` extracts the outermost (highest-grade) part of the geometric
product of two pure blades:

```
gp_max(A, B) = grade_proj(gp(A, B), grade(A) + grade(B))
```

- Both A and B must be pure blades; raises `ValueError` otherwise.
- Returns a blade of grade `grade(A) + grade(B)` (unless the product vanishes).
- For grade-1 vectors this gives the same result as the outer product `A ^ B`.
- For higher grades it extracts the outermost contribution of the geometric product.

Galgebra's symbolic operations (`simplify`, `expand`, `trigsimp`, `subs`, `diff`,
`Grad`, `pdiff`, `func`, `factor`, etc.) have **no numeric equivalent** in tanga
and are **not** in scope.


---

## 4. Naming discussion — scalar product

Galgebra's `sp(A, B, switch='')` / `sp(A, B, switch='rev')` computes either
`scalar_part(A * B)` or `scalar_part(rev(A) * B)`.

Tanga already has `sp(a, b)` = `scalar_part(a * b)` which must stay unchanged.

**Suggested name for the galgebra-style variant: `scalar_product`**

Rationale:
- Clearly describes a scalar-valued product of two MVs.
- The `rev` keyword makes the reversal explicit: `a.scalar_product(b, rev=True)`.
- Does not collide with the existing short, two-letter `sp`.
- Consistent naming — this returns a scalar, not an MV.
- Avoids cryptic names like `spr` or `sp_galgebra`.

Alternative (less preferred): `scp` (too close to `sp`, easy to typo).

---

## 5. Naming discussion — Clifford conjugate

Tanga's `conj()` stays. Galgebra's `ccon()` needs a distinct name.

**Suggested name: `grade_conj`**

Rationale:
- "Grade-based Clifford conjugate" — explicitly distinguishes from tanga's metric-aware `conj`.
- Short enough for frequent use (cf. `rev`, `conj`, `dual`).
- Matches the pattern of short-word GA involutions.
- Galgebra's `ccon` = `grade_involution(self).rev()`.

Alternative: `cliff_conj` (a bit long but very explicit).

---

## 6. Implementation approach

### 6.1 Pure Python (no C++ changes needed)

These can be implemented directly on top of existing tanga primitives:
`grade_involution`, `grade_conj`, `scalar_product`, `qform`, `even`, `odd`,
`undual`, `pure_grade`, `is_vector`, `is_base`, `components`, `blade_coefs`,
`get_coefs`, `cp`, `acp`, `gp_min`, `gp_max`.

Implementation pattern:
```python
# On MV class:
def grade_involution(self) -> "MV":
    """Grade involution: negate odd-grade parts."""
    return self.even() - self.odd()
```

The extensions to `project_to()` and `grade_proj()` are also pure Python
(they dispatch on the argument type and call existing primitives).

### 6.2 Precision support

The new `Algebra._precision` attribute requires changes in:
- `Algebra.__init__` — new `precision` parameter (default `1e-10`)
- `Algebra.precision` — read/write property
- `DynMV.prune()` — already exists; wrap to pass `precision` threshold
- `Algebra.is_zero()` / `Algebra.is_scalar()` — use `precision` for comparisons
- `MV.is_zero` / `MV.is_scalar` (properties) — pass algebra precision

### 6.3 May benefit from C++ (performance)

- `norm` / `norm2` — already have `mag2` at C++ level; `norm2` could follow same pattern.
- `right_contraction` / `rc` — C++ `IP` is left-contraction; right-contraction would be a new product analogous to `IP`.
- `exp` — requires mathematical logic; can be pure Python calling existing `gp` and `scalar`.
- `is_blade` / `is_versor` — more complex checks; may benefit from C++ `blade_factorize`.

### 6.4 Files to modify

| File | What changes |
|------|--------------|
| `py/pytanga/algebra/_algebra.py` | `precision` property, Algebra-level methods, extend `project_to` and `grade_proj` |
| `py/pytanga/algebra/_mv.py` | MV-level methods and properties for new operations |
| `py/pytanga/basis/pga3.py` | Override `undual()` with J-map |
| `py/pytanga/basis/pga2.py` | Override `undual()` with J-map |
| Tests (`py/tests/algebra/`) | Add tests for each new operation |
| `py/pytanga/codegen/_mv_operators.py` | (Only if C++ bindings needed for `rc`, `norm`, etc.) |
| `docs/py/mv.md` | Document new operations |




---

## 7. Complete operation inventory (galgebra → tanga mapping)

| Galgebra | Tanga (existing) | Tanga (new) | Notes |
|----------|-----------------|-------------|-------|
| `rev()` / `~A` | `rev()` / `~mv` | — | Same |
| `ccon()` | `conj()` (metric-aware) | `grade_conj` | **Different math** — tanga's `conj` includes `(−1)^r` metric sign |
| `g_invol()` | — | `grade_involution` | New |
| `even()` / `odd()` | — | `even` / `odd` | New |
| `norm()` / `norm2()` | `mag` / `mag2` (different def) | `norm` / `norm2` | New definition |
| `qform()` | — | `qform` | New |
| `exp()` | — | `exp` | New |
| `dual()` | `dual()` (signed) / `complement()` (unsigned) / `ldual()` (left) | `undual` | New — algebra-specific |
| `sp(A, B)` | `sp(a, b)` | `scalar_product` (with `rev` kwarg) | `sp` stays; galgebra variant added |
| `inv()` | `inv()` | — | Same |
| `grade(k)` / `A[k]` | `grade(k)` / `grade_proj` | extended to accept `list[int]` | Extended |
| `scalar()` | `scalar` (property) | — | Same concept, different API |
| `mag2()` / `mag()` | `mag2` (property) / `mag` (property) | — | Same |
| `normalized()` | `normalized()` | — | Same |
| `is_scalar()` | `is_scalar` (property) | updated to use `precision` | Updated |
| `is_zero()` | `is_zero` (property) | updated to use `precision` | Updated |
| `proj(blades)` | `project_to` | extended to accept `int | list[int]` | Extended |
| `*` | `*` (gp) | — | Same |
| `^` | `^` (op) | — | Same |
| `\|` | `\|` (ip, left-contraction) | — | Same |
| `<` (left contraction) | `\|` (ip) | — | Same — tanga's ip = left contraction |
| `>` (right contraction) | — | `rc` or `right_contraction` | New |
| | Hestenes inner product | — | `gp_min` | New — blade-to-blade: `<AB>_{|k-j|}` |
| | outermost grade product | — | `gp_max` | New — blade-to-blade: `<AB>_{k+j}` |
| `abs(A)` (norm) | — | `norm` | New |
| `/` | `/` | — | Same |
| `is_vector()` | — | `is_vector` (property) | New |
| `is_blade()` | — | `is_blade` (property) | New |
| `is_versor()` | — | `is_versor` (property) | New |
| `is_base()` | — | `is_base` (property) | New |
| `pure_grade()` | `is_grade(k)` (different) | `pure_grade` | New |
| `blade_coefs()` | — | `blade_coefs` | New |
| `components()` | `to_dict()` (different) | `components` | New |
| `get_coefs(k)` | — | `get_coefs` | New |
| `commutator` | — | `cp` / `acp` | New — commutator + anti-commutator |
| `undual()` | — | `undual` (algebra-specific) | New — may coincide with `dual` in PGA |
| `simplify/expand/subs/…` | — | — | **Not applicable** (symbolic) |

---

## 8. Order of work (recommended)

### Phase 0 — Foundation
- Add `Algebra.precision` property and integrate into `prune`, `is_zero`, `is_scalar`.

### Phase A — Pure Python, high impact
- G1: `grade_involution`  
- G2: `grade_conj`  
- G3: `scalar_product` (with `rev` kwarg)  
- G5: `qform`  
- G6: `even` / `odd`

### Phase B — Norm & exponentiation
- G4: `norm` / `norm2`  
- G7: `exp`

### Phase C — Extend existing methods
- Extend `project_to` to accept `int` / `list[int]`
- Extend `grade_proj` to accept `list[int]`

### Phase D — Duals & products
- G8: `undual` (with algebra-specific overrides in `BasisPGA3`, `BasisPGA2`)
- G9: `cp` / `acp` (commutator + anti-commutator)
- G10: `rc` / `right_contraction`
- G11: `gp_min` (Hestenes inner product)
- G12: `gp_max` (outermost grade product)

### Phase E — Type checks & coefficients
- G13–G20: `pure_grade`, `is_vector`, `is_blade`, `is_versor`, `is_base`, `blade_coefs`, `components`, `get_coefs`

---

## 9. Design decisions

1. **`conj` stays metric-aware.** Tanga's Clifford conjugate includes the
   metric sign `(−1)^r`. Galgebra's is purely grade-based. Both are legitimate
   definitions; tanga keeps both under different names.

2. **`mag`/`mag2` vs `norm`/`norm2`.** Tanga retains its existing
   sum-of-squares magnitude. The galgebra-style quadratic-form norm is added
   separately. This preserves backward compatibility.

3. **`sp` stays as-is.** The galgebra-style variant with optional reversal
   gets a new name (`scalar_product`) to avoid API breakage.

4. **Galgebra `dual` vs tanga `dual`.** Tanga's `dual` is the signed Hodge-like
   dual. Galgebra's is configurable (left/right multiply by I or I⁻¹, with
   configurable sign). Tanga already covers these cases via `dual`, `complement`,
   and `ldual`. No changes needed.

5. **Right contraction.** Tanga's `ip` is already left contraction. Right
   contraction is added as `rc(A, B)` = `ip(B, A) × (−1)^(grade(A)(grade(B)−grade(A)))`.
   Pure Python or C++ binding.

6. **`simplify`/`expand`/`subs`/`diff` are not ported.** These are
   symbolic-algebra operations with no numeric equivalent.

7. **`project_to` absorbs galgebra's `proj`.** Instead of a separate
   `project_onto` method, `project_to` is extended to accept a blade mask
   (`int`) or blade ID list (`list[int]`), unifying the API.

8. **`grade_proj` extended for multi-grade selection.** Accepting a
   `list[int]` avoids the need for a separate multi-grade method (galgebra's
   `even()`/`odd()` already cover the most common use).

9. **`commutator` → `cp` + `acp`.** Galgebra mentions commutator conceptually.
   Tanga provides both commutator `cp` and anti-commutator `acp` as separate
   two-letter methods following the `sp`, `gp`, `ip`, `op` convention.

10. **`undual` is algebra-aware.** Each `Basis*` class overrides
    `undual()` where needed: E3/P3/N3 use `A * I`; PGA3/PGA2 use the J-map.
    In PGA, `dual` and `undual` may be the same operation.

11. **`precision` on Algebra.** A single tolerance value on the Algebra
    instance controls numerical zero thresholds across `prune()`,
    `is_zero()`, and `is_scalar()`, replacing ad-hoc hardcoded thresholds.

12. **`gp_min` / `gp_max` for pure blades.** The Hestenes inner product and
    outermost grade product are defined for homogeneous (pure-grade) blades.
    Both require operands to be pure blades (checked via `is_grade()`) and
    raise `ValueError` otherwise.  `gp_min` extracts `⟨AB⟩_{|k−j|}` and
    `gp_max` extracts `⟨AB⟩_{k+j}`, using the extended `grade_proj()`.  For
    grade-1 vectors, `gp_max` coincides with the outer product.
