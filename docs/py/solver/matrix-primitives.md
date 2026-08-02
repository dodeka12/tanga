# Matrix Primitives

The solver module exposes low‑level functions that convert multivectors
to/from matrices and build product matrices.  These are used internally by
the high‑level solvers, but are also available for step‑by‑step workflows.

```python
from pytanga.matrix.product import product_matrix
from pytanga.matrix.convert import to_matrix, from_matrix
```

## `to_matrix` — MV → column vector(s)

Converts one or more multivectors into an `MVMatrix` with rows ordered by
the given `BladeMask`:

```python
# Single MV → (len(mask), 1) column vector
mat = to_matrix(mv, mask=full)

# List of MVs → (len(mask), n_mvs) matrix
mat = to_matrix([mv1, mv2, mv3], mask=full)
```

Each column is the coefficient vector of one MV, with coefficients ordered
by `mask.ids`.  Axes that the MV doesn't occupy become zero entries.

```python
full = BladeMask.full(alg)                         # 8 blades
mv = alg({"e1": 2.0, "e2": -1.0})
mat = to_matrix(mv, mask=full)                     # shape (8, 1)
print(mat.data[full.index(1)])                     # 2.0  (e1)
print(mat.data[full.index(2)])                     # -1.0 (e2)
```

## `from_matrix` — column vector(s) → MV

The reverse operation: converts an `MVMatrix` (or its raw numpy array)
back to `MV` or `list[MV]`:

```python
# Single column → MV
mv = from_matrix(mat)

# Multiple columns → list[MV]
mvs = from_matrix(mat)
```

The `row_mask` of the matrix tells the conversion which blades each row
corresponds to.

## `product_matrix` — build the linear system

```python
M = product_matrix(A, a_mask=..., b_mask=..., c_mask=...)
M = product_matrix(A, a_mask=a_mask, b_mask=b_mask, c_mask=c_mask,
                   product='gp',                # 'gp' | 'ip' | 'op'
                   left=True)                    # A ∘ X vs X ∘ A
```

Returns an `MVProductMatrix` — a 3‑D tensor of shape
`(|a_mask|, |c_mask|, |b_mask|)`.  For a single MV, `|a_mask| == 1` and
`M.data[0]` is the familiar 2‑D product matrix.

The product matrix encodes the GA operation as a linear map:
`M.data[0] @ vec(X) = vec(A ∘ X)`.  Each entry is +1, -1, or 0, computed
on the C++ side.

**Parameters**:
- `A` — the fixed‑coefficient MV, or list of MVs.
- `a_mask` — the A‑subspace (auto‑computed if omitted).
- `b_mask` — the subspace of the unknown X (columns).
- `c_mask` — the output subspace (rows).
- `product` — which GA product (`GP`, `IP`, `OP`).
- `left` — whether `A ∘ X` (True) or `X ∘ A` (False).

## Putting it together — manual solve

```python
from pytanga import BladeMask
from pytanga.blade_mask.predict import inverse_blade_mask, product_blade_mask
from pytanga.matrix.product import product_matrix
from pytanga.matrix.convert import to_matrix, from_matrix
from pytanga.matrix import MVMatrix
import numpy as np

A = alg({"e1": 1.0, "e2": -2.0, 0: 0.5})
Y = alg(1.0)

# Determine the blade masks
a_mask = BladeMask(A)
c_mask = BladeMask(Y)
b_mask = inverse_blade_mask(a_mask, c_mask)

# Build the product matrix and RHS
M = product_matrix(A, a_mask=a_mask, b_mask=b_mask, c_mask=b_mask)
y_vec = to_matrix(Y, mask=M.c_mask)

# Solve
x_arr = np.linalg.solve(M.data[0], y_vec.data)   # M.data[0] is (|c|, |b|)
X = from_matrix(MVMatrix(x_arr, M.b_mask))
print(X)