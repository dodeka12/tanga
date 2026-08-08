# Labeled Tensors (`MVLabeledTensor`)

`MVLabeledTensor` wraps an `MVTensor` with per‑axis labels so that arithmetic
operations can be expressed entirely through label strings.  Labels determine
which axes are contracted, broadcast, or kept element‑wise — without manually
writing `np.einsum` subscripts.

```python
from pytanga.tensor import MVLabeledTensor
```

`MVLabeledTensor` is a frozen dataclass (`frozen=True`): labels are immutable
after construction.  Relabeling returns a new instance.

## Labels

### Syntax

Each axis is described by a **raw name** (a single letter `a–z`, `A–Z`)
followed by an optional **mode character**:

| Mode | Written as | Meaning |
|------|------------|---------|
| Contraction | `"i"` or `"i*"` | Axis can be summed over when the same name appears on two inputs.  This is the **default**. |
| Element‑wise | `"n_"` | Axis is never summed.  When the same element‑wise name appears on two inputs, the axes are aligned element‑wise in the output. |

A **label string** is the sequence of label pairs, e.g. `"k*i*j*"` for a
rank‑3 tensor.

### Short form and canonicalisation

Users can write compact label strings; they are normalised automatically:

| User writes | Canonical form |
|-------------|----------------|
| `"kij"` | `"k*i*j*"` |
| `"in_"` | `"i*n_"` |
| `"ij_n"` | `"i*j_n*"` |
| `"i*n_"` | `"i*n_"` (already canonical) |

Rules:
- A raw name without a following `_` or `*` gets `*` (contraction) by default.
- `_` must immediately follow a raw name — stray underscores are errors.
- Duplicate raw names on the same tensor are errors.

### Creating a labeled tensor

Two ways to obtain an `MVLabeledTensor`:

1. **From an `MVTensor`** via string indexing:
   ```python
   A = MVTensor.zeros([mask])["i"]          # labels "i*"
   O = product_tensor(mask, mask)["kij"]     # labels "k*i*j*"
   ```

2. **Factory constructors**:
   ```python
   Z = MVLabeledTensor.zeros("kij", [mask, mask, mask])
   Z = MVLabeledTensor.zeros_from_dict("in", {"i": mask, "n": 5})
   ```

## Arithmetic operations

### Multiplication (`*`) — contraction

Multiplication of two labeled tensors is **label‑driven contraction**.
Shared labels that are both contractible (`*`) are summed out.  All other
labels appear in the output.

```python
# e1 (blade 1) * e2 (blade 2) = e12 (blade 3)
O = product_tensor(mask, mask)               # Ô_{kij}
A = to_tensor(e1, mask=mask)["i"]            # A_i, shape 8
B = to_tensor(e2, mask=mask)["j"]            # B_j, shape 8

result = O["kij"] * A["i"] * B["j"]          # labels "k*"
```

The contraction algorithm:
1. Extract raw names from both tensors.
2. Find shared names.  If both are `*`, that axis is **contracted** (summed).
3. If either is `_` or the name is unique, the axis stays **element‑wise** in the output.
4. Build an einsum subscript automatically and delegate to `np.einsum`.

#### Contraction examples

| Expression | Einsum equivalent | Output labels |
|------------|-------------------|---------------|
| `A["i"] * B["j"]` | `"i,j->ij"` | `"i*j*"` |
| `A["ij"] * B["jk"]` | `"ij,jk->ik"` | `"i*k*"` |
| `O["kij"] * A["i"] * B["j"]` | `"kij,i,j->k"` | `"k*"` |
| `A["ij"] * B["kl"]` | `"ij,kl->ijkl"` | `"i*j*k*l*"` |

### Element‑wise (`_` suffix)

A shared label with mode `_` on **either** tensor prevents contraction.  The
axis is aligned element‑wise and appears in the output:

```python
A = MVLabeledTensor.zeros("in_", [mask, 5])   # 8×5
B = MVLabeledTensor.zeros("jn_", [mask, 5])   # 8×5

C = A["in_"] * B["jn_"]                       # labels "i*j*n_", shape 8×8×5
```

| Expression | Einsum | Contraction? | Output labels |
|------------|--------|-------------|---------------|
| `A["in_"] * B["jn_"]` | `"in,jn->ijn"` | No (`n` is `_` on both) | `"i*j*n_"` |
| `A["in_"] * B["jn"]` | `"in,jn->ijn"` | No (`n` is `_` on A) | `"i*j*n_"` |
| `A["in"] * B["jn_"]` | `"in,jn->ijn"` | No (`n` is `_` on B) | `"i*j*n_"` |

The mode `_` *wins* for the output label when exactly one input marks it as
element‑wise.

### Scalar multiplication

Plain `int` / `float` with a labeled tensor does element‑wise scaling:

```python
result = A["i"] * 2.0          # labels "i*"
result = 3.0 * A["i"]          # same
```

### Division (`/`)

Division computes an element‑wise reciprocal of the denominator then
multiplies:

```python
A["ij"] / B["jk"]     # → 1/B["jk"] (element‑wise) then A["ij"] * (1/B)["jk"]
A["i"] / 3.0          # scalar division, labels "i*"
6.0 / A["i"]          # scalar right‑division
```

### Addition (`+`) and subtraction (`-`)

