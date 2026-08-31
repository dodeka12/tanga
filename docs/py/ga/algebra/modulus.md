# Modulus Arithmetic

pytanga supports **integer geometric algebras** with modular reduction for
lattice-based cryptography applications.

## Fixed modulus — `Algebra(…, modulus=p)`

When a `modulus` is set at construction time, every arithmetic operator
(`+`, `-`, `*`, scalar multiply) automatically applies half-space modular
reduction (`hmod`) after each operation.

See [`ga/algebra/modulus_algebra_single.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/ga/algebra/modulus_algebra_single.py).

```python
alg = Algebra(3, 0, dtype="int64", modulus=101)

e1 = alg("e1")
e2 = alg("e2")

# 60 > 50 → hmod(60, 101) = 60 - 101 = -41
result = 60 * e1
```

**Constraints**: `modulus` requires `dtype='int32'` or `dtype='int64'`.

## `hmod(v, p)` — half-space reduction

$$\text{hmod}(v, p) = \begin{cases} v & \text{if } v \le \lfloor p/2 \rfloor \\ v - p & \text{otherwise} \end{cases}$$

Coefficients are kept in the centred interval
$[-\lfloor(p-1)/2\rfloor,\, \lfloor(p-1)/2\rfloor]$.

## Explicit modulus per operation — two-modulus algebra

When the same algebra must operate under two different moduli (as in
NTRU-style geometric-algebra cryptosystems), create **one** algebra without
a fixed modulus and use the `_mod` method variants:

See [`ga/algebra/modulus_algebra_multi.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/ga/algebra/modulus_algebra_multi.py).

```python
alg = Algebra(3, 0, dtype="int64")   # no fixed modulus

e1 = alg("e1")
e2 = alg("e2")

P = 101
Q = 127

r_p = e1.gp_mod(e2, P)   # geometric product, reduced mod P
r_q = e1.gp_mod(e2, Q)   # same operands, different modulus
```

This maps to the C++ pattern:

| Python | C++ |
|--------|-----|
| `a.gp_mod(b, p)` | `GA::GP_Congruence(res, a, b, xModP)` |
| `a.reduce(p)` | `GA::Congruence(res, xModP)` |
| `a.inv(p)` | `GA::Inverse(res, a, xModP)` |

For further context on the modular inverse and the congruence maps that
underpin it, see the C++ documentation in
[docs/cpp/congruence.md](../../../cpp/congruence.md).

## Modular solver

Use `solve_mod` to solve linear equations modulo a prime:

```python
from pytanga.solver.solve import solve_mod

alg_i = Algebra(3, 0, dtype="int64")
A = alg_i({"e1": 3, "e2": 5, 0: 1})

X = solve_mod(A, 1, modulus=97, algebra=alg_i)   # A * X ≡ 1 (mod 97)
```

See [Equation Solving](../solver/index.md) for details.