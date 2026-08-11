# Algebra Submodule

The `pytanga.algebra` submodule contains the core types that form the
foundation of the entire pytanga package.  The [`Algebra`](algebra.md) class
configures a geometric algebra — it defines the vector-space dimension, the
signature, the value type, and an optional integer modulus.  Calling an
`Algebra` instance creates an [`MV`](mv.md) (multivector) from dict, string,
or tuple input.  Multivectors support the full set of GA operations:
geometric, outer, and inner products, addition, inversion, reverse,
conjugate, and versor products.  Three complement/dual operations are
available: an unsigned (bitwise) [complement](duals.md), a signed Clifford
[dual](duals.md), and a [left dual](duals.md) (pseudoscalar on the left).
Integer algebras support
[modulus arithmetic](modulus.md) with half-space modular reduction.

```python
from pytanga.algebra import Algebra, MV, EProduct
```

## Reference

| Topic | Guide |
|-------|-------|
| `Algebra` class — construction, properties, GA operations, blade ops, display | [`Algebra`](algebra.md) |
| `MV` class — initialization, coefficient access, operators, utility methods | [`MV`](mv.md) |
| Duals — complement, signed `dual`, and left `ldual` operations | [Duals](duals.md) |
| Modulus arithmetic — integer algebras, `hmod`, multi-modulus pattern | [Modulus](modulus.md) |
| Galgebra bridge — bidirectional conversion between galgebra (sympy) and tanga (numeric) MVs | [Galgebra Bridge](galgebra_bridge.md) |

## Quick start

```python
from pytanga.algebra import Algebra

# Create a 3D Euclidean algebra
alg = Algebra(3, 0, "float64")

# Create multivectors from string expressions
a = alg("e1 + 2 e2")
b = alg("e2 + e3")

# Geometric product
print(a * b)

# Outer product
print(a ^ b)
```
