# Product Tensor

The **product tensor** is a rank‑3 `MVTensor` that encodes a bilinear geometric
algebra operation (geometric product, inner product, outer product) as a sparse
tensor of +1, -1, and 0 entries.  Multiplying two multivector tensors through
the product tensor performs the GA operation via `np.einsum`.

```python
from pytanga.tensor.product import product_tensor
```

## `product_tensor()`

```python
product_tensor(
    a_mask: BladeMask,
    b_mask: BladeMask,
    c_mask: BladeMask | None = None,
    *,
    product: EProduct = EProduct.GP,
    left: bool = True,
    a_inv: EInv = EInv.ID,
    b_inv: EInv = EInv.ID,
    c_inv: EInv = EInv.ID,
) -> MVTensor
```

The returned `MVTensor` has masks `(c_mask, a_mask, b_mask)` — axis 0
corresponds to the result blade, axis 1 to the left operand A, and axis 2 to
the right operand B.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `a_mask` | *(required)* | Blade mask of the A operand |
| `b_mask` | *(required)* | Blade mask of the B operand |
| `c_mask` | `None` | Blade mask of the result C.  Auto‑computed from *a_mask* and *b_mask* if `None`. |
| `product` | `EProduct.GP` | GA operation: `GP` (geometric), `IP` (inner), or `OP` (outer) |
| `left` | `True` | If `True` (default): `A ∘ B = C`.  If `False`: `B ∘ A = C`. |
| `a_inv` | `EInv.ID` | Involution on A blades: `ID`, `REV` (reverse), or `CONJ` (conjugate) |
| `b_inv` | `EInv.ID` | Involution on B blades |
| `c_inv` | `EInv.ID` | Involution on the result multivector |

The product tensor is computed on the C++ side for efficiency and cached once
per mask combination.

```python
from pytanga import Algebra, BladeMask
from pytanga.basis import BasisE3
from pytanga.tensor import MVTensor
from pytanga.tensor.product import product_tensor
from pytanga.enums import EProduct

alg = BasisE3()
full = BladeMask.full(alg)                         # 8 blades

# Geometric product tensor
O_gp = product_tensor(full, full)                  # shape 8×8×8

# Outer product tensor
O_op = product_tensor(full, full, product=EProduct.OP)

# Reverse on the A operand:  Ã * B = C
O_rev = product_tensor(full, full, a_inv=EInv.REV)
```

## Using the product tensor

The product tensor `O` (masks `(c, a, b)`) is used with `contract()` or with
`MVLabeledTensor` multiplication:

### With `contract()` (explicit subscripts)

```python
from pytanga.tensor.ops import contract
from pytanga.tensor.convert import to_tensor
from pytanga.mv_utils import _as_mv

mv_a = _as_mv(alg, "e1")
mv_b = _as_mv(alg, "e2")
A = to_tensor(mv_a, mask=full)            # shape 8
B = to_tensor(mv_b, mask=full)

C = contract("kij,i,j->k", O_gp, A, B)   # shape 8
# C encodes the multivector e1 * e2 = e12
```

### With labeled tensors

```python
C = O_gp["kij"] * A["i"] * B["j"]         # "k*" — same as above
```

The labels `"k"`, `"i"`, `"j"` map to the product tensor's axes: result (c),
left operand (a), right operand (b).

## Helper: `product_tensor_rev()` and `product_tensor_conj()`

Diagonal matrices encoding the reverse / conjugate sign per blade:

```python
from pytanga.tensor.product import product_tensor_rev, product_tensor_conj

R_rev  = product_tensor_rev(full)          # shape 8×8, masks (full, full)
R_conj = product_tensor_conj(full)         # shape 8×8, masks (full, full)
```

These are square `MVTensor` instances with ±1 on the diagonal.  Use them to
apply an involution to a multivector tensor:

```python
A_rev = contract("ij,j->i", R_rev, A)     # Ã
```

## Examples

### Single geometric product via labeled tensors

```python
from pytanga import Algebra, BladeMask
from pytanga.basis import BasisE3
from pytanga.tensor.product import product_tensor
from pytanga.tensor.convert import to_tensor
from pytanga.mv_utils import _as_mv

alg = BasisE3()
full = BladeMask.full(alg)

O = product_tensor(full, full)                     # Ô_{kij}
a = to_tensor(_as_mv(alg, "1 + 2e1"), mask=full)
b = to_tensor(_as_mv(alg, "e2 + e3"), mask=full)

result = O["kij"] * a["i"] * b["j"]               # labels "k*"
```

### Batch product with element‑wise batch axis

```python
batch = 10
A_batch = MVLabeledTensor.zeros("i*n_", [full, batch])
B_batch = MVLabeledTensor.zeros("j*n_", [full, batch])

# Fill A_batch, B_batch ...
C_batch = O["kij"] * A_batch["in_"] * B_batch["jn_"]
# labels "k*n_", shape (8, 10)
```

### Inner product

```python
O_ip = product_tensor(full, full, product=EProduct.IP)
result = O_ip["kij"] * a["i"] * b["j"]
```
