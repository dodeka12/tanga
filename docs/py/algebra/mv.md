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
| `a \| b` | Inner (left-contraction) product |
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
| `a.ip(b)` | `a \| b` | Inner (left-contraction) product |
| `a.inv()` | — | Multiplicative inverse |
| `a.rev()` | — | Reverse $\tilde{a}$: reverses blade factor order |
| `a.conj()` | — | Clifford conjugate |
| `a.vp(b)` | — | Versor product: $a \cdot b \cdot \tilde{a}$ |
| `a.nvp(b)` | — | Normalized versor product: $a \cdot b \cdot a^{-1}$ |
| `a.grade(k)` | — | Grade projection: extract ⟨a⟩ₖ |
| `a.complement()` | — | Unsigned complement — see [Duals](duals.md) |
| `a.dual()` | — | Signed dual ★A = A · I⁺ — see [Duals](duals.md) |
| `a.ldual()` | — | Left dual I · A — see [Duals](duals.md) |
| `a.sp(b)` | — | Scalar product: scalar part of a * b |
| `a.project_to(b)` | — | Restrict a to the blade set of b |
| `a.blade_inverse()` | — | Proper blade inverse $A^{-1} = \tilde{A} / \mathrm{IP}(A, \tilde{A})$ |
| `a.blade_pseudo_inverse()` | — | Pseudo-inverse of a blade (uses conjugate instead of reverse) |
| `a.blade_factorize()` | — | Factorize blade into $k$ normalized grade-1 vectors |
| `a.blade_join(b)` | — | Join of two blades: smallest-grade blade containing both |
| `a.blade_factorize_versor()` | — | Factorize versor into `(scale, [factor_vectors])` |
| `a.project(blade)` | — | Project multivector onto a blade: $\mathrm{proj}_N(A)$ |
| `a.reject(blade)` | — | Reject multivector from a blade: $A - \mathrm{proj}_N(A)$ |
| `a.show(label, fmt)` | — | Print in algebra display basis |

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
| `a.prune()` | Removes near-zero coefficients in-place; returns `self` |
| `repr(a)` | Produces a human-readable expression string |

## Properties

| Property | Return type | Description |
|---|---|---|
| `a.scalar` | `float \| int` | Scalar coefficient |
| `a.mag2` | `float \| int` | Sum of squared coefficients |
| `a.mag` | `float` | sqrt of mag2 |
| `a.is_zero` | `bool` | True if all blades are zero |
| `a.is_scalar` | `bool` | True if only scalar blade is non-zero |

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