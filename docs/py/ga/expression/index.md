# Expression System

The `pytanga.expression` package provides a lightweight symbolic layer for
composing geometric-algebra equations where only a few elements change during
an animation or optimization.

- **`Variable`** — a named slot with a fixed
  [`BladeMask`](../blade-mask/index.md) (its "type").
- **`Expression`** — a reduced product tensor with one axis per variable
  occurrence and one output axis, built by combining variables with constant
  multivectors.  A variable may appear up to `MAX_DEGREE` times per term
  (`v * v`).
- **`AffineExpression`** — a sum of `Expression` terms that could not be merged
  into a single tensor, produced by adding/subtracting differently-shaped
  expressions or constants.

Evaluate an expression by binding variables to multivectors:

```python
from pytanga import BladeMask, Variable
from pytanga.basis import BasisE3

alg = BasisE3()
v = Variable("V1", BladeMask.full(alg))
a = alg.multivector({"e1": 2.0})

e = v * a
e(V1=alg.multivector({"e1": 1.0}))  # -> e1 * (2 e1) = 2
```

See [usage](usage.md) for the full API, and the `py/examples/ga/expression/`
scripts for runnable examples.
