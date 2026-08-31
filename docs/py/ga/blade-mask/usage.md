# Usage in Pipelines

`BladeMask` serves as the foundational type used by `MVTensor`, `MVMatrix`,
`MVProductMatrix`, and the solver functions.  This page explains how each
system uses blade masks and how mask compatibility is enforced.

## In MVTensor

Each axis of an `MVTensor` carries a `BladeMask` (or `None` for batch axes).
The mask determines:
- How many elements are on that axis (`len(mask)`).
- Which blade each position along the axis represents.
- Compatibility checks when two tensors are aligned (contraction, broadcast).

```python
from pytanga.tensor import MVTensor
mask = BladeMask.full(alg)

t = MVTensor.zeros([mask, mask, mask])    # each axis = 8 elements
# t.masks = (mask, mask, mask)
```

When two `MVTensor` axes align (e.g. in tensor contraction), both must carry
the same mask or both `None`.  A mask on one axis with `None` on the other
is rejected — the semantics are ambiguous.

## In MVMatrix

`MVMatrix` wraps a 2‑D numpy array with a single `row_mask`:

```python
from pytanga.matrix import MVMatrix

mat = MVMatrix(data=np.zeros((8, 3)), row_mask=full)
# 8 rows (one per blade), 3 columns (3 multivectors)
```

The `row_mask` maps each row index to a blade ID.  When converting between
`MV` and `MVMatrix`, the mask defines the ordering:
- `to_matrix(mv, mask)` fills rows in `mask.ids` order.
- `from_matrix(mat)` reconstructs an `MV` using `mat.row_mask`.

## In MVProductMatrix

`MVProductMatrix` carries three masks, one per tensor axis:

| Mask | Axis | Meaning |
|------|------|---------|
| `a_mask` | dim 0 | A‑subspace (list of MVs, or blades of one MV) |
| `c_mask` | dim 1 | Output subspace — determines rows of each matrix |
| `b_mask` | dim 2 | Unknown X subspace — determines columns of each matrix |

```python
from pytanga.matrix.product import product_matrix

M = product_matrix(A, a_mask=a_mask, b_mask=b_mask, c_mask=c_mask)
# M.a_mask, M.b_mask, M.c_mask
```

The three masks together define the dimensions of the linear system:
`(|a_mask|, |c_mask|, |b_mask|)`.  When `|c_mask| == |b_mask|`, the system
is square.

## In the solver pipeline

The solver pipeline uses blade masks to determine the subspace of the
unknown.  See [Blade Mask Pipeline](../solver/blade-mask-pipeline.md) for
the full description.  In summary:

```
a_mask = BladeMask(A)                           # blades of known operand
c_mask = BladeMask(Y)                           # blades of result
b_mask = inverse_blade_mask(a_mask, c_mask)      # blades of unknown
```

## Compatibility enforcement

Every operation that aligns two axes checks that both masks:
1. **Belong to the same algebra** (or at least one is `None` for batch axes).
2. **Have the same blade IDs** (same set, same order).
3. **Have the same length** — the axis sizes must match.

A mask of `None` on both axes is compatible (both are batch axes).  A mask
of `None` on one axis with a concrete `BladeMask` on the other is **not**
compatible — the framework cannot know how to align a batch axis with a
blade‑specific axis.

These checks prevent silent bugs where blades from different algebras or
subspaces are accidentally aligned.

```python
# This raises ValueError — a_mask ≠ b_mask
mask_a = BladeMask(alg, [0, 1, 2])
mask_b = BladeMask(alg, [1, 2, 3])
# mask_a.intersection(mask_b) succeeds (set op)
# aligning tensor axes with these masks fails (compatibility check)
```
