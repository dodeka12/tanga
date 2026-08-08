# Matrix Operations

The `pytanga.matrix` submodule bridges geometric algebra multivectors with
linear algebra.  [`MVMatrix`](mvmatrix.md) wraps a 2‑D numpy array whose rows
are labelled by a [`BladeMask`](../blade-mask/index.md) — each column stores
one multivector's coefficient vector.  [`MVProductMatrix`](mvproductmatrix.md)
is a 3‑D tensor encoding one product matrix per blade of a subspace, built by
the `product_matrix` function and used internally by the equation solvers in
`pytanga.solver`.  Blade masks label every row and column, preventing
mask‑mismatch bugs at every axis alignment point.

```python
from pytanga.matrix import MVMatrix, MVProductMatrix
```

## Reference

| Topic | Guide |
|-------|-------|
| `BladeMask` — construction, membership, union/intersection, grade filtering | [BladeMask](../blade-mask/index.md) |
| `MVMatrix` — row‑labelled coefficient matrix, `to_matrix`, `from_matrix`, batch support | [MVMatrix](mvmatrix.md) |
| `MVProductMatrix` — 3‑D tensor, `product_matrix`, reverse/conjugate matrices | [MVProductMatrix](mvproductmatrix.md) |

## Quick start

```python
from pytanga import Algebra, BladeMask
from pytanga.basis import BasisE3
from pytanga.matrix import MVMatrix
from pytanga.matrix.product import product_matrix
import numpy as np

alg = BasisE3()
full = BladeMask.full(alg)             # all 8 blades

# Create a column vector for one multivector
v = MVMatrix(data=np.zeros((8, 1)), row_mask=full)

# Build a product matrix for a random multivector
A = alg.random_mv(rng=42)
a_mask = BladeMask(A)
b_mask = BladeMask(alg, grades=[1])   # vector subspace

M = product_matrix(A, a_mask=a_mask, b_mask=b_mask, c_mask=a_mask)
# M.data[0] is the (|a_mask|×|b_mask|) 2‑D product matrix