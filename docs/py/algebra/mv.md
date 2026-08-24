# The `MV` Class

`MV` represents a multivector belonging to a specific `Algebra` instance.
Coefficients are stored in the wrapped C++ `CDynamicMultivector` object;
arithmetic operators delegate to the parent `Algebra`.

```python
from pytanga.algebra import MV
```

See [`mv_demo.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/mv_demo.py) for a runnable walkthrough.

## Initialization

Multivectors are created by calling the `Algebra` instance (or
`alg.multivector(coeffs)`). Five input forms are accepted:

```python
alg = Algebra(3, 0)

# 1. Zero multivector
z = alg()

# 2. String expression — most readable for hand-written values
a = alg("1 + 2 e1 - 3 e2 + 4 e12")

# 3. Dict with string blade names ("s" for scalar)
b = alg({"e1": 2.0, "e2": -3.0, "e12": 4.0, "s": 1.0})

# 4. Dict with tuple keys — 1-based vector indices; (0,) or () for scalar
c = alg({(0,): 1.0, (1,): 2.0, (2,): -3.0, (1, 2): 4.0})

# 5. Dict with raw blade bitmasks (bit k corresponds to e_{k+1})
d = alg({0: 1.0, 1: 2.0, 2: -3.0, 3: 4.0})
```

String blade names use:
- `e1`, `e2`, `e3`, … for single-index blades
- `e12`, `e23`, … (compact, only for dim ≤ 9) or `e1,2,3` (comma form, any dim)
- `s` or a bare number for the scalar
- `I` for the pseudoscalar

## Coefficient Access

Read or write individual blade coefficients by blade name or raw bitmask:

```python
mv = alg("3 e1 + 5 e12")

# Read
mv["e1"]    # → 3.0
mv["e12"]   # → 5.0
mv["e2"]    # → 0.0  (absent blade)
mv[1]       # → 3.0  (raw bitmask: bit 0 set → e1)

# Write
mv["e2"] = -7.0
mv[3]   = 2.0      # bitmask 3 = 0b11 → e12
```

## Arithmetic Operators

| Expression | Meaning |
|------------|---------|
| `-a` | Negate all coefficients |
| `a + b` | Component-wise addition |
| `a - b` | Component-wise subtraction |
| `a * b` | Geometric product $ab$ |
| `a ^ b` | Outer (wedge) product $a \wedge b$ |
| `a \| b` | Inner product (symmetric) |
| `~a` | Reverse $\tilde{a}$: reverses blade factor order |
| `a / b` | $a \cdot b^{-1}$ (geometric product with inverse of $b$) |
| `s * a`, `a * s` | Scalar scaling ($s$ is `int` or `float`) |
| `a / s` | Scalar division |
| `s / a` | $s \cdot a^{-1}$ |

All binary operators also accept a plain `int` or `float` on either side;
the scalar is automatically promoted to a scalar multivector.

## Named Methods

| Method | Operator | Description |
|--------|----------|-------------|
| `a.gp(b)` | `a * b` | Geometric product |
| `a.op(b)` | `a ^ b` | Outer (wedge) product |
| `a.ip(b)` | `a \| b` | Inner product (symmetric) |
| `a.inv()` | — | Multiplicative inverse |
| `a.rev()` | — | Reverse $\tilde{a}$: reverses blade factor order |
| `a.conj()` | — | Clifford conjugate (metric‑aware, includes $(−1)^r$) |
| `a.vp(b)` | — | Versor product: $a \cdot b \cdot \tilde{a}$ |
| `a.nvp(b)` | — | Normalized versor product: $a \cdot b \cdot a^{-1}$ |
| `a.grade(k)` | — | Grade projection: extract ⟨a⟩ₖ (also accepts `list[int]`) |
| `a.complement()` | — | Unsigned complement — see [Duals](duals.md) |
| `a.dual()` | — | Signed dual ★A = A · I⁺ — see [Duals](duals.md) |
| `a.ldual()` | — | Left dual I · A — see [Duals](duals.md) |
| `a.sp(b)` | — | Scalar product: scalar part of a * b |
| `a.project_to(b)` | — | Restrict a to the blade set of b (also accepts `int` mask / `list[int]`) |
| `a.blade_inverse()` | — | Proper blade inverse $A^{-1} = \tilde{A} / \mathrm{IP}(A, \tilde{A})$ |
| `a.blade_pseudo_inverse()` | — | Pseudo-inverse of a blade: an inverse only w.r.t. the inner product $\langle A \cdot A^{-1} \rangle_0 = 1$; the reciprocal of a null blade |
| `a.blade_factorize()` | — | Factorize blade into $k$ normalized grade-1 vectors |
| `a.join(b)` | — | Join of two blades: smallest-grade blade containing both |
| `a.meet(b)` | — | Meet of two blades: largest-grade blade contained in both |
| `a.blade_factorize_versor()` | — | Factorize versor into `(scale, [factor_vectors])` |
| `a.project(blade)` | — | Project multivector onto a non-degenerate blade: $\mathrm{proj}_N(A)$ (null blade → pseudo-inverse fallback, not a true projection) |
| `a.reject(blade)` | — | Reject multivector from a non-degenerate blade: $A - \mathrm{proj}_N(A)$ (null blade → pseudo-inverse fallback, not a true rejection) |
| `a.show(label, fmt)` | — | Print in algebra display basis |

### Grade‑based Involutions

| Method | Description |
|--------|-------------|
| `a.grade_involution()` | Grade involution: negate odd‑grade parts. $\mathrm{ginvol}(⟨A⟩_k) = (−1)^k · ⟨A⟩_k$ |
| `a.grade_conj()` | Grade‑based Clifford conjugate (galgebra `ccon`, metric‑independent). $\mathrm{grade\_conj}(⟨A⟩_k) = (−1)^{k(k+1)/2} · ⟨A⟩_k$. Equivalent to `grade_involution().rev()` |
| `a.conj()` | Metric‑aware Clifford conjugate (existing — see [§2 distinction below](#clifford-conjugates)) |

### Grade Extraction

| Method | Description |
|--------|-------------|
| `a.even()` | Extract even‑grade part (grades 0, 2, 4, …) |
| `a.odd()` | Extract odd‑grade part (grades 1, 3, 5, …) |
| `a.grade(k)` | Extract grade‑k part ⟨a⟩ₖ. Also accepts `list[int]` for multi‑grade projection |
| `a.grade_proj(k)` | Alias for `grade(k)` (on `Algebra`) |

### Norms and Exponential

| Method | Description |
|--------|-------------|
| `a.norm2()` | Quadratic‑form‑based squared norm: $|\mathrm{scalar\_part}(\tilde{A} · A)|$. In Euclidean: same as `mag2` |
| `a.norm()` | Quadratic‑form‑based norm: $\sqrt{\mathrm{norm2}(A)}$ |
| `a.qform()` | Quadratic form: $\mathrm{scalar\_part}(\tilde{A} · A)$ |
| `a.exp()` | Exponential. Requires $A² ∈ ℝ$ (blade‑like); raises `ValueError` otherwise. Formula: $\cosh(√s) + (\sinh(√s)/√s)A$ for $s>0$, $1+A$ for $s=0$, $\cos(√|s|) + (\sin(√|s|)/√|s|)A$ for $s<0$ |

### Duals

| Method | Description |
|--------|-------------|
| `a.undual()` | Inverse of the signed dual. $A·I$ in E3/P3/N3; Hodge undualization of the J‑map in PGA (involutive in PGA2, `grade_involution` of `dual` in PGA3) |
| `a.duals_inverse()` | Synonym for `undual()` |

See [Duals](duals.md) for `dual()`, `complement()`, `ldual()`.

### Products

| Method | Description |
|--------|-------------|
| `a.scalar_product(b, *, rev=False)` | Scalar product with optional reverse. `rev=True` computes $\mathrm{scalar\_part}(\tilde{A}·B)$ |
| `a.cp(b)` | Commutator: $(A·B − B·A)/2$ |
| `a.acp(b)` | Anti‑commutator: $(A·B + B·A)/2$ |
| `a.rc(b)` | Right contraction $A ⌊ B$. Vanishes when $\mathrm{grade}(A) < \mathrm{grade}(B)$ |
| `a.gp_min(b)` | Hestenes inner product for pure blades: $⟨AB⟩_{\|k−j\|}$. Raises `ValueError` if not pure blades |
| `a.gp_max(b)` | Outermost grade product for pure blades: $⟨AB⟩_{k+j}$. For vectors = outer product. Raises `ValueError` if not pure blades |

### Products with reverse/conjugate flags

Each core product is also available with explicit per-operand reverse or
conjugate flags, matching galgebra's convention:

| Method | Description |
|--------|-------------|
| `a.gp_rev(b, rev_self=False, rev_other=False)` | Geometric product with optional reverse on either operand |
| `a.gp_conj(b, conj_self=False, conj_other=False)` | Geometric product with optional conjugate on either operand |
| `a.ip_rev(b, rev_self=False, rev_other=False)` | Inner product with optional reverse on either operand |
| `a.ip_conj(b, conj_self=False, conj_other=False)` | Inner product with optional conjugate on either operand |
| `a.op_rev(b, rev_self=False, rev_other=False)` | Outer product with optional reverse on either operand |
| `a.op_conj(b, conj_self=False, conj_other=False)` | Outer product with optional conjugate on either operand |

These delegate to the equivalent `Algebra` methods (`gp_rev`, `gp_conj`,
`ip_rev`, `ip_conj`, `op_rev`, `op_conj`).

## Modular Arithmetic Methods

For integer-dtype algebras, explicit per-call modulus variants exist.
These are required when two different moduli must be used on the same algebra
(see [`modulus_algebra_multi.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/modulus_algebra_multi.py)):