Broadcast‑style addition/subtraction.  The output has the **union** of all
labels from both inputs (self first, then other's unique names).  Shared
axes must have compatible masks and the same length:

```python
A["ij"] + B["jk"]       # output labels "i*j*k*", broadcast on i, k
A["ij"] + B["ij"]       # direct element‑wise (same labels)
A["ij"] - B["ij"]       # direct element‑wise subtraction
```

Mismatched masks on a shared label raise `ValueError`.

## Relabeling and transposing (`__getitem__` on `MVLabeledTensor`)

### Relabel

`A["ijk"]` returns a new `MVLabeledTensor` with the given labels (the
underlying tensor data is **shared** — no copy):

```python
t = MVLabeledTensor.zeros("abc", [mask, 5, mask])
view = t["xyz"]                       # same data, new labels "x*y*z*"
```

### Transpose / reorder with arrow syntax

The `->` arrow in the key string acts as transpose:

```python
t["ij->ji"]       # swap axes 0↔1
t["kij->jki"]     # cyclic shift (0,1,2) → (1,2,0)
t["ijk->kji"]     # reverse all axes
```

Both sides of the arrow are validated: source labels must be a permutation of
the tensor's current labels, and the two sides must have the same set of names.
Transposes return **views** when possible (`np.transpose` with no data copy).

#### Inferred source: `"->target"`

When the source side is empty, it is inferred from the tensor's current
labels:

```python
# C has labels "i*j*n_" from a product
C = A["in_"] * B["jn_"]        # labels "i*j*n_"
D = C["->nij"]                 # labels "n_i*j*", shape 5×8×8
```

This is the key syntax for reordering a product result: write
`(A["in_"] * B["jn_"])["->nij"]` to reorder the temporary `"ijn"` labels to
`"nij"`.

#### Inferred target: `"source->"`

```python
t["ij->"]          # identity (keeps current order)
```

### Numeric indexing

Non‑string keys (slices, integers, tuples) are forwarded to the underlying
`MVTensor.__getitem__`, which preserves mask metadata for basic
slicing.  Fancy indexing falls back to a raw `np.ndarray`.

```python
t = MVLabeledTensor.zeros("ij", [mask, mask])
t_slice = t[0:4, 2:6]          # MVTensor with filtered masks
```

## Assignment (`__setitem__`)

`MVLabeledTensor` supports label‑aligned assignment between labeled tensors:

```python
A["kij"] = B["ji"]
```

Algorithm:
- Validate that the key's raw names match the target's label set.
- Align shared axes (validate mask compatibility and length).
- Broadcast `B`'s missing axes from `A`.
- Assign in‑place into `A.tensor.data`.

A plain `MVTensor` can also be assigned — its labels are inferred from the key:

```python
T = MVTensor.zeros([mask, mask, mask])
A["kij"] = T                     # T treated as having labels "kij"
```

Attempting to assign a tensor with extra labels not in the target raises
`ValueError`.

## Iterating over a label (`iter_labels`)

`iter_labels` is a free function that iterates synchronously over a named
axis across one or more labeled tensors, yielding slices with that axis
removed.  See the [Label Iterator](iterator.md) page for a full walkthrough
with examples of per‑element contraction, function application, and result
accumulation.

```python
from pytanga.tensor._labeled import iter_labels

A = MVLabeledTensor.zeros("n*a*", [5, mask])    # 5×8
for a_slice in iter_labels("n", A):
    # a_slice.labels == "a*", shape (8,)
    ...

A = MVLabeledTensor.zeros("n*a*", [5, mask])
B = MVLabeledTensor.zeros("n*b*", [5, 3])
for a_s, b_s in iter_labels("n", A, B):
    # a_s.labels == "a*", b_s.labels == "b*"
    result = a_s["a"] * b_s["b"]
```

- The iterated axis is **removed** (not kept as size‑1).
- All tensors must have the same axis length for that label.
- Works for both contraction (`*`) and element‑wise (`_`) axes.

## Mask compatibility

Any operation that aligns two axes (contraction, element‑wise multiply, add,
assignment) checks that the corresponding `BladeMask` instances are compatible:
same algebra and same blade ids.  An axis with `mask=None` (batch axis) is
compatible with any other `None` mask.

## Complete examples

### Geometric product via labeled tensors

```python
from pytanga import Algebra, BladeMask
from pytanga.basis import BasisE3
from pytanga.tensor import MVTensor, MVLabeledTensor
from pytanga.tensor.product import product_tensor
from pytanga.tensor.convert import to_tensor
from pytanga.mv_utils import _as_mv

alg = BasisE3()
mask = BladeMask.full(alg)

# Product tensor Ô_{kij}
O = product_tensor(mask, mask)
mv_a = _as_mv(alg, "e1")
mv_b = _as_mv(alg, "e2")

A = to_tensor(mv_a, mask=mask)               # shape 8
B = to_tensor(mv_b, mask=mask)

# Label‑driven GP
result = O["kij"] * A["i"] * B["j"]          # labels "k*", shape 8
```

### Batch geometric product with element‑wise batch axis

```python
batch_size = 5
A_batch = MVLabeledTensor.zeros("i*n_", [mask, batch_size])
B_batch = MVLabeledTensor.zeros("j*n_", [mask, batch_size])

# Fill A_batch, B_batch data ...
result = O["kij"] * A_batch["in_"] * B_batch["jn_"]
# result.labels == "k*n_", shape (8, 5)
# Each batch element's GP is computed independently.
```

### Reorder after product

```python
C = (A_batch["in_"] * B_batch["jn_"])         # labels "i*j*n_"
D = C["->nij"]                                # labels "n_i*j*"