# MVTensor

`MVTensor` is the fundamental N‑D tensor class in pytanga.  Each axis carries a
`BladeMask` (mapping data positions to specific GA blades) or `None` for
batch/counting axes without blade semantics.

```python
from pytanga.tensor import MVTensor
```

## Construction

### Direct

```python
import numpy as np
from pytanga import BladeMask

mask = BladeMask.full(algebra)  # all blades of an algebra

# Rank‑1 — one multivector
t = MVTensor(
    data=np.zeros(len(mask)),
    masks=(mask,),
)

# Rank‑3 — product tensor: result × left operand × right operand
O = MVTensor(
    data=np.zeros((len(mask), len(mask), len(mask))),
    masks=(mask, mask, mask),
)
```

`masks` is a tuple with one entry per axis.  Each entry is either a `BladeMask`
or `None`.  Validation at construction checks that `len(masks) == data.ndim` and
that each mask's length equals the corresponding axis size.

### Factory: `MVTensor.zeros`

Create a zero-initialised tensor from a list of specifiers:

```python
# spec = BladeMask → axis uses that mask, size = len(mask)
# spec = int → axis is a batch axis (mask=None), size = spec

t = MVTensor.zeros([mask, 5, mask])
# t.masks → (mask, None, mask)
# t.shape → (len(mask), 5, len(mask))
```

`dtype` defaults to `float64`.  `MVTensor.zeros_like(other)` creates a
same‑shape tensor matching *other*.

```python
# Batch of 10 multivectors, each on the first 4 blades
sub = BladeMask(alg, [0, 1, 2, 3])
batch = MVTensor.zeros([10, sub])          # shape 10×4
clone = MVTensor.zeros_like(batch)          # same shape and masks
```

Invalid specifiers (non‑`BladeMask`, non‑`int`) raise `TypeError`.

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `data` | `np.ndarray` | Raw data array |
| `masks` | `tuple[BladeMask\|None, ...]` | One mask per axis |
| `shape` | `tuple[int, ...]` | `data.shape` |
| `algebra` | `Algebra` | Inferred from the first non‑`None` mask |

## Indexing (`__getitem__`)

### Numeric indexing

Slice, integer, and tuple indexing is forwarded to the underlying `data` array
while attempting to preserve mask metadata:

| Key type | Behaviour |
|----------|-----------|
| `slice` | Preserves the axis.  Masks are filtered to match the slice range. |
| `int` | Collapses the axis.  The corresponding mask is dropped. |
| `np.array` / `list` (fancy) | Falls back to a raw `np.ndarray` — masks are too ambiguous to preserve. |
| `None` (newaxis) | Inserts a `None` mask at that position. |

```python
mv_tensor = MVTensor.zeros([mask])          # rank-1, 8 elements

first_four = mv_tensor[0:4]                 # slice → MVTensor, shape (4,)
middle     = mv_tensor[2]                   # int → scalar (0‑d ndarray)
selected   = mv_tensor[[0, 3, 5]]           # fancy → np.ndarray
```

### String indexing — creating a labeled tensor

Passing a string key creates an `MVLabeledTensor`:

```python
O = product_tensor(mask, mask)               # rank-3, shape 8×8×8
O_labeled = O["kij"]                         # MVLabeledTensor with labels "k*i*j*"
A_labeled = MVTensor.zeros([mask])["i"]      # MVLabeledTensor with labels "i*"
```

This is the entry point into label‑driven arithmetic (see
[Labeled Tensors](labeled-tensor.md)).  The string is canonicalised internally
— `"kij"` becomes `"k*i*j*"`.

## Scalar operations

| Method | Description |
|--------|-------------|
| `mul_scalar(s)` | Element‑wise `data * s` |
| `div_scalar(s)` | Element‑wise `data / s` |
| `rdiv_scalar(s)` | Element‑wise `s / data` |

All return a new `MVTensor` with the same masks.

```python
doubled = t.mul_scalar(2.0)
halved  = t.div_scalar(2.0)
reciprocal = t.rdiv_scalar(1.0)      # 1 / data
```

## Assignment

`MVTensor` has no `__setitem__` overload — label‑aware assignment is handled by
`MVLabeledTensor.__setitem__`.  Standard NumPy in‑place assignment works through
the `data` attribute:

```python
t.data[0:5] = np.arange(5)
```

## Relationship to product tensors

`MVTensor` is the return type of `product_tensor()` (see
[Product Tensor](product-tensor.md)).  The product tensor is a rank‑3
`MVTensor` with masks `(c_mask, a_mask, b_mask)` encoding a bilinear GA
operation as a sparse +-1/0 tensor.

## Examples

```python
from pytanga import Algebra, BladeMask
from pytanga.basis import BasisE3
from pytanga.tensor import MVTensor

alg = BasisE3()
full = BladeMask.full(alg)
sub  = BladeMask(alg, [0, 1, 2, 3])  # s, e1, e2, e3

# Zero-initialised batch
batch = MVTensor.zeros([10, sub])     # 10 multivectors, 4 blades each

# Slice
first_five = batch[0:5]               # shape (5, 4), masks=(None, sub)

# Scalar ops
scaled = batch.mul_scalar(3.0)

# Convert to labeled tensor for label‑driven arithmetic
labeled = batch["nm"]                 # labels "n*_*" (short form) → "n*_*" canon