| Method | Description |
|--------|-------------|
| `a.gp_mod(b, p)` | Geometric product, then `hmod(·, p)` |
| `a.op_mod(b, p)` | Outer product, then `hmod(·, p)` |
| `a.ip_mod(b, p)` | Inner product, then `hmod(·, p)` |
| `a.inv(p)` | Modular inverse mod prime $p$ |
| `a.reduce(p)` | Apply `hmod` coefficient-wise |

See [Modulus Arithmetic](modulus.md) for details on `hmod` and modular
algebra construction.

## Utility Methods

| Method | Description |
|--------|-------------|
| `a.to_dict()` | Returns `{blade_name: coeff}` for all non-zero blades |
| `a.prune(tol=None)` | Removes coefficients `abs(coeff) < tol` in-place; returns `self`. When `tol` is `None`, uses `algebra.precision` |
| `a.normalized()` | Returns the MV scaled to unit magnitude `a / |a|` |
| `a.is_grade(k)` | True if this multivector is a pure grade‑*k* element |
| `repr(a)` | Produces a human-readable expression string |

## Properties

| Property | Return type | Description |
|---|---|---|
| `a.scalar` | `float \| int` | Scalar coefficient |
| `a.mag2` | `float \| int` | Sum of squared coefficients |
| `a.mag` | `float` | sqrt of mag2 |
| `a.is_zero` | `bool` | True if all coefficients within `algebra.precision` of zero |
| `a.is_scalar` | `bool` | True if all non‑scalar coefficients within `algebra.precision` of zero |
| `a.is_vector` | `bool` | True if only grade‑1 blades have non‑zero coefficients |
| `a.is_base` | `bool` | True if exactly one basis blade with coefficient 1 |
| `a.is_blade` | `bool` | True if a simple r‑vector (blade factorizable) |
| `a.is_versor` | `bool` | True if a versor (product of invertible vectors) |
| `a.grades` | `list[int]` | List of grades that have non‑zero coefficients |
| `a.algebra` | `Algebra` | The parent Algebra instance |

