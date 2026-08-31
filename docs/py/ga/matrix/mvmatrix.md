# MVMatrix

`MVMatrix` wraps a 2‑D numpy array with a `BladeMask` labelling its rows.
Each column stores the coefficients of one multivector, ordered by the
`row_mask`.

```python
from pytanga.matrix import MVMatrix
```

## Construction

```python
import numpy as np
from pytanga import BladeMask

mask = BladeMask.full(alg)                     # 8 blades

# Single multivector — column vector
m = MVMatrix(data=np.zeros((len(mask), 1)), row_mask=mask)

# Batch of 3 multivectors
m = MVMatrix(data=np.zeros((len(mask), 3)), row_mask=mask)
```

Validation at construction time checks that `data.ndim == 2` and
`data.shape[0] == len(row_mask)`.

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `data` | `np.ndarray` | Shape `(len(row_mask), n_cols)` |
| `row_mask` | `BladeMask` | Ordered blade IDs labelling each row |
| `shape` | `tuple[int, ...]` | `data.shape` |
| `n_cols` | `int` | Number of multivectors (columns) |
| `is_single` | `bool` | `True` when exactly one column |
| `algebra` | `Algebra` | From `row_mask` |

## Conversion

`MVMatrix` is created and consumed by the matrix conversion functions:

```python
from pytanga.matrix.convert import to_matrix, from_matrix

# MV → MVMatrix
mat = to_matrix(mv, mask=full)                  # single MV → (8, 1)
mat = to_matrix([mv1, mv2, mv3], mask=full)     # list → (8, 3)

# MVMatrix → MV (or list[MV])
mv = from_matrix(mat)                           # single col → MV
mvs = from_matrix(mat)                          # multi‑col → list[MV]
```

## Relationship to product matrices

Multiplying an `MVProductMatrix.data` with an `MVMatrix` performs the
corresponding GA operation in matrix form:

```python
from pytanga.matrix.product import product_matrix
from pytanga.matrix.convert import to_matrix

M = product_matrix(A, b_mask=b_mask, c_mask=c_mask)   # MVProductMatrix
V = to_matrix(X, mask=b_mask)                          # MVMatrix

result = np.matmul(M.data, V.data)                     # (|a|, |c|, 1)
result = result.squeeze(-1).T                           # (|c|, |a|)
```

## Examples

```python
from pytanga import Algebra, BladeMask
from pytanga.basis import BasisE3
from pytanga.matrix import MVMatrix
import numpy as np

alg = BasisE3()
full = BladeMask.full(alg)

# Build a column vector for one multivector
v = MVMatrix(data=np.random.randn(8, 1), row_mask=full)

# Build a batch of 5 multivectors
batch = MVMatrix(data=np.random.randn(8, 5), row_mask=full)
print(batch.n_cols)                            # 5
print(batch.is_single)                         # False
```
