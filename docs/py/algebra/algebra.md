# The `Algebra` Class

The `Algebra` class is the central configuration object in pytanga.  It
defines a geometric algebra $G(d, s)$ with dimension $d$, signature $s$,
and a value type (`float64`, `int64`, etc.).  On first construction for a new
combination of parameters, the C++ binding is compiled and cached (~5–20 s).
Subsequent constructions load the cached binary (~ms).

```python
from pytanga.algebra import Algebra
```

## Construction

An `Algebra` is created by specifying the vector-space dimension, the
signature, and the data type.  For convenience, dedicated `Basis` subclasses expose named blades and
factory methods for common geometries.

```python
# G(3,0) — 3D Euclidean
alg = Algebra(3, 0, "float64")

# G(4,1) — 4D with negative-signature basis vector
alg = Algebra(4, 0b10000, "float64")
# bit 4 set → e5 squares to -1

# PGA3 — 5D with null-vector embedding
alg = Algebra(5, 0b10000, "float64")

# From a Basis subclass (named blades + factory methods)
from pytanga.basis import BasisE3, BasisP3, BasisPGA3
alg = BasisE3("float64")
alg = BasisP3("float64")
alg = BasisPGA3("float64")
```

The signature bitmask encodes which basis vectors square to $-1$: bit `k`
set means $e_{k+1}^2 = -1$.  A signature can also be passed as a tuple of
1-based indices, e.g. `(1, 4, 5)` has the same effect as `0b11001`.

Available Basis subclasses: `BasisE2`, `BasisE3`, `BasisP2`, `BasisP3`,
`BasisN2`, `BasisN3`, `BasisPGA2`, `BasisPGA3`. These expose named blades
as attributes and provide convenience factory methods.

## Properties

These properties give read-only access to the algebra's configuration:

| Property | Type | Description |
|---|---|---|
| `dim` | `int` | Vector-space dimension |
| `sig` | `int` | Signature bitmask |
| `dtype` | `str` | `"float64"`, `"float32"`, `"int64"`, or `"int32"` |
| `modulus` | `int \| None` | Stored modulus for integer algebras |
| `algebra_dim` | `int` | `2**dim` — total number of basis blades |
| `pseudoscalar_id` | `int` | Blade bitmask of the pseudoscalar $I$ |
| `rng` | `random.Random` | Random number generator seeded from construction argument |
| `print_fmt` | `str` | Python format spec for coefficient display (default `'.4g'`) |

## Creating Multivectors

Calling an `Algebra` instance (or equivalently `alg.multivector(...)`) creates
a multivector.  Five input forms are accepted:

```python
# 1. Zero multivector
a = alg()

# 2. Dict with integer keys — raw blade bitmasks
a = alg({1: 1.0, 3: -0.5})           # 1.0·e1 − 0.5·e12

# 3. Dict with string keys — blade names
a = alg({"e1": 1.0, "e12": -0.5})

# 4. Dict with tuple keys — 1-based vector index tuples
a = alg({(2,): 1, (1, 3): 2})        # 1·e2 + 2·e13

# 5. String expression — parsed sum of signed terms
a = alg("2.3 + 4 e2 - 5 e1,2")       # comma-separated indices for dim > 9
```

String blade names use `e1`, `e2`, … for single-index blades, `e12` or
`e1,2` for multi-index blades (comma form required for dim > 9), `s` for
the scalar, and `I` for the pseudoscalar.

## GA Operations

All primitive GA operations are methods on `Algebra` that take two `MV`
arguments.  Most have corresponding operator overloads on `MV` for
convenience:

```python
c = alg.gp(a, b)       # geometric product a * b   (also a * b)
c = alg.op(a, b)       # outer product a ^ b       (also a ^ b)
c = alg.ip(a, b)       # inner product a | b       (also a | b)
c = alg.add(a, b)      # addition a + b            (also a + b)
c = alg.sub(a, b)      # subtraction a - b         (also a - b)
c = alg.neg(a)         # negation                  (also -a)
c = alg.scale(a, s)    # scalar scaling            (also s * a)
```

### Involutions

The `rev` and `conj` methods apply blade-level involutions:

```python
r = alg.rev(a)         # reverse: rev(blade) = (-1)^(k(k-1)/2) · blade
c = alg.conj(a)        # Clifford conjugate: conj(blade) = rev(blade) · (-1)^r
```

The reverse negates blades of grades 2 and 3 mod 4.  The conjugate adds an
extra sign factor $(-1)^r$ where $r$ is the count of negative-metric basis
vectors in the blade.

For convenience, `MV` also exposes `a.rev()` and `a.conj()` which delegate
to the parent algebra.

### Miscellaneous operations

```python
scalar = alg.scalar(a)         # scalar coefficient
grade_k = alg.grade_proj(a, k) # ⟨A⟩_k — grade-k part
mag_sq = alg.magnitude_sq(a)   # sum of squared coefficients
magnitude = alg.magnitude(a)   # sqrt of magnitude_sq
is_zero = alg.is_zero(a)       # True if all coefficients zero
is_scalar = alg.is_scalar(a)   # True if only scalar blade non-zero
comp_a = alg.complement(a)     # unsigned complement — see [Duals](duals.md)
dual_a = alg.dual(a)           # signed dual ★A = A · I⁺ — see [Duals](duals.md)
ldual_a = alg.ldual(a)         # left dual I · A — see [Duals](duals.md)
sp = alg.sp(a, b)              # scalar product: scalar part of a * b

inv_a = alg.inv(a)             # multiplicative inverse
inv_a = alg.inv(a, 97)         # modular inverse (integer algebras only)
```

### Versor product

The versor product $R \cdot v \cdot \tilde{R}$ applies a versor (rotor /
reflector) to a multivector:

```python
rotated = alg.vp(R, v)         # R * v * rev(R)
rotated = alg.nvp(R, v)        # R * v * inv(R) — magnitude-independent
```

`vp` uses the reverse (standard for unit versors).  `nvp` uses the algebraic
inverse, making the result independent of the versor's magnitude.

### Blade operations

These operate on pure blades (homogeneous multivectors of a single grade):

```python
alg.blade_inverse(blade)          # inverse of a blade
alg.blade_pseudo_inverse(blade)   # pseudo-inverse (uses conjugate)
alg.blade_factorize(blade)        # → list of k grade-1 vectors
alg.blade_join(a, b)              # smallest blade containing both
alg.blade_project(a, blade)       # project a onto blade
alg.blade_reject(a, blade)        # reject a from blade
```

### Integer modular operations

For integer-dtype algebras, explicit `_mod` variants apply modular reduction
per operation.  Full details in [Modulus](modulus.md):

```python
alg.gp_mod(a, b, 97)             # geometric product modulo 97
alg.op_mod(a, b, 97)             # outer product with reduction
alg.ip_mod(a, b, 97)             # inner product with reduction
alg.reduce(a, 97)                # apply hmod coefficient-wise
```

### Display

```python
alg.show(a, "label")             # print with label
s = alg.show_str(a, "result")    # return string instead
```

If the algebra is a `Basis` subclass, `show()` uses a named display basis
(e.g. `einf`, `eo` for conformal algebras).