## Coefficient Methods

| Method | Description |
|--------|-------------|
| `a.blade_coefs(blade_lst=None)` | Coefficients for each blade in `blade_lst` (or all blades if `None`) |
| `a.components()` | Decompose into list of single‑blade MVs |
| `a.get_coefs(k)` | Grade‑*k* coefficients in canonical blade order |

### `to_dict()` example

```python
mv = alg("3 e1 - 2 e12")
print(mv.to_dict())   # → {'e1': 3.0, 'e12': -2.0}
```

### `show()`

`show()` prints the multivector in the algebra's display basis (if the parent
is a Basis subclass) or as a plain expression otherwise:

```python
mv.show("my vector")
mv.show("result", fmt=".6f")
```

## Grade and Blade Names

Blade bitmasks encode grade and index: the bitmask for an $r$-blade is an
$r$-bit integer.  The scalar has bitmask `0`; `e1` has bitmask `1`;
`e12 = e1 ∧ e2` has bitmask `3` (`0b11`); the pseudoscalar in $G(3)$ has
bitmask `7` (`0b111`).

String names follow the pattern `e<indices>` where indices are either
concatenated (compact form for dim ≤ 9) or comma-separated.
The scalar blade is named `s`.

Blade names are interpreted in canonical ascending order.  A name whose
indices are not ascending is accepted but carries the sign of the permutation
needed to sort them: `e31` resolves to `-e13` (because
$e_3 \wedge e_1 = -e_1 \wedge e_3$), `e321` resolves to `-e123`, and so on.
This sign applies to string expressions, dict string keys, tuple keys, and
bracket access — so `alg("1 e31") == -alg("1 e13")` and `mv["e31"] == -mv["e13"]`.

## Clifford Conjugates

Tanga provides two distinct Clifford conjugates:

| Method | Definition | Metric-dependent? |
|--------|------------|-------------------|
| `a.conj()` | $\mathrm{rev}(B_k) · (−1)^r$ where $r$ = count of negative‑metric basis vectors | **Yes** |
| `a.grade_conj()` | $g\_\mathrm{invol}(B_k).\mathrm{rev}() = (−1)^{k(k+1)/2} · B_k$ | **No** — purely grade‑based |

`conj()` is tanga's original metric‑aware Clifford conjugate.  
`grade_conj()` is the galgebra‑style `ccon`, added for compatibility.

## Precision

The `Algebra` class has a `precision` property (default `1e-10`, settable at
construction or via assignment) that controls the numerical zero threshold for:

- `prune()` — removes coefficients with `abs(coeff) < precision` (or an explicit
  `tol` override)
- `is_zero()` — returns `True` when all `abs(coeff) < precision`
- `is_scalar()` — ignores non‑scalar blades whose `abs(coeff) < precision`

`prune()` additionally accepts an optional tolerance argument to override the
algebra default:

```python
mv = alg("1e-6 e1 + 1e-12 e2 + 2 e3")
mv.prune()        # uses alg.precision (default 1e-10) → keeps e1 and e3
mv.prune(1e-8)    # keeps only e3
```

```python
alg = Algebra(3, precision=1e-8)
alg.precision   # → 1e-8
alg.precision = 1e-12
```