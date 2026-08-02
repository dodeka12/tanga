# MVProductMatrix

`MVProductMatrix` is a 3‑D tensor encoding one product matrix per blade of an
`a_mask` subspace.  It is the return type of `product_matrix` and is used
internally by the solver pipeline.

```python
from pytanga.matrix import MVProductMatrix
```

## Construction

`MVProductMatrix` is created by the `product_matrix` function:

```python
from pytanga.matrix.product import product_matrix

M = product_matrix(A, a_mask=a_mask, b_mask=b_mask, c_mask=c_mask)
# M is an MVProductMatrix; shape (|a_mask|, |c_mask|, |b_mask|)
```

Each slice `M.data[i, :, :]` is the `(|c_mask| × |b_mask|)` product matrix
for multivector `i` of the A‑subspace.

## Data shape

The 3‑D tensor has axes:

| Axis | Dimension | Mask | Meaning |
|------|-----------|------|---------|
| 0 | `|a_mask|` | `a_mask` | Which multivector of the A‑subspace |
| 1 (middle) | `|c_mask|` | `c_mask` | Output blade rows |
| 2 (last) | `|b_mask|` | `b_mask` | Unknown X blades (columns) |

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `data` | `np.ndarray` | 3‑D array of shape `(n_mvs, \|c_mask\|, \|b_mask\|)` |
| `a_mask` | `BladeMask` | First axis — A‑subspace |
| `b_mask` | `BladeMask` | Last axis — subspace of unknown X |
| `c_mask` | `BladeMask` | Middle axis — output subspace |
| `n_mvs` | `int` | Number of multivectors encoded (= `\|a_mask\|`) |
| `shape` | `tuple` | `data.shape` |
| `product` | `EProduct` | `GP`, `IP`, or `OP` |
| `left` | `bool` | `True` = A ∘ X, `False` = X ∘ A |
| `left_inv` | `EInv` | Involution on left operand |
| `right_inv` | `EInv` | Involution on right operand |
| `algebra` | `Algebra` | From `b_mask` |

## Matrix multiplication pattern

A standard numpy matrix product with a single‑column `MVMatrix` contracts the
last axis and broadcasts over the first:

```python
from pytanga.matrix.product import product_matrix
from pytanga.matrix.convert import to_matrix

M = product_matrix(A, a_mask=..., b_mask=b_mask, c_mask=c_mask)
V = to_matrix(X, mask=b_mask)                    # shape (|b|, 1)

result = np.matmul(M.data, V.data)               # → (|a_mask|, |c_mask|, 1)
result = result.squeeze(-1).T                    # → (|c_mask|, |a_mask|)
# Each column of result is A_i ∘ X for one MV of a_mask
```

For a single MV, `|a_mask| == 1` and `M.data[0]` is the familiar 2‑D product
matrix.

## Examples

```python
from pytanga import Algebra, BladeMask
from pytanga.matrix.product import product_matrix
from pytanga.enums import EInv

alg = Algebra.from_name("E3")
full = BladeMask.full(alg)
vectors = BladeMask(alg, grades=[1])

A = alg({"e1": 2.0, "e2": -3.0})

# Product matrix for one MV
M = product_matrix(A, a_mask=BladeMask(A),
                   b_mask=vectors, c_mask=full)
# M.data[0] is (8×3)

# Outer product
M_op = product_matrix(A, a_mask=BladeMask(A),
                      b_mask=full, c_mask=full, product='op')

# Batch: product matrices for a list of MVs
points = [alg.random_mv(rng=i) for i in range(5)]
M_arr = product_matrix(points, b_mask=full, c_mask=full)
# M_arr.data.shape == (5, 8, 8)