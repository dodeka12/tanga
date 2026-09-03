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
- **`DataArray`** — a labeled data container (one `BladeMask` per blade axis and
  a `str` per counting axis) used to bind variables and reduce counting axes.
  See [DataArray](data-array.md).

Evaluate an expression by binding variables to multivectors:

```python
import numpy as np
from pytanga import BladeMask, Variable, DataArray
from pytanga.basis import BasisE3

E3 = BasisE3()
vec_mask = BladeMask(E3, grades=[1])  # Mask for grade-1 blades (vectors) in E3

# Define a variable v of grade-1 (vector) in E3
v = Variable("v", vec_mask)
a = E3("e12 + 3 e23")

# Build the expression e = v * a
e = v * a

# Evaluate the expression for a specific value of v
e_vals = e(v=E3("2 e1"))  # -> (2 e1) * (e12 + 3 e23) = 2 e2 + 6 I
print(e_vals)

# Combine with a DataArray to evaluate the expression for multiple values of v
v_data = np.random.rand(5, 3)  # Random values for v in R^3
# Evaluate the expression for multiple values of v, 
# giving a name for the index dimension and a mask for vectors.
e_data = e(v=DataArray(v_data, masks=("v_idx", vec_mask)))  # Evaluate
# This results in a list of multivectors.
print(e_data)
```

See [usage](usage.md) for the full API, [DataArray](data-array.md) for the data
container and its use cases, [weighted sum example](example-weighted-sum.ipynb) for
a worked NumPy grid example, and the `py/examples/ga/expression/` scripts for
runnable examples.
