# Tensor Operations

The `pytanga.tensor` submodule provides a tensor layer for working with
multi-dimensional arrays of multivector components.  [`MVTensor`](mvtensor.md)
is a plain N‑D tensor where each axis carries a `BladeMask` (or `None` for
batch axes).  [`MVLabeledTensor`](labeled-tensor.md) wraps an `MVTensor` with
per‑axis label strings, enabling label‑driven arithmetic — multiplication
infers Einsum‑style contractions from shared labels, addition broadcasts over
non‑matching labels, and arrow syntax (`"ij->ji"`, `"->nij"`) reorders axes.
The [`product_tensor`](product-tensor.md) function builds the 3‑D tensor
encoding a GA product from blade masks.

```python
from pytanga.tensor import MVTensor, MVLabeledTensor
```

## Reference

| Topic | Guide |
|-------|-------|
| `MVTensor` — slicing, factories, scalar ops, NumPy interop | [MVTensor](mvtensor.md) |
| `MVLabeledTensor` — labels, `*` contraction, `+`/`-` broadcast, `/` division, `->` transpose | [Labeled Tensors](labeled-tensor.md) |
| `iter_labels` — iterating over a label for per‑element computation | [Label Iterator](iterator.md) |
| `product_tensor()` — building the 3‑D product tensor from blade masks | [Product Tensor](product-tensor.md) |

## Quick start

```python
from pytanga import Algebra, BladeMask
from pytanga.basis import BasisE3
from pytanga.tensor import MVTensor
from pytanga.tensor.product import product_tensor

alg = BasisE3()
mask = BladeMask.full(alg)       # 8 blades

# A rank-1 tensor holding one multivector
A = MVTensor.zeros([mask])

# A product tensor O_{kij} for the geometric product
O = product_tensor(mask, mask)  # shape 8×8×8

# Label the axes and perform a label‑driven GP
C = (O["kij"] * A["i"] * A["j"])["->k"]
